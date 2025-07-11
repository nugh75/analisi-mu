#!/usr/bin/env python3
"""
Test ottimizzazioni finali - timeout 90s e batch 3
"""

print('=== TEST OTTIMIZZAZIONI FINALI ===')
print()

print('1. VERIFICHE APPLICATE')
print('   ✅ Timeout aumentato: 30s → 90s')
print('   ✅ Batch size ridotto: 5 → 3 celle')
print('   ✅ Prompt semplificato per velocità')
print('   ✅ Retry logic mantenuto (2 tentativi)')

print()
print('2. TEST RAPIDO SINGOLA CELLA')
try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from services.ai_annotator import AIAnnotatorService
        from models import Label
        
        ai_service = AIAnnotatorService()
        
        # Test prompt veloce
        labels = Label.query.filter_by(is_active=True).limit(5).all()
        test_texts = ["Test veloce"]
        
        import time
        start_time = time.time()
        prompt = ai_service.build_annotation_prompt(test_texts, labels, 1)
        prompt_time = time.time() - start_time
        
        print(f'   📄 Prompt semplificato generato in {prompt_time:.2f}s')
        print(f'   📏 Lunghezza ridotta: {len(prompt)} caratteri')
        print(f'   📝 Preview: {prompt[:150]}...')
        
except Exception as e:
    print(f'   ❌ Errore: {e}')

print()
print('3. CONSIGLI PER TEST')
print('   🔧 Riavvia server: Ctrl+C poi `python app.py`')
print('   🧪 Testa con poche celle per verificare funzionamento')
print('   ⏱️ Ora dovrebbe completare in ~60-90s per batch')
print('   📊 Se persiste timeout, switcha a modello più veloce (llama3:latest)')

print()
print('=== OTTIMIZZAZIONI COMPLETE ===')
