#!/usr/bin/env python3
"""
Script per aggiornare il prompt di sistema AI con le categorie di etichette
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, Label

def create_smart_prompt():
    """Crea un prompt intelligente basato sulle categorie di etichette disponibili"""
    
    app = create_app()
    
    with app.app_context():
        # Ottiene tutte le etichette raggruppate per categoria
        labels = Label.query.order_by(Label.category, Label.name).all()
        
        if not labels:
            print("❌ Nessuna etichetta trovata nel database!")
            return
        
        # Raggruppa per categoria (gestisce anche None)
        categories = {}
        for label in labels:
            category = label.category if label.category else "GENERALE"
            if category not in categories:
                categories[category] = []
            categories[category].append(label)
        
        # Costruisce il prompt dinamico
        prompt = """Sei un assistente AI specializzato nell'etichettatura di testi educativi riguardanti l'uso dell'Intelligenza Artificiale nell'istruzione.

Il tuo compito è analizzare risposte testuali a questionari sull'IA nell'educazione e assegnare etichette appropriate basate sulle seguenti categorie:

CATEGORIE E ETICHETTE DISPONIBILI:
"""
        
        for category, category_labels in categories.items():
            prompt += f"\n📂 {category}:\n"
            for label in category_labels:
                prompt += f"   • {label.name}"
                if label.description:
                    prompt += f" - {label.description}"
                prompt += "\n"
        
        prompt += """
ISTRUZIONI SPECIFICHE:
1. Leggi attentamente ogni testo fornito
2. Identifica il tema principale e il sentiment espresso
3. Assegna SOLO UNA etichetta per testo, quella più appropriata
4. Se un testo è ambiguo o copre più temi, scegli l'etichetta più dominante
5. Se un testo non corrisponde a nessuna etichetta, NON etichettarlo
6. Rispondi SEMPRE in formato JSON valido
7. Includi un livello di confidenza (0.0-1.0) per ogni assegnazione

FORMATO RISPOSTA:
[
    {"index": 0, "label": "nome_etichetta_esatto", "confidence": 0.95},
    {"index": 1, "label": "nome_etichetta_esatto", "confidence": 0.87}
]

ESEMPI:
- "L'AI mi aiuta a studiare meglio" → Benefici/Efficienza
- "Ho paura che l'AI sostituisca i professori" → Rischi e Preoccupazioni/Perdita Competenze  
- "Uso ChatGPT per i compiti" → Utilizzo AI/Scrittura
- "È importante usare l'AI in modo etico" → Aspetti Etici/Responsabilità

Analizza sempre dal punto di vista del contesto educativo e dell'impatto dell'IA sull'apprendimento."""

        # Aggiorna la configurazione AI attiva
        config = AIConfiguration.query.filter_by(is_active=True).first()
        
        if not config:
            print("❌ Nessuna configurazione AI attiva trovata!")
            return
        
        config.system_prompt = prompt
        
        try:
            db.session.commit()
            print("✅ Prompt di sistema aggiornato con successo!")
            print(f"📊 Incluse {len(labels)} etichette in {len(categories)} categorie")
            print(f"🔧 Configurazione: {config.name} ({config.provider})")
            
            # Mostra un'anteprima del prompt
            print("\n📝 ANTEPRIMA PROMPT:")
            print("-" * 60)
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print("-" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore nell'aggiornamento: {str(e)}")

if __name__ == "__main__":
    create_smart_prompt()
