#!/usr/bin/env python3
"""
Test dell'endpoint prompt/preview con richiesta HTTP diretta
"""
import requests
import json

def test_prompt_preview():
    """Testa l'endpoint prompt/preview"""
    url = "http://127.0.0.1:5005/ai/prompt/preview"
    
    # Dati di test (dovrai sostituire file_id con un ID valido)
    test_data = {
        'file_id': 1,  # Assumendo che esista un file con ID 1
        'template_id': 1,
        'selected_categories': [],
        'batch_size': 3
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🧪 Testing POST {url}")
        print(f"📊 Data: {test_data}")
        
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"📬 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 401:
            print("ℹ️ Errore 401: Autenticazione richiesta (normale per questo test)")
        elif response.status_code == 400:
            print("❌ Errore 400: Errore nei parametri della richiesta")
        elif response.status_code == 200:
            print("✅ Success!")
        else:
            print(f"⚠️ Status code inaspettato: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione - assicurati che l'app sia in esecuzione")
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    test_prompt_preview()
