#!/usr/bin/env python3
"""
Script per testare direttamente i client AI senza autenticazione
"""

from app import create_app
from models import db, AIConfiguration
from services.ollama_client import OllamaClient
from services.openrouter_client import OpenRouterClient

def test_ai_connections():
    """Testa direttamente le connessioni AI"""
    
    app = create_app()
    with app.app_context():
        configs = AIConfiguration.query.all()
        
        print(f"TESTING AI CONNECTIONS")
        print("="*50)
        print(f"Trovate {len(configs)} configurazioni AI\n")
        
        for config in configs:
            print(f"Configurazione: {config.name}")
            print(f"Provider: {config.provider}")
            print(f"Attiva: {'✅ Sì' if config.is_active else '❌ No'}")
            
            try:
                if config.provider == 'ollama':
                    print(f"URL Ollama: {config.ollama_url}")
                    print(f"Modello: {config.ollama_model}")
                    
                    client = OllamaClient(config.ollama_url)
                    print("Testando connessione...", end=" ")
                    
                    is_connected = client.test_connection()
                    
                    if is_connected:
                        print("✅ SUCCESSO")
                        
                        # Testa se il modello è disponibile
                        print("Recuperando lista modelli...", end=" ")
                        try:
                            models = client.list_models()
                            print(f"✅ {len(models)} modelli trovati")
                            
                            model_available = any(m['name'] == config.ollama_model for m in models)
                            print(f"Modello '{config.ollama_model}': {'✅ Disponibile' if model_available else '❌ Non trovato'}")
                            
                            if not model_available:
                                print(f"Modelli disponibili: {[m['name'] for m in models[:5]]}")  # Mostra primi 5
                                
                        except Exception as e:
                            print(f"❌ Errore nel recupero modelli: {str(e)}")
                    else:
                        print("❌ FALLITA")
                        
                elif config.provider == 'openrouter':
                    print(f"Modello: {config.openrouter_model}")
                    print(f"API Key: {'✅ Configurata' if config.openrouter_api_key else '❌ Mancante'}")
                    
                    if not config.openrouter_api_key:
                        print("❌ Impossibile testare senza API key")
                    else:
                        client = OpenRouterClient(config.openrouter_api_key)
                        print("Testando connessione...", end=" ")
                        
                        is_connected = client.test_connection()
                        
                        if is_connected:
                            print("✅ SUCCESSO - API key valida")
                        else:
                            print("❌ FALLITA - API key non valida")
                            
            except Exception as e:
                print(f"❌ ERRORE: {str(e)}")
                
            print("-" * 50)

def test_specific_connections():
    """Testa connessioni specifiche con URL predefiniti"""
    
    print(f"\nTEST CONNESSIONI SPECIFICHE")
    print("="*50)
    
    # Test Ollama con URL predefinito
    print("Test Ollama (http://192.168.129.14:11435)")
    try:
        client = OllamaClient("http://192.168.129.14:11435")
        is_connected = client.test_connection()
        print(f"Connessione: {'✅ SUCCESSO' if is_connected else '❌ FALLITA'}")
        
        if is_connected:
            models = client.list_models()
            print(f"Modelli disponibili: {len(models)}")
            for model in models[:3]:  # Mostra primi 3
                print(f"  - {model['name']}")
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
    
    print("-" * 30)
    
    # Test OpenRouter con chiave di test (se disponibile)
    app = create_app()
    with app.app_context():
        openrouter_config = AIConfiguration.query.filter_by(provider='openrouter').first()
        if openrouter_config and openrouter_config.openrouter_api_key:
            print("Test OpenRouter")
            try:
                client = OpenRouterClient(openrouter_config.openrouter_api_key)
                is_connected = client.test_connection()
                print(f"Connessione: {'✅ SUCCESSO' if is_connected else '❌ FALLITA'}")
            except Exception as e:
                print(f"❌ Errore: {str(e)}")
        else:
            print("❌ Nessuna configurazione OpenRouter con API key trovata")

if __name__ == "__main__":
    test_ai_connections()
    test_specific_connections()
    print("\nTest completato!")
