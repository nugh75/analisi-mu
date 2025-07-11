#!/usr/bin/env python3
"""
Diagnostica completa del sistema AI
"""

print('=== DIAGNOSTICA AI SYSTEM ===')
print()

# Test connessione Ollama
print('1. TEST CONNESSIONE OLLAMA')
try:
    import requests
    response = requests.get('http://192.168.129.14:11435/api/tags', timeout=10)
    if response.status_code == 200:
        data = response.json()
        models = [m['name'] for m in data.get('models', [])]
        print(f'✅ Ollama OK - Modelli disponibili: {models}')
    else:
        print(f'❌ Ollama risponde ma status: {response.status_code}')
except Exception as e:
    print(f'❌ Ollama non raggiungibile: {e}')

print()
print('2. TEST CONFIGURAZIONE AI')
from app import create_app
app = create_app()
with app.app_context():
    from models import AIConfiguration
    config = AIConfiguration.query.filter_by(is_active=True).first()
    if config:
        print(f'✅ Config attiva: {config.provider} - {config.name}')
        print(f'   Provider: {config.provider}')
        if config.provider == 'ollama':
            print(f'   Ollama URL: {config.ollama_url}')
            print(f'   Ollama Model: {config.ollama_model}')
        elif config.provider == 'openrouter':
            print(f'   OpenRouter Model: {config.openrouter_model}')
            print(f'   API Key: {"***" + config.openrouter_api_key[-4:] if config.openrouter_api_key else "Non configurata"}')
        print(f'   Max Tokens: {config.max_tokens}')
        print(f'   Temperature: {config.temperature}')
    else:
        print('❌ Nessuna configurazione AI attiva')

print()
print('3. TEST AI SERVICE')
try:
    from services.ai_annotator import AIAnnotatorService
    ai_service = AIAnnotatorService()
    templates = ai_service.get_available_templates()
    print(f'✅ AI Service OK - {len(templates)} template disponibili')
    for tid, template in templates.items():
        print(f'   Template {tid}: {template["name"]}')
except Exception as e:
    print(f'❌ Errore AI Service: {e}')
    import traceback
    traceback.print_exc()

print()
print('4. TEST GENERAZIONE PROMPT')
try:
    from models import Label, Category
    with app.app_context():  # Aggiungi context per query database
        labels = Label.query.filter_by(is_active=True).limit(5).all()
        print(f'✅ Trovate {len(labels)} etichette per test')
        
        if labels:
            test_texts = ["Questo è un test", "Un altro testo di prova"]
            prompt = ai_service.build_annotation_prompt(test_texts, labels, 1)
            print(f'✅ Prompt generato (lunghezza: {len(prompt)} caratteri)')
            print(f'   Prime 200 caratteri: {prompt[:200]}...')
        else:
            print('❌ Nessuna etichetta disponibile per il test')
        
except Exception as e:
    print(f'❌ Errore generazione prompt: {e}')
    import traceback
    traceback.print_exc()

print()
print('5. IDENTIFICAZIONE PROBLEMI')
print('📋 Problemi identificati:')

# Verifica timeout e configurazione
if config and config.provider == 'ollama':
    print(f'   - Batch size attuale: NON CONFIGURABILE (hardcoded a 20)')
    print(f'   - Timeout: NON CONFIGURATO nel database (usa default 60s)')
    print(f'   - Modello usato: {config.ollama_model}')
    
print()
print('6. RACCOMANDAZIONI')
print('🔧 Azioni necessarie:')
print('   1. Aggiungere campo timeout alla configurazione AI')
print('   2. Aggiungere campo batch_size alla configurazione AI') 
print('   3. Ridurre timeout da 60s a valori più ragionevoli (10-30s)')
print('   4. Implementare sistema template management nell\'admin')
print('   5. Aggiungere retry logic per gestire timeout occasionali')
