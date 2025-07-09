#!/usr/bin/env python3
"""
Script per testare gli endpoint di test connessione
"""

import requests
import json
from app import app
from models import db, AIConfiguration

def test_connection_endpoints():
    """Testa gli endpoint di test connessione per tutte le configurazioni"""
    
    with app.app_context():
        # Ottieni tutte le configurazioni AI
        configs = AIConfiguration.query.all()
        
        print(f"Trovate {len(configs)} configurazioni AI")
        print("-" * 50)
        
        for config in configs:
            print(f"\nTestando configurazione: {config.name} ({config.provider})")
            
            # Test della connessione tramite endpoint
            url = f"http://127.0.0.1:5004/admin/ai-config/{config.id}/test"
            
            try:
                response = requests.post(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    status = "✅ SUCCESSO" if data.get('success') else "❌ FALLITO"
                    print(f"  Status: {status}")
                    print(f"  Messaggio: {data.get('message', 'Nessun messaggio')}")
                else:
                    print(f"  ❌ Errore HTTP: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Errore richiesta: {str(e)}")
            except Exception as e:
                print(f"  ❌ Errore generale: {str(e)}")

def test_direct_clients():
    """Testa direttamente i client senza passare per l'endpoint"""
    from services.ollama_client import OllamaClient
    from services.openrouter_client import OpenRouterClient
    
    with app.app_context():
        configs = AIConfiguration.query.all()
        
        print("\n" + "="*50)
        print("TEST DIRETTO DEI CLIENT")
        print("="*50)
        
        for config in configs:
            print(f"\nTestando direttamente: {config.name} ({config.provider})")
            
            try:
                if config.provider == 'ollama':
                    client = OllamaClient(config.ollama_url)
                    result = client.test_connection()
                    
                    if result:
                        models = client.list_models()
                        model_available = any(m['name'] == config.ollama_model for m in models)
                        print(f"  ✅ Connessione riuscita")
                        print(f"  Modello {config.ollama_model}: {'✅ Disponibile' if model_available else '❌ Non trovato'}")
                        print(f"  Modelli disponibili: {len(models)}")
                    else:
                        print(f"  ❌ Connessione fallita")
                        
                elif config.provider == 'openrouter':
                    if not config.openrouter_api_key:
                        print(f"  ❌ Nessuna API key configurata")
                        continue
                        
                    client = OpenRouterClient(config.openrouter_api_key)
                    result = client.test_connection()
                    
                    if result:
                        print(f"  ✅ API key valida")
                    else:
                        print(f"  ❌ API key non valida")
                        
            except Exception as e:
                print(f"  ❌ Errore: {str(e)}")

if __name__ == "__main__":
    print("TESTING AI CONNECTION ENDPOINTS")
    print("="*50)
    
    # Prima testa gli endpoint HTTP
    test_connection_endpoints()
    
    # Poi testa direttamente i client
    test_direct_clients()
    
    print("\n" + "="*50)
    print("Test completato!")
