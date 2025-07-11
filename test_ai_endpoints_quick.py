#!/usr/bin/env python3
"""
Test rapido degli endpoint AI migliorati
"""

import requests
import json

def test_ai_endpoints():
    """Testa gli endpoint AI migliorati"""
    base_url = "http://localhost:5004"
    
    print("=== Test Endpoint AI Migliorati ===\n")
    
    # 1. Test template disponibili
    print("1. Test /ai/templates/available...")
    try:
        response = requests.get(f"{base_url}/ai/templates/available")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                templates = data.get('templates', {})
                print(f"   ✓ {len(templates)} template trovati")
                for tid, template in templates.items():
                    print(f"     - {tid}: {template['name']}")
            else:
                print(f"   ⚠️ Errore: {data.get('error')}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Errore connessione: {e}")
    
    # 2. Test validazione configurazione
    print("\n2. Test /ai/validate-configuration...")
    try:
        response = requests.get(f"{base_url}/ai/validate-configuration")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                config = data.get('config', {})
                print(f"   ✓ Configurazione valida: {config['provider']} - {config['model']}")
                print(f"     Etichette attive: {config['active_labels_count']}")
            else:
                print(f"   ⚠️ Configurazione non valida: {data.get('error')}")
                if 'validation_errors' in data:
                    for error in data['validation_errors']:
                        print(f"     - {error}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Errore connessione: {e}")
    
    # 3. Test configurazione corrente
    print("\n3. Test /ai/config/current...")
    try:
        response = requests.get(f"{base_url}/ai/config/current")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                config = data.get('config', {})
                print(f"   ✓ Config attiva: {config['name']} ({config['provider']})")
            else:
                print(f"   ⚠️ Nessuna config attiva: {data.get('message')}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Errore connessione: {e}")
    
    print("\n=== Test completato ===")

if __name__ == "__main__":
    test_ai_endpoints()
