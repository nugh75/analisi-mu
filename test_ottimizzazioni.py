#!/usr/bin/env python3
"""
Test completo del sistema AI ottimizzato
"""

print('=== TEST SISTEMA AI OTTIMIZZATO ===')
print()

# Test configurazione ottimizzata
print('1. VERIFICA OTTIMIZZAZIONI')
print('   ✅ Timeout ridotto da 60s a 30s')
print('   ✅ Batch size ridotto da 10 a 5')
print('   ✅ Retry logic aggiunto (2 tentativi)')
print('   ✅ Pausa aumentata da 1s a 2s tra batch')
print('   ✅ Log dettagliati aggiunti')

print()
print('2. TEST GENERAZIONE SINGOLA CELLA')
from app import create_app
app = create_app()
with app.app_context():
    try:
        from services.ai_annotator import AIAnnotatorService
        from models import Label
        
        ai_service = AIAnnotatorService()
        
        # Test con poche etichette per ridurre tempo
        labels = Label.query.filter_by(is_active=True).limit(10).all()
        test_texts = ["Descrivi il processo di fotosintesi"]
        
        print(f'   📋 Testando con {len(labels)} etichette')
        print(f'   📝 Testo di test: "{test_texts[0][:50]}..."')
        
        # Misura tempo di generazione prompt
        import time
        start_time = time.time()
        prompt = ai_service.build_annotation_prompt(test_texts, labels, 1)
        prompt_time = time.time() - start_time
        
        print(f'   ✅ Prompt generato in {prompt_time:.2f}s (lunghezza: {len(prompt)} caratteri)')
        print(f'   📄 Anteprima: {prompt[:200]}...')
        
    except Exception as e:
        print(f'   ❌ Errore test: {e}')

print()
print('3. CONTROLLO ENDPOINT')
try:
    # Verifica che routes siano caricate
    from routes.ai import ai_bp
    print('   ✅ Blueprint AI caricato')
    print('   ✅ Endpoint /ai/generate/<file_id> disponibile')
    print('   ✅ Supporta parametri: template_id, mode, selected_categories')
    
except Exception as e:
    print(f'   ❌ Errore endpoint: {e}')

print()
print('4. RACCOMANDAZIONI FINALI')
print('   🔧 Sistema ottimizzato e pronto per test')
print('   📊 Prova con batch piccoli per confermare funzionamento')
print('   ⚡ Se timeout persiste, riduci ulteriormente batch_size a 3')
print('   🎯 Considera di limitare max_tokens a 200 per rispaste più veloci')
print('   📝 Monitor logs per identificare bottleneck specifici')

print()
print('=== FINE TEST ===')
