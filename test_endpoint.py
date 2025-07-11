#!/usr/bin/env python3
"""
Script di test per l'endpoint prompt/preview
"""
import sys
import json

sys.path.append('.')

from app import create_app
from models import db, ExcelFile, TextCell

def test_prompt_preview_endpoint():
    """Test dell'endpoint prompt/preview"""
    print("🧪 Testing prompt/preview endpoint...")
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Trova un file Excel esistente per il test
            excel_file = ExcelFile.query.first()
            
            if not excel_file:
                print("❌ Nessun file Excel trovato nel database")
                return False
            
            print(f"📁 Usando file: {excel_file.filename} (ID: {excel_file.id})")
            
            # Prepara i dati della richiesta
            test_data = {
                'file_id': excel_file.id,
                'template_id': 1,
                'selected_categories': [],
                'batch_size': 3
            }
            
            print(f"📤 Sending POST request to /ai/prompt/preview")
            print(f"📊 Data: {test_data}")
            
            # Simula login (crea una sessione semplificata)
            with client.session_transaction() as sess:
                sess['_user_id'] = '1'  # Simula utente loggato
                sess['_fresh'] = True
            
            # Effettua la richiesta
            response = client.post(
                '/ai/prompt/preview',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            print(f"📬 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.get_json()
                if result.get('success'):
                    print(f"✅ Endpoint test SUCCESS!")
                    print(f"📝 Prompt length: {len(result.get('prompt', ''))}")
                    return True
                else:
                    print(f"❌ Endpoint returned error: {result.get('error')}")
                    return False
            else:
                print(f"❌ HTTP Error {response.status_code}")
                try:
                    error_data = response.get_json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.get_data(as_text=True)}")
                return False

if __name__ == "__main__":
    success = test_prompt_preview_endpoint()
    sys.exit(0 if success else 1)
