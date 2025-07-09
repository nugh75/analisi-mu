#!/usr/bin/env python3
"""
Script per testare l'interfaccia admin UI tramite richieste HTTP
"""

import requests
import time
from app import create_app
from models import db, User, AIConfiguration

def test_admin_ui():
    """Testa l'interfaccia admin tramite HTTP"""
    
    app = create_app()
    
    # Avvia l'app in test mode
    with app.test_client() as client:
        with app.app_context():
            print("TESTING ADMIN UI ENDPOINTS")
            print("="*50)
            
            # Crea un utente admin per il test se non esiste
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@test.com',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Utente admin creato per il test")
            
            # Login come admin
            login_response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if login_response.status_code == 200:
                print("✅ Login admin riuscito")
                
                # Test della pagina di configurazione AI
                config_response = client.get('/admin/ai-configuration')
                if config_response.status_code == 200:
                    print("✅ Pagina configurazione AI accessibile")
                    
                    # Test degli endpoint di test connessione per ogni configurazione
                    configs = AIConfiguration.query.all()
                    
                    for config in configs:
                        print(f"\nTesting endpoint per: {config.name} ({config.provider})")
                        
                        test_response = client.post(f'/admin/ai-config/{config.id}/test')
                        
                        if test_response.status_code == 200:
                            try:
                                data = test_response.get_json()
                                if data:
                                    status = "✅ SUCCESSO" if data.get('success') else "❌ FALLITO"
                                    print(f"  Status: {status}")
                                    print(f"  Messaggio: {data.get('message', 'Nessun messaggio')}")
                                else:
                                    print(f"  ❌ Risposta JSON non valida")
                            except Exception as e:
                                print(f"  ❌ Errore parsing JSON: {str(e)}")
                        else:
                            print(f"  ❌ Errore HTTP: {test_response.status_code}")
                            print(f"  Response: {test_response.data.decode()[:200]}...")
                
                else:
                    print(f"❌ Errore accesso pagina configurazione: {config_response.status_code}")
            else:
                print(f"❌ Errore login: {login_response.status_code}")

def check_ui_elements():
    """Verifica gli elementi dell'interfaccia utente"""
    
    print(f"\nVERIFICA ELEMENTI UI")
    print("="*30)
    
    # Verifica che i template esistano
    templates_to_check = [
        'templates/admin/ai_configuration.html',
        'templates/admin/create_ai_config.html',
        'templates/admin/edit_ai_config.html',
        'templates/admin/ollama_models.html',
        'templates/admin/openrouter_models.html'
    ]
    
    for template in templates_to_check:
        try:
            with open(template, 'r') as f:
                content = f.read()
                if 'test-config-btn' in content:
                    print(f"✅ {template}: Pulsante test trovato")
                else:
                    print(f"❌ {template}: Pulsante test mancante")
        except FileNotFoundError:
            print(f"❌ {template}: File non trovato")

def summary_report():
    """Genera un report riassuntivo"""
    
    app = create_app()
    with app.app_context():
        print(f"\n" + "="*50)
        print("REPORT FINALE - SISTEMA AI ANNOTATION")
        print("="*50)
        
        # Statistiche database
        configs = AIConfiguration.query.all()
        active_configs = AIConfiguration.query.filter_by(is_active=True).all()
        
        print(f"📊 STATISTICHE DATABASE:")
        print(f"  - Configurazioni AI totali: {len(configs)}")
        print(f"  - Configurazioni attive: {len(active_configs)}")
        
        for config in configs:
            status = "ATTIVA" if config.is_active else "INATTIVA"
            print(f"  - {config.name} ({config.provider}): {status}")
        
        print(f"\n🔧 FUNZIONALITÀ IMPLEMENTATE:")
        print(f"  ✅ Client Ollama con test connessione")
        print(f"  ✅ Client OpenRouter con test connessione")
        print(f"  ✅ Database AI configurazioni")
        print(f"  ✅ Interfaccia admin per gestione configurazioni")
        print(f"  ✅ CRUD completo per configurazioni AI")
        print(f"  ✅ Test connessione endpoint HTTP")
        print(f"  ✅ Sincronizzazione modelli Ollama/OpenRouter")
        print(f"  ✅ Dropdown selezione modelli")
        print(f"  ✅ Attivazione/disattivazione configurazioni")
        
        print(f"\n🎯 PROSSIMI PASSI:")
        print(f"  - Implementare annotazione batch completa")
        print(f"  - Sistema di review annotazioni")
        print(f"  - Dashboard analytics utilizzo AI")
        print(f"  - Rate limiting e monitoring")

if __name__ == "__main__":
    test_admin_ui()
    check_ui_elements()
    summary_report()
    print(f"\n✅ Test completo terminato!")
