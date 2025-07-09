#!/usr/bin/env python3
"""
Script per attivare Ollama invece di OpenRouter
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration

def switch_to_ollama():
    """Attiva la configurazione Ollama e disattiva OpenRouter"""
    
    app = create_app()
    
    with app.app_context():
        # Disattiva tutte le configurazioni
        AIConfiguration.query.update({'is_active': False})
        
        # Attiva la configurazione Ollama
        ollama_config = AIConfiguration.query.filter_by(provider='ollama').first()
        
        if ollama_config:
            ollama_config.is_active = True
            
            try:
                db.session.commit()
                print("✅ Configurazione Ollama attivata!")
                print(f"🔧 Provider: {ollama_config.provider}")
                print(f"🤖 Modello: {ollama_config.ollama_model}")
                print(f"🌐 URL: {ollama_config.ollama_url}")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Errore nell'attivazione: {str(e)}")
        else:
            print("❌ Configurazione Ollama non trovata!")

if __name__ == "__main__":
    switch_to_ollama()
