#!/usr/bin/env python3
"""
Test semplice per verificare la funzionalità del modal AI
"""

import os
import sys
import json

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, ExcelFile, CellAnnotation, AIConfiguration, PromptTemplate

def test_modal_simple():
    """Test semplice della funzionalità del modal AI"""
    print("🧪 TEST SEMPLICE MODAL AI")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # 1. Verifica che esistano template e configurazioni
        templates = PromptTemplate.query.all()
        configs = AIConfiguration.query.all()
        
        print(f"\n✅ Template disponibili: {len(templates)}")
        for t in templates:
            print(f"   - {t.name} (ID: {t.id}, Categoria: {t.category})")
            
        print(f"\n✅ Configurazioni disponibili: {len(configs)}")
        for c in configs:
            print(f"   - {c.name} (ID: {c.id}, Provider: {c.provider}, Attiva: {c.is_active})")
        
        # 2. Test degli endpoint con il client Flask
        print("\n🌐 Test endpoint API:")
        
        with app.test_client() as client:
            # Test endpoint templates
            print("\n🌐 Test endpoint /ai/templates:")
            response = client.get('/ai/templates')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Templates disponibili: {len(data.get('templates', []))}")
                for t in data.get('templates', []):
                    print(f"      - {t['name']} (ID: {t['id']})")
            else:
                print(f"   Errore: {response.data}")
            
            # Test endpoint configurations  
            print("\n🌐 Test endpoint /ai/configurations:")
            response = client.get('/ai/configurations')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Configurazioni disponibili: {len(data.get('configurations', []))}")
                for c in data.get('configurations', []):
                    print(f"      - {c['name']} ({c['provider']}) - Attiva: {c['is_active']}")
            else:
                print(f"   Errore: {response.data}")

if __name__ == "__main__":
    test_modal_simple()
