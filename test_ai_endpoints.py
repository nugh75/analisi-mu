#!/usr/bin/env python3
"""
Script per testare gli endpoint AI
"""

import os
import sys
import requests

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, ExcelFile

def test_ai_endpoints():
    """Testa gli endpoint AI"""
    app = create_app()
    
    with app.app_context():
        print("=== Test Endpoint AI ===\n")
        
        # URL base
        base_url = "http://localhost:5004"
        
        # 1. Test /ai/config/current senza autenticazione
        print("1. Test /ai/config/current (senza autenticazione)...")
        try:
            response = requests.get(f"{base_url}/ai/config/current")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                if data.get('success'):
                    print("   ✓ Endpoint funziona senza autenticazione")
                else:
                    print(f"   ⚠️  Risposta negativa: {data.get('message')}")
            else:
                print(f"   ✗ Errore: Status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ✗ Errore di connessione: {str(e)}")
        
        # 2. Test /ai/status/<file_id> senza autenticazione
        print("\n2. Test /ai/status/<file_id> (senza autenticazione)...")
        
        # Trova un file di test
        test_file = ExcelFile.query.first()
        if test_file:
            print(f"   Usando file ID: {test_file.id}")
            try:
                response = requests.get(f"{base_url}/ai/status/{test_file.id}")
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Response: {data}")
                    if data.get('success'):
                        print("   ✓ Endpoint funziona senza autenticazione")
                    else:
                        print(f"   ⚠️  Risposta negativa: {data.get('error')}")
                else:
                    print(f"   ✗ Errore: Status {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
            except Exception as e:
                print(f"   ✗ Errore di connessione: {str(e)}")
        else:
            print("   ⚠️  Nessun file trovato per il test")
        
        # 3. Test con autenticazione
        print("\n3. Test endpoint con autenticazione...")
        
        # Crea una sessione e fai login
        session = requests.Session()
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code in [302, 303]:  # Redirect dopo login
            print("   ✓ Login effettuato con successo")
            
            # Test /ai/config/current con autenticazione
            print("\n   Test /ai/config/current (con autenticazione)...")
            response = session.get(f"{base_url}/ai/config/current")
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
            
            # Test /ai/status/<file_id> con autenticazione
            if test_file:
                print(f"\n   Test /ai/status/{test_file.id} (con autenticazione)...")
                response = session.get(f"{base_url}/ai/status/{test_file.id}")
                print(f"   Status Code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Response: {data}")
        else:
            print("   ✗ Login fallito")
        
        print("\n✅ Test completati!")
        
        # Verifica configurazione AI nel database
        print("\n4. Verifica configurazione AI nel database...")
        ai_config = AIConfiguration.query.filter_by(is_active=True).first()
        if ai_config:
            print(f"   ✓ Configurazione attiva trovata:")
            print(f"     - Provider: {ai_config.provider}")
            print(f"     - Nome: {ai_config.name}")
            if ai_config.provider == 'ollama':
                print(f"     - Modello: {ai_config.ollama_model}")
                print(f"     - URL: {ai_config.ollama_url}")
            elif ai_config.provider == 'openrouter':
                print(f"     - Modello: {ai_config.openrouter_model}")
                print(f"     - API Key: {'***' + ai_config.openrouter_api_key[-4:] if ai_config.openrouter_api_key else 'Non impostata'}")
        else:
            print("   ✗ Nessuna configurazione AI attiva trovata")

if __name__ == "__main__":
    print("Assicurati che l'applicazione sia in esecuzione su http://localhost:5004\n")
    test_ai_endpoints()