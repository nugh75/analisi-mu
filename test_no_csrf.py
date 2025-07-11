#!/usr/bin/env python3
"""
Test dell'endpoint di test senza CSRF
"""
import requests
import json

def test_prompt_preview_no_csrf():
    """Testa l'endpoint di test senza CSRF"""
    url = "http://127.0.0.1:5005/ai/prompt/preview/test"
    
    test_data = {
        'file_id': 1,
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
        
        if response.status_code == 200:
            print("✅ Success! Fix del lazy loading funziona!")
            result = response.json()
            print(f"📝 Debug info: {result.get('debug', {})}")
            print(f"📝 Prompt length: {len(result.get('prompt', ''))}")
            print(f"📝 First 200 chars: {result.get('prompt', '')[:200]}...")
        else:
            print(f"❌ Errore {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    test_prompt_preview_no_csrf()
