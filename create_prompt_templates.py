#!/usr/bin/env python3
"""
Script per creare il sistema di template per i prompt AI
"""

from app import create_app
from models import db

# Aggiungiamo il nuovo modello AIPromptTemplate
class AIPromptTemplate(db.Model):
    __tablename__ = 'ai_prompt_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    base_prompt = db.Column(db.Text, nullable=False)  # Parte generica del prompt
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<AIPromptTemplate {self.name}>'

def create_prompt_templates():
    """Crea i template di prompt predefiniti"""
    app = create_app()
    
    with app.app_context():
        print("=== CREAZIONE TEMPLATE PROMPT AI ===\n")
        
        # Template predefiniti
        templates = [
            {
                'name': 'Analisi Sentiment Educativo',
                'description': 'Template per analizzare il sentiment in contesti educativi',
                'base_prompt': '''Sei un esperto nell'analisi del sentiment in contesti educativi e ricerca.

Analizza i seguenti testi e assegna a ciascuno una o più etichette appropriate dalle categorie selezionate.

ISTRUZIONI:
1. Leggi attentamente ogni testo
2. Identifica il sentiment, la prospettiva e i temi principali
3. Assegna solo etichette pertinenti e accurate
4. Usa la confidence per indicare la sicurezza della tua valutazione
5. Se un testo non è classificabile, lascia l'etichetta vuota

FORMATO RISPOSTA (JSON):
[
  {"index": 0, "label": "Nome_Etichetta", "confidence": 0.95},
  {"index": 1, "label": "Altra_Etichetta", "confidence": 0.80}
]'''
            },
            {
                'name': 'Classificazione Tematica',
                'description': 'Template per classificazione tematica generale',
                'base_prompt': '''Sei un esperto nella classificazione tematica di testi.

Analizza i seguenti testi e classifica ciascuno secondo le categorie tematiche fornite.

ISTRUZIONI:
1. Identifica il tema principale di ogni testo
2. Assegna l'etichetta più appropriata dalle categorie disponibili
3. Mantieni coerenza nella classificazione
4. Usa confidence alta (>0.8) solo per classificazioni molto sicure

FORMATO RISPOSTA (JSON):
[
  {"index": 0, "label": "Categoria_Principale", "confidence": 0.90},
  {"index": 1, "label": "", "confidence": 1.0}
]'''
            },
            {
                'name': 'Analisi Multi-dimensionale',
                'description': 'Template per analisi complessa con multiple dimensioni',
                'base_prompt': '''Sei un esperto nell'analisi multidimensionale di testi.

Analizza i seguenti testi considerando tutte le dimensioni presenti nelle categorie selezionate (sentiment, prospettiva, utilizzo, benefici, rischi, ecc.).

ISTRUZIONI:
1. Esamina ogni testo da multiple prospettive
2. Identifica tutti gli aspetti rilevanti presenti nel testo
3. Assegna multiple etichette se il testo tocca più dimensioni
4. Mantieni alta precisione nella classificazione

NOTA: Puoi assegnare multiple etichette allo stesso testo se pertinenti.

FORMATO RISPOSTA (JSON):
[
  {"index": 0, "label": "Prima_Etichetta", "confidence": 0.85},
  {"index": 0, "label": "Seconda_Etichetta", "confidence": 0.75},
  {"index": 1, "label": "Altra_Etichetta", "confidence": 0.90}
]'''
            }
        ]
        
        created_count = 0
        for template_data in templates:
            # Verifica se esiste già
            existing = AIPromptTemplate.query.filter_by(name=template_data['name']).first()
            if not existing:
                template = AIPromptTemplate(**template_data)
                db.session.add(template)
                created_count += 1
                print(f"✅ Creato template: {template_data['name']}")
            else:
                print(f"⚠️  Template già esistente: {template_data['name']}")
        
        try:
            db.session.commit()
            print(f"\n🎉 Creati {created_count} nuovi template!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore: {e}")

if __name__ == '__main__':
    create_prompt_templates()
