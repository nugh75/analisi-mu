#!/usr/bin/env python3
"""
Script per cambiare al modello llama3 più veloce
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration
from services.ollama_client import OllamaClient

def switch_to_llama3():
    """Cambia al modello llama3 più veloce"""
    
    app = create_app()
    
    with app.app_context():
        # Trova la configurazione Ollama attiva
        ollama_config = AIConfiguration.query.filter_by(provider='ollama', is_active=True).first()
        
        if not ollama_config:
            print("❌ Nessuna configurazione Ollama attiva!")
            return
        
        print(f"🔧 Modello attuale: {ollama_config.ollama_model}")
        
        # Aggiorna a llama3
        ollama_config.ollama_model = "llama3:latest"
        ollama_config.max_tokens = 300  # Ridotto per velocità
        ollama_config.temperature = 0.2  # Più deterministico
        
        try:
            db.session.commit()
            print(f"✅ Configurazione aggiornata!")
            print(f"  Modello: llama3:latest (4.3 GB)")
            print(f"  Max tokens: {ollama_config.max_tokens}")
            print(f"  Temperature: {ollama_config.temperature}")
            
            # Test rapido
            client = OllamaClient(ollama_config.ollama_url)
            print(f"\n🧪 Test rapido...")
            
            test_response = client.generate(
                model="llama3:latest",
                prompt="Analizza questo testo e rispondi con una sola etichetta: 'L'AI mi aiuta a studiare meglio'",
                max_tokens=20,
                temperature=0.1
            )
            
            if test_response:
                print(f"✅ Test OK: {test_response}")
            else:
                print(f"❌ Test fallito")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore: {str(e)}")

if __name__ == "__main__":
    switch_to_llama3()
