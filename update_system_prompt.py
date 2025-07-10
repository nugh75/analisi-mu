#!/usr/bin/env python3
"""
Script per aggiornare il system prompt dell'AI con le categorie e etichette
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, Label, Category


def build_system_prompt():
    """Costruisce un system prompt completo con categorie e etichette"""
    
    # Raggruppa le etichette per categoria
    from collections import defaultdict
    categories_dict = defaultdict(list)
    
    labels = Label.query.filter_by(is_active=True).all()
    
    for label in labels:
        category_name = label.category_obj.name if label.category_obj else 'Generale'
        categories_dict[category_name].append(label)
    
    # Costruisce la lista delle categorie ed etichette
    categories_text = "ETICHETTE DISPONIBILI (organizzate per categoria):\n"
    for category, cat_labels in sorted(categories_dict.items()):
        categories_text += f"\n=== {category} ===\n"
        for label in sorted(cat_labels, key=lambda x: x.name):
            desc = f" - {label.description}" if label.description else ""
            categories_text += f"• {label.name}{desc}\n"
    
    system_prompt = f"""Sei un assistente esperto nell'etichettatura di testi educativi, questionari e ricerche accademiche.

{categories_text}

COMPITI PRINCIPALI:
1. Analizzare testi di risposte a questionari educativi
2. Identificare temi, sentiment e contenuti specifici
3. Assegnare etichette appropriate dalla lista disponibile
4. Fornire punteggi di confidenza accurati

REGOLE DI ETICHETTATURA:
• Usa SOLO etichette dalla lista sopra
• Usa il nome ESATTO dell'etichetta come appare nella lista
• Per testi vuoti o poco chiari, usa una stringa vuota ""
• Assegna un punteggio di confidenza da 0.0 a 1.0
• Preferisci etichette specifiche a quelle generiche
• Considera sia il contenuto esplicito che implicito

FORMATO DI RISPOSTA:
Rispondi sempre con un array JSON valido, senza testo aggiuntivo:
[
  {{"index": 0, "label": "nome_etichetta_esatto", "confidence": 0.95}},
  {{"index": 1, "label": "nome_etichetta_esatto", "confidence": 0.87}}
]

IMPORTANTE: Non aggiungere testo prima o dopo il JSON. Rispondi solo con l'array JSON."""
    
    return system_prompt


def update_system_prompt():
    """Aggiorna il system prompt della configurazione AI attiva"""
    
    print("🔄 Aggiornamento system prompt AI...")
    
    # Trova la configurazione attiva
    config = AIConfiguration.query.filter_by(is_active=True).first()
    if not config:
        print("❌ Nessuna configurazione AI attiva trovata")
        return False
    
    # Costruisce il nuovo prompt
    new_prompt = build_system_prompt()
    
    # Aggiorna la configurazione
    config.system_prompt = new_prompt
    db.session.commit()
    
    print(f"✅ System prompt aggiornato per: {config.name}")
    print(f"📝 Lunghezza prompt: {len(new_prompt)} caratteri")
    print(f"🏷️  Configurazione provider: {config.provider}")
    
    # Mostra un'anteprima
    preview = new_prompt[:300] + "..." if len(new_prompt) > 300 else new_prompt
    print(f"\n📋 Anteprima prompt:\n{preview}")
    
    return True


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success = update_system_prompt()
        if success:
            print("\n🎉 System prompt aggiornato con successo!")
        else:
            print("\n❌ Errore nell'aggiornamento del system prompt")
            sys.exit(1)
