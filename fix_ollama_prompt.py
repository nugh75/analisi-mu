#!/usr/bin/env python3
"""
Script per copiare il prompt di sistema dalla configurazione OpenRouter a Ollama
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration

def fix_ollama_prompt():
    """Copia il prompt dalla configurazione OpenRouter a Ollama"""
    
    app = create_app()
    
    with app.app_context():
        # Trova le configurazioni
        ollama_config = AIConfiguration.query.filter_by(provider='ollama').first()
        openrouter_config = AIConfiguration.query.filter_by(provider='openrouter').first()
        
        if not ollama_config:
            print("❌ Configurazione Ollama non trovata!")
            return
            
        if not openrouter_config:
            print("❌ Configurazione OpenRouter non trovata!")
            return
        
        # Copia il prompt
        if openrouter_config.system_prompt:
            ollama_config.system_prompt = openrouter_config.system_prompt
            print(f"✅ Prompt copiato da {openrouter_config.name} a {ollama_config.name}")
            print(f"📝 Lunghezza prompt: {len(ollama_config.system_prompt)} caratteri")
        else:
            print("⚠️  La configurazione OpenRouter non ha un prompt di sistema!")
            return
        
        # Assicurati che Ollama sia attiva
        if not ollama_config.is_active:
            # Disattiva tutte le altre
            AIConfiguration.query.update({'is_active': False})
            # Attiva Ollama
            ollama_config.is_active = True
            print("✅ Configurazione Ollama attivata")
        
        try:
            db.session.commit()
            print("💾 Modifiche salvate nel database")
            
            # Mostra anteprima
            preview = ollama_config.system_prompt[:200] + "..." if len(ollama_config.system_prompt) > 200 else ollama_config.system_prompt
            print(f"\n📋 ANTEPRIMA PROMPT OLLAMA:")
            print("-" * 50)
            print(preview)
            print("-" * 50)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore nel salvataggio: {str(e)}")

if __name__ == "__main__":
    fix_ollama_prompt()
