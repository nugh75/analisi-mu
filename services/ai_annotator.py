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
        """Costruisce il prompt per l'annotazione"""
        
        prompt = f"""ISTRUZIONI SPECIFICHE PER QUESTA RICHIESTA:
1. Analizza ogni testo fornito
2. Assegna UNA o più etichette appropriate per ogni testo dalla lista disponibile nel tuo prompt di sistema
3. Usa il tuo giudizio esperto per identificare temi, sentimenti e contenuti
4. Rispondi SOLO in formato JSON valido con questa struttura:
[
  {{"index": 0, "label": "nome_etichetta", "confidence": 0.95}},
  {{"index": 1, "label": "nome_etichetta", "confidence": 0.87}}
]

TESTI DA ETICHETTARE:
"""
        
        for i, text in enumerate(texts):
            # Pulisce il testo e lo tronca se troppo lungo
            clean_text = re.sub(r'\s+', ' ', text.strip())[:800]
            prompt += f"{i}: {clean_text}\n"
        
        prompt += "\nRispondi solo con il JSON (array di oggetti):"
        
        return prompt
    
    def generate_annotations(self, file_id: int, batch_size: int = 20) -> Dict:
        """Genera annotazioni AI per un file"""
        try:
            # Ottiene la configurazione attiva
            config = self.get_active_configuration()
            if not config:
                return {"error": "Nessuna configurazione AI attiva"}
            
            self.initialize_clients(config)
            
            # Ottiene i testi non ancora annotati
            unannotated_cells = TextCell.query.filter(
                TextCell.excel_file_id == file_id,
                ~TextCell.id.in_(
                    db.session.query(CellAnnotation.text_cell_id).distinct()
                )
            ).limit(batch_size * 5).all()  # Prende più testi per gestire i batch
            
            if not unannotated_cells:
                return {"message": "Nessun testo da annotare", "annotations": []}
            
            # Ottiene le etichette disponibili
            labels = Label.query.all()
            if not labels:
                return {"error": "Nessuna etichetta disponibile"}
            
            # Processa in batch
            all_annotations = []
            total_processed = 0
            
            for i in range(0, len(unannotated_cells), batch_size):
                batch_cells = unannotated_cells[i:i + batch_size]
                batch_texts = [cell.text_content for cell in batch_cells]
                
                # Genera le annotazioni per questo batch
                batch_annotations = self._process_batch(
                    batch_texts, batch_cells, labels, config
                )
                
                all_annotations.extend(batch_annotations)
                total_processed += len(batch_cells)
                
                # Break se abbiamo processato abbastanza
                if total_processed >= 100:  # Limite per evitare timeout
                    break
            
            return {
                "message": f"Generate {len(all_annotations)} annotazioni",
                "annotations": all_annotations,
                "total_processed": total_processed
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _process_batch(self, texts: List[str], cells: List[TextCell], 
                      labels: List[Label], config: AIConfiguration) -> List[Dict]:
        """Processa un batch di testi"""
        annotations = []
        
        try:
            # Costruisce il prompt
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
                    label_name = ai_ann['label'].lower()
                    
                    # Trova l'etichetta corrispondente
                    label = label_map.get(label_name)
                    if not label:
                        # Cerca match parziale
                        for name, lbl in label_map.items():
                            if label_name in name or name in label_name:
                                label = lbl
                                break
                    
                    if label:
                        annotation = CellAnnotation(
                            text_cell_id=cell.id,
                            label_id=label.id,
                            user_id=ai_user.id,
                            is_ai_generated=True,
                            ai_confidence=ai_ann.get('confidence', 0.5),
                            ai_model=config.ollama_model or config.openrouter_model,
                            ai_provider=config.provider,
                            status='pending_review'
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
