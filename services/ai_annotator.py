"""
Servizio per l'annotazione automatica tramite AI
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from models import (
    db, User, Label, TextCell, CellAnnotation, 
    AIConfiguration, OpenRouterModel, OllamaModel
)
from services.ollama_client import OllamaClient
from services.openrouter_client import OpenRouterClient


class AIAnnotatorService:
    def __init__(self):
        self.ollama_client = None
        self.openrouter_client = None
        self.ai_user = None
        
    def get_or_create_ai_user(self) -> User:
        """Ottiene o crea l'utente AI"""
        if not self.ai_user:
            self.ai_user = User.query.filter_by(username='ai_assistant').first()
            if not self.ai_user:
                self.ai_user = User(
                    username='ai_assistant',
                    email='ai@system.local',
                    role='annotatore'
                )
                self.ai_user.set_password('N/A')
                db.session.add(self.ai_user)
                db.session.commit()
        return self.ai_user
    
    def get_active_configuration(self) -> Optional[AIConfiguration]:
        """Ottiene la configurazione AI attiva"""
        return AIConfiguration.query.filter_by(is_active=True).first()
    
    def initialize_clients(self, config: AIConfiguration = None):
        """Inizializza i client AI"""
        if not config:
            config = self.get_active_configuration()
        
        if not config:
            raise ValueError("Nessuna configurazione AI attiva trovata")
        
        if config.provider == 'ollama':
            self.ollama_client = OllamaClient(config.ollama_url)
        elif config.provider == 'openrouter':
            self.openrouter_client = OpenRouterClient(config.openrouter_api_key)
    
    def build_annotation_prompt(self, texts: List[str], labels: List[Label]) -> str:
        """
        Costruisce il prompt per l'annotazione AI usando le etichette correnti del sistema
        
        Args:
            texts: Lista dei testi da annotare
            labels: Lista delle etichette correnti del sistema (sempre aggiornate)
        """
        # Organizza le etichette per categoria per un prompt più strutturato
        from collections import defaultdict
        categories_dict = defaultdict(list)
        
        for label in labels:
            if label.is_active:  # Solo etichette attive
                category_name = label.category_obj.name if label.category_obj else 'Generale'
                categories_dict[category_name].append(label)
        
        # Costruisce la lista delle categorie ed etichette
        categories_text = "ETICHETTE DISPONIBILI (sempre aggiornate dal sistema):\n"
        for category, cat_labels in categories_dict.items():
            categories_text += f"\n=== {category} ===\n"
            for label in cat_labels:
                desc = f" - {label.description}" if label.description else ""
                categories_text += f"• {label.name}{desc}\n"
        
        prompt = f"""Sei un assistente esperto nell'etichettatura di testi educativi e questionari.

{categories_text}

ISTRUZIONI:
1. Analizza ogni testo fornito
2. Assegna SOLO etichette dalla lista sopra (nomi ESATTI)
3. Puoi assegnare multiple etichette se appropriato
4. Se un testo non è rilevante o non ha etichette appropriate, usa etichetta vuota: ""
5. Rispondi SOLO in formato JSON valido con questa struttura:
[
  {{"index": 0, "label": "NomeEsattoDallaLista", "confidence": 0.95}},
  {{"index": 1, "label": "AltroNomeEsatto", "confidence": 0.87}},
  {{"index": 2, "label": "", "confidence": 1.0}}
]

TESTI DA ETICHETTARE:
"""
        
        for i, text in enumerate(texts):
            # Pulisce il testo e lo tronca se troppo lungo
            clean_text = re.sub(r'\s+', ' ', text.strip())[:800]
            prompt += f"{i}: {clean_text}\n"
        
        prompt += f"\nRispondi solo con il JSON. Usa SOLO i nomi delle etichette dalla lista sopra (case-sensitive):"
        
        return prompt
    
    def generate_annotations(self, file_id: int, batch_size: int = 10, mode: str = 'new', 
                           template_id: int = None, selected_categories: List[str] = None) -> Dict:
        """
        Genera annotazioni AI per un file
        
        Args:
            file_id: ID del file Excel
            batch_size: Numero di testi per batch (ridotto per evitare timeout)
            mode: Modalità di etichettatura ('new', 'additional', 'replace')
            template_id: ID del template prompt da usare
            selected_categories: Lista delle categorie selezionate per il prompt
        """
        try:
            # Ottiene la configurazione attiva
            config = self.get_active_configuration()
            if not config:
                return {"error": "Nessuna configurazione AI attiva"}

            self.initialize_clients(config)

            # Ottiene le etichette disponibili
            if selected_categories:
                # Filtra per categorie selezionate
                from models import Category
                categories = Category.query.filter(Category.name.in_(selected_categories)).all()
                labels = []
                for cat in categories:
                    labels.extend(Label.query.filter_by(category_id=cat.id, is_active=True).all())
            else:
                labels = Label.query.filter_by(is_active=True).order_by(Label.category, Label.name).all()
            
            if not labels:
                return {"error": "Nessuna etichetta attiva disponibile"}

            # Ottiene i testi da annotare in base alla modalità
            if mode == 'replace':
                # Ri-etichettatura: tutte le celle
                target_cells = TextCell.query.filter_by(excel_file_id=file_id).all()
                print(f"🔄 Modalità sostituzione: {len(target_cells)} celle totali")
            elif mode == 'additional':
                # Etichettatura aggiuntiva: tutte le celle (anche quelle già annotate)
                target_cells = TextCell.query.filter_by(excel_file_id=file_id).all()
                print(f"➕ Modalità aggiuntiva: {len(target_cells)} celle totali")
            else:  # mode == 'new'
                # Modalità normale: solo celle non annotate
                target_cells = TextCell.query.filter(
                    TextCell.excel_file_id == file_id,
                    ~TextCell.id.in_(
                        db.session.query(CellAnnotation.text_cell_id).distinct()
                    )
                ).all()
                print(f"🆕 Modalità nuove: {len(target_cells)} celle non annotate")

            if not target_cells:
                message = f"Nessuna cella da elaborare per modalità '{mode}'"
                return {"message": message, "annotations": []}

            # Processa in batch più piccoli per evitare timeout
            all_annotations = []
            total_processed = 0
            max_cells_per_session = 20  # Ridotto per performance migliori

            # Limita il numero di celle da processare
            cells_to_process = target_cells[:max_cells_per_session]

            for i in range(0, len(cells_to_process), batch_size):
                batch_cells = cells_to_process[i:i + batch_size]
                batch_texts = [cell.text_content for cell in batch_cells]

                print(f"📝 Processando batch {i//batch_size + 1}: {len(batch_cells)} celle")

                # Genera le annotazioni per questo batch
                batch_annotations = self._process_batch(
                    batch_texts, batch_cells, labels, config, mode, template_id
                )

                all_annotations.extend(batch_annotations)
                total_processed += len(batch_cells)

                # Pausa tra i batch per evitare overload
                import time
                time.sleep(1)

            return {
                "message": f"Generate {len(all_annotations)} annotazioni (modalità: {mode})",
                "annotations": all_annotations,
                "total_processed": total_processed,
                "mode": mode
            }

        except Exception as e:
            print(f"❌ Errore in generate_annotations: {e}")
            return {"error": str(e)}
    
    def _process_batch(self, texts: List[str], cells: List[TextCell], 
                      labels: List[Label], config: AIConfiguration, mode: str = 'new', 
                      template_id: int = None) -> List[Dict]:
        """
        Processa un batch di testi
        
        Args:
            texts: Lista dei testi da annotare
            cells: Lista delle celle corrispondenti
            labels: Lista delle etichette disponibili (filtrate per categorie)
            config: Configurazione AI
            mode: Modalità di etichettatura ('new', 'additional', 'replace')
            template_id: ID del template prompt da usare
        """
        annotations = []
        
        try:
            # Costruisce il prompt con le etichette aggiornate
            prompt = self.build_annotation_prompt(texts, labels)
            
            # Prepara i messaggi
            messages = [
                {"role": "system", "content": config.system_prompt or "Sei un assistente per l'etichettatura di testi."},
                {"role": "user", "content": prompt}
            ]
            
            # Chiama l'AI
            response = None
            if config.provider == 'ollama':
                response = self.ollama_client.generate_chat(
                    config.ollama_model,
                    messages,
                    config.temperature,
                    config.max_tokens
                )
            elif config.provider == 'openrouter':
                response = self.openrouter_client.generate_chat(
                    config.openrouter_model,
                    messages,
                    config.temperature,
                    config.max_tokens
                )
            
            if not response or 'error' in response:
                print(f"Errore nella risposta AI: {response}")
                return annotations
            
            # Estrae il contenuto della risposta
            content = ""
            if config.provider == 'ollama':
                content = response.get('message', {}).get('content', '')
            elif config.provider == 'openrouter':
                content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Parsifica le annotazioni
            ai_annotations = self._parse_ai_response(content)
            
            # Crea le annotazioni nel database
            ai_user = self.get_or_create_ai_user()
            label_map = {label.name.lower(): label for label in labels}
            
            for ai_ann in ai_annotations:
                if ai_ann['index'] < len(cells):
                    cell = cells[ai_ann['index']]
                    
                    # Gestisce il caso in cui label può essere stringa o lista
                    label_raw = ai_ann.get('label', '')
                    if isinstance(label_raw, list):
                        # Se è una lista, prende il primo elemento
                        label_name = label_raw[0] if label_raw else ''
                    else:
                        label_name = str(label_raw)
                    
                    # Converte a lowercase per il match
                    label_name = label_name.lower() if label_name else ''
                    
                    # Salta se l'etichetta è vuota
                    if not label_name or label_name.strip() == "":
                        continue
                    
                    # Trova l'etichetta corrispondente (match esatto prima)
                    label = label_map.get(label_name)
                    if not label:
                        # Cerca match parziale solo se non trova match esatto
                        label_name_clean = label_name.strip()
                        for name, lbl in label_map.items():
                            if label_name_clean == name.lower() or label_name_clean in name.lower() or name.lower() in label_name_clean:
                                label = lbl
                                break
                    
                    if label:
                        # Se è modalità ri-etichettatura, rimuovi le annotazioni esistenti dell'utente AI
                        if re_annotate:
                            existing_ai_annotations = CellAnnotation.query.filter_by(
                                text_cell_id=cell.id,
                                user_id=ai_user.id,
                                is_ai_generated=True
                            ).all()
                            for existing_ann in existing_ai_annotations:
                                db.session.delete(existing_ann)
                        
                        # Crea la nuova annotazione con status pending_review
                        annotation = CellAnnotation(
                            text_cell_id=cell.id,
                            label_id=label.id,
                            user_id=ai_user.id,
                            is_ai_generated=True,
                            ai_confidence=ai_ann.get('confidence', 0.5),
                            ai_model=config.ollama_model or config.openrouter_model,
                            ai_provider=config.provider,
                            status='pending_review'  # SEMPRE pending_review
                        )
                        
                        db.session.add(annotation)
                        annotations.append({
                            'text': cell.text_content[:100] + '...',
                            'label': label.name,
                            'confidence': ai_ann.get('confidence', 0.5)
                        })
            
            db.session.commit()
            
        except Exception as e:
            print(f"Errore nel processamento batch: {e}")
            db.session.rollback()
        
        return annotations
    
    def _parse_ai_response(self, content: str) -> List[Dict]:
        """Parsifica la risposta JSON dell'AI"""
        try:
            # Estrae il JSON dalla risposta (potrebbe esserci testo aggiuntivo)
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Prova a parsificare l'intera risposta come JSON
                return json.loads(content.strip())
        except json.JSONDecodeError:
            print(f"Errore nel parsing JSON: {content}")
            return []
    
    def review_annotation(self, annotation_id: int, action: str, reviewer_id: int) -> bool:
        """Rivede un'annotazione AI (accetta/rifiuta)"""
        try:
            annotation = CellAnnotation.query.get(annotation_id)
            if not annotation or not annotation.is_ai_generated:
                return False
            
            if action == 'accept':
                annotation.status = 'active'
            elif action == 'reject':
                annotation.status = 'rejected'
            else:
                return False
            
            annotation.reviewed_by = reviewer_id
            annotation.reviewed_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Errore nella revisione: {e}")
            db.session.rollback()
            return False
    
    def get_pending_annotations(self, file_id: int = None) -> List[Dict]:
        """Ottiene le annotazioni in attesa di revisione"""
        query = CellAnnotation.query.filter(
            CellAnnotation.is_ai_generated == True,
            CellAnnotation.status == 'pending_review'
        )
        
        if file_id:
            query = query.join(TextCell).filter(TextCell.excel_file_id == file_id)
        
        annotations = query.all()
        
        result = []
        for ann in annotations:
            result.append({
                'id': ann.id,
                'text': ann.text_cell.text_content,
                'label': ann.label.name,
                'confidence': ann.ai_confidence,
                'model': ann.ai_model,
                'provider': ann.ai_provider,
                'created_at': ann.created_at.isoformat()
            })
        
        return result
