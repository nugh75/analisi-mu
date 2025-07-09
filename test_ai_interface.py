#!/usr/bin/env python3
"""
Script per testare l'interfaccia AI dopo le correzioni
"""

import os
import sys
import requests
from datetime import datetime

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, ExcelFile, TextCell, AIConfiguration

def test_ai_interface():
    """Testa l'interfaccia AI e le funzionalità correlate"""
    app = create_app()
    
    with app.app_context():
        print("=== Test Interfaccia AI ===\n")
        
        # 1. Verifica configurazione AI
        print("1. Verifica configurazione AI...")
        ai_config = AIConfiguration.query.first()
        if ai_config:
            print(f"   ✓ Configurazione trovata:")
            print(f"     - Provider: {ai_config.provider}")
            model_name = ai_config.ollama_model if ai_config.provider == 'ollama' else ai_config.openrouter_model
            print(f"     - Modello: {model_name}")
            print(f"     - Attiva: {'Sì' if ai_config.is_active else 'No'}")
        else:
            print("   ✗ Nessuna configurazione AI trovata")
            return False
        
        # 2. Verifica file Excel di test
        print("\n2. Verifica file Excel di test...")
        test_file = ExcelFile.query.first()
        if test_file:
            print(f"   ✓ File trovato: {test_file.filename}")
            print(f"     - ID: {test_file.id}")
            print(f"     - Celle totali: {len(test_file.text_cells)}")
        else:
            print("   ✗ Nessun file Excel trovato nel database")
            return False
        
        # 3. Test endpoint status AI
        print("\n3. Test endpoint status AI...")
        with app.test_client() as client:
            # Login come admin
            login_response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if login_response.status_code == 200:
                print("   ✓ Login effettuato con successo")
            else:
                print("   ✗ Errore nel login")
                return False
            
            # Test endpoint /ai/status/<file_id>
            status_response = client.get(f'/ai/status/{test_file.id}')
            if status_response.status_code == 200:
                status_data = status_response.get_json()
                print(f"   ✓ Endpoint status funzionante:")
                print(f"     - Provider: {status_data.get('provider', 'N/A')}")
                print(f"     - Modello: {status_data.get('model', 'N/A')}")
                print(f"     - Stato: {status_data.get('status', 'N/A')}")
                print(f"     - Celle annotate: {status_data.get('annotated_cells', 0)}")
                print(f"     - Celle totali: {status_data.get('total_cells', 0)}")
            else:
                print(f"   ✗ Errore endpoint status: {status_response.status_code}")
                return False
            
            # Test endpoint /ai/config/current
            config_response = client.get('/ai/config/current')
            if config_response.status_code == 200:
                config_data = config_response.get_json()
                print(f"\n   ✓ Endpoint config funzionante:")
                print(f"     - Provider: {config_data.get('provider', 'N/A')}")
                model_key = 'ollama_model' if config_data.get('provider') == 'ollama' else 'openrouter_model'
                print(f"     - Modello: {config_data.get(model_key, 'N/A')}")
            else:
                print(f"   ✗ Errore endpoint config: {config_response.status_code}")
        
        # 4. Verifica modelli OpenRouter
        print("\n4. Verifica modelli OpenRouter...")
        from models import OpenRouterModel
        free_models = OpenRouterModel.query.filter_by(is_free=True).count()
        total_models = OpenRouterModel.query.count()
        print(f"   ✓ Modelli OpenRouter nel database:")
        print(f"     - Modelli gratuiti: {free_models}")
        print(f"     - Modelli totali: {total_models}")
        
        # 5. Test connessione AI (se configurata)
        if ai_config and ai_config.is_active:
            print(f"\n5. Test connessione {ai_config.provider}...")
            
            if ai_config.provider == 'ollama':
                from services.ollama_client import OllamaClient
                client = OllamaClient(ai_config.ollama_url or 'http://localhost:11434')
                try:
                    models = client.list_models()
                    if models:
                        print(f"   ✓ Connessione Ollama OK - {len(models)} modelli disponibili")
                    else:
                        print("   ⚠️  Connessione OK ma nessun modello trovato")
                except Exception as e:
                    print(f"   ✗ Errore connessione Ollama: {str(e)}")
            
            elif ai_config.provider == 'openrouter':
                from services.openrouter_client import OpenRouterClient
                client = OpenRouterClient(ai_config.openrouter_api_key)
                try:
                    if client.test_connection():
                        print("   ✓ Connessione OpenRouter OK")
                    else:
                        print("   ✗ Test connessione OpenRouter fallito")
                except Exception as e:
                    print(f"   ✗ Errore connessione OpenRouter: {str(e)}")
        
        print("\n✅ Test completati!")
        return True

if __name__ == "__main__":
    success = test_ai_interface()
    
    if success:
        print("\n✨ Tutti i test sono passati con successo!")
        print("\nProssimi passi:")
        print("1. Avvia l'applicazione con: python app.py")
        print("2. Vai su http://localhost:5004")
        print("3. Effettua il login come admin (username: admin, password: admin123)")
        print("4. Apri un file Excel e verifica che:")
        print("   - I badge di stato AI abbiano lo stile corretto (sfondo grigio)")
        print("   - Il pulsante 'Genera Etichette AI' funzioni")
        print("   - La selezione dei modelli OpenRouter mostri i nuovi modelli gratuiti")
    else:
        print("\n⚠️  Alcuni test hanno fallito. Verifica i problemi segnalati.")
        sys.exit(1)