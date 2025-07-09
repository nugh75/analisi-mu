#!/usr/bin/env python3
"""
Script per testare e configurare un modello Ollama più veloce
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration
from services.ollama_client import OllamaClient

def switch_to_faster_model():
    """Cambia a un modello Ollama più veloce"""
    
    app = create_app()
    
    with app.app_context():
        # Trova la configurazione Ollama attiva
        ollama_config = AIConfiguration.query.filter_by(provider='ollama', is_active=True).first()
        
        if not ollama_config:
            print("❌ Nessuna configurazione Ollama attiva!")
            return
        
        print(f"🔧 Configurazione attuale: {ollama_config.ollama_model}")
        
        # Testa la connessione
        try:
            client = OllamaClient(ollama_config.ollama_url)
            models = client.list_models()
            
            print(f"📋 Modelli disponibili ({len(models)}):")
            for model in models:
                model_name = model['name']
                size_gb = model.get('size', 0) / (1024**3) if model.get('size') else 0
                print(f"  • {model_name} ({size_gb:.1f} GB)")
            
            # Cerciamo un modello più piccolo
            faster_models = ['llama3.2:3b', 'llama3.2:1b', 'gemma2:2b', 'phi3:mini', 'qwen2.5:3b']
            available_faster = []
            
            for fast_model in faster_models:
                if any(fast_model in m['name'] for m in models):
                    available_faster.append(fast_model)
            
            if available_faster:
                new_model = available_faster[0]
                print(f"✅ Modello più veloce trovato: {new_model}")
                
                # Aggiorna la configurazione
                ollama_config.ollama_model = new_model
                
                # Riduci il timeout e aumenta i token per modelli piccoli
                ollama_config.max_tokens = 500
                ollama_config.temperature = 0.3  # Più deterministico
                
                try:
                    db.session.commit()
                    print(f"✅ Configurazione aggiornata!")
                    print(f"  Modello: {new_model}")
                    print(f"  Max tokens: {ollama_config.max_tokens}")
                    print(f"  Temperature: {ollama_config.temperature}")
                    
                    # Test rapido
                    print(f"\n🧪 Test rapido...")
                    test_response = client.generate(
                        model=new_model,
                        prompt="Rispondi con una sola parola: colore del cielo",
                        max_tokens=10,
                        temperature=0.1
                    )
                    
                    if test_response:
                        print(f"✅ Test OK: {test_response[:50]}...")
                    else:
                        print(f"❌ Test fallito")
                        
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Errore nell'aggiornamento: {str(e)}")
            else:
                print("❌ Nessun modello più veloce disponibile")
                print("💡 Suggestion: installa un modello più piccolo con:")
                print("   ollama pull llama3.2:3b")
                
        except Exception as e:
            print(f"❌ Errore connessione Ollama: {str(e)}")

if __name__ == "__main__":
    switch_to_faster_model()
