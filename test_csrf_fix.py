#!/usr/bin/env python3
"""
Test dell'endpoint prompt/preview con CSRF token
"""
import requests
import json
import re

def get_csrf_token():
    """Ottiene il token CSRF dalla pagina principale"""
    try:
        response = requests.get("http://127.0.0.1:5005/")
        # Cerca il token CSRF nel meta tag
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]*)"', response.text)
        if csrf_match:
            return csrf_match.group(1)
    except:
        pass
    return None

def test_prompt_preview_with_csrf():
    """Testa l'endpoint prompt/preview con token CSRF"""
    url = "http://127.0.0.1:5005/ai/prompt/preview"
    
    # Ottieni il token CSRF
    csrf_token = get_csrf_token()
    if not csrf_token:
        print("❌ Impossibile ottenere il token CSRF")
        return
    
    print(f"🔐 CSRF Token ottenuto: {csrf_token[:20]}...")
    
    # Dati di test
    test_data = {
        'file_id': 1,
        'template_id': 1,
        'selected_categories': [],
        'batch_size': 3
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
    }
    
    try:
        print(f"🧪 Testing POST {url}")
        print(f"📊 Data: {test_data}")
        
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"📬 Status: {response.status_code}")
        
        if response.status_code == 401:
            print("ℹ️ Errore 401: Autenticazione richiesta (serve login)")
            print(f"📝 Response: {response.text[:200]}...")
        elif response.status_code == 400:
            print("❌ Errore 400 ancora presente")
            print(f"📝 Response: {response.text[:200]}...")
        elif response.status_code == 200:
            print("✅ Success! Errore CSRF risolto!")
            result = response.json()
            if result.get('success'):
                print(f"📝 Prompt generato correttamente, lunghezza: {len(result.get('prompt', ''))}")
            else:
                print(f"⚠️ Success HTTP ma errore applicativo: {result.get('error')}")
        else:
            print(f"⚠️ Status code inaspettato: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione - assicurati che l'app sia in esecuzione")
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    test_prompt_preview_with_csrf()
