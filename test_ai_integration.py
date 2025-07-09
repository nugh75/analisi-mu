#!/usr/bin/env python3
"""
Script per testare le integrazioni AI (Ollama e OpenRouter)
"""

import sys
import os
import json
from datetime import datetime

# Aggiungi il path dell'app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_client import OllamaClient
from services.openrouter_client import OpenRouterClient
from services.ai_annotator import AIAnnotatorService
from app import create_app

def test_ollama():
    """Testa la connessione e funzionalità di Ollama"""
    print("🔧 Test Ollama")
    print("-" * 50)
    
    client = OllamaClient("http://192.168.12.14:11435")
    
    # Test connessione
    print("📡 Test connessione...")
    if client.test_connection():
        print("✅ Connessione riuscita")
    else:
        print("❌ Connessione fallita")
        return False
    
    # Lista modelli
    print("\n📋 Modelli installati:")
    models = client.list_models()
    if models:
        for model in models[:5]:  # Mostra i primi 5
            print(f"   • {model.get('name', 'N/A')} - {model.get('size', 'N/A')}")
    else:
        print("   Nessun modello trovato")
    
    # Test generazione (se c'è almeno un modello)
    if models:
        model_name = models[0].get('name', '').split(':')[0]
        print(f"\n🧠 Test generazione con {model_name}...")
        
        messages = [
            {"role": "system", "content": "Sei un assistente per l'etichettatura di testi."},
            {"role": "user", "content": "Etichetta questo testo con una categoria: 'Mi piace molto studiare matematica'"}
        ]
        
        response = client.generate_chat(model_name, messages, temperature=0.7, max_tokens=100)
        
        if 'error' not in response:
            print("✅ Generazione riuscita:")
            content = response.get('message', {}).get('content', 'N/A')
            print(f"   Risposta: {content[:100]}...")
        else:
            print(f"❌ Errore generazione: {response['error']}")
            return False
    
    print("✅ Test Ollama completato")
    return True

def test_openrouter():
    """Testa la connessione e funzionalità di OpenRouter"""
    print("\n🌐 Test OpenRouter")
    print("-" * 50)
    
    # Cerca API key nell'ambiente
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("⚠️  API key OpenRouter non trovata nelle variabili d'ambiente")
        print("   Imposta OPENROUTER_API_KEY per testare OpenRouter")
        return False
    
    client = OpenRouterClient(api_key)
    
    # Test connessione
    print("📡 Test connessione...")
    if client.test_connection():
        print("✅ Connessione riuscita")
    else:
        print("❌ Connessione fallita (API key non valida?)")
        return False
    
    # Lista modelli gratuiti
    print("\n📋 Modelli gratuiti disponibili:")
    free_models = client.get_free_models()
    if free_models:
        for model in free_models[:3]:  # Mostra i primi 3
            print(f"   • {model.get('name', 'N/A')}")
    else:
        print("   Nessun modello gratuito trovato")
    
    # Test generazione con modello gratuito
    if free_models:
        model_id = free_models[0].get('id')
        print(f"\n🧠 Test generazione con {model_id}...")
        
        messages = [
            {"role": "system", "content": "Sei un assistente per l'etichettatura di testi."},
            {"role": "user", "content": "Etichetta questo testo con una categoria: 'Mi piace molto studiare matematica'"}
        ]
        
        response = client.generate_chat(model_id, messages, temperature=0.7, max_tokens=100)
        
        if 'error' not in response:
            print("✅ Generazione riuscita:")
            content = response.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')
            print(f"   Risposta: {content[:100]}...")
        else:
            print(f"❌ Errore generazione: {response['error']}")
            return False
    
    # Info utilizzo
    print("\n📊 Info utilizzo account:")
    usage = client.get_usage()
    if 'error' not in usage:
        print("✅ Dati utilizzo recuperati")
    else:
        print(f"⚠️  Impossibile recuperare dati utilizzo: {usage['error']}")
    
    print("✅ Test OpenRouter completato")
    return True

def test_ai_annotator():
    """Testa il servizio di annotazione AI"""
    print("\n🤖 Test AI Annotator Service")
    print("-" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            service = AIAnnotatorService()
            
            # Test creazione utente AI
            print("👤 Test creazione utente AI...")
            ai_user = service.get_or_create_ai_user()
            print(f"✅ Utente AI: {ai_user.username} (ID: {ai_user.id})")
            
            # Test configurazione attiva
            print("\n⚙️  Test configurazione attiva...")
            config = service.get_active_configuration()
            if config:
                print(f"✅ Configurazione attiva: {config.name} ({config.provider})")
            else:
                print("⚠️  Nessuna configurazione AI attiva")
            
            # Test costruzione prompt
            print("\n📝 Test costruzione prompt...")
            from models import Label
            labels = Label.query.limit(3).all()
            
            if labels:
                texts = ["Mi piace la matematica", "Studio storia antica"]
                prompt = service.build_annotation_prompt(texts, labels)
                print("✅ Prompt costruito:")
                print(f"   Lunghezza: {len(prompt)} caratteri")
                print(f"   Etichette incluse: {len(labels)}")
            else:
                print("⚠️  Nessuna etichetta trovata nel database")
            
            print("✅ Test AI Annotator completato")
            return True
            
        except Exception as e:
            print(f"❌ Errore nel test AI Annotator: {e}")
            return False

def test_complete_workflow():
    """Testa il flusso completo di annotazione AI"""
    print("\n🔄 Test Flusso Completo")
    print("-" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            from models import ExcelFile, TextCell, Label
            
            # Trova un file di test
            excel_file = ExcelFile.query.first()
            if not excel_file:
                print("⚠️  Nessun file Excel trovato per il test")
                return False
            
            print(f"📁 File di test: {excel_file.original_filename}")
            
            # Conta testi non annotati
            unannotated_count = TextCell.query.filter(
                TextCell.excel_file_id == excel_file.id
            ).limit(5).count()  # Limita per il test
            
            print(f"📝 Testi da testare: {min(unannotated_count, 5)}")
            
            # Verifica etichette
            labels_count = Label.query.count()
            print(f"🏷️  Etichette disponibili: {labels_count}")
            
            if labels_count == 0:
                print("⚠️  Nessuna etichetta disponibile per il test")
                return False
            
            service = AIAnnotatorService()
            config = service.get_active_configuration()
            
            if not config:
                print("⚠️  Nessuna configurazione AI attiva per il test completo")
                return False
            
            print(f"⚙️  Configurazione: {config.name}")
            print("✅ Test flusso completo pronto (simulazione)")
            
            # Nota: Non eseguiamo l'annotazione reale per evitare costi/carico
            print("   (Annotazione reale non eseguita in modalità test)")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore nel test flusso completo: {e}")
            return False

def main():
    """Esegue tutti i test"""
    print("🧪 TEST INTEGRAZIONI AI")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'ollama': False,
        'openrouter': False,
        'ai_annotator': False,
        'complete_workflow': False
    }
    
    # Test individuali
    try:
        results['ollama'] = test_ollama()
    except Exception as e:
        print(f"❌ Errore nel test Ollama: {e}")
    
    try:
        results['openrouter'] = test_openrouter()
    except Exception as e:
        print(f"❌ Errore nel test OpenRouter: {e}")
    
    try:
        results['ai_annotator'] = test_ai_annotator()
    except Exception as e:
        print(f"❌ Errore nel test AI Annotator: {e}")
    
    try:
        results['complete_workflow'] = test_complete_workflow()
    except Exception as e:
        print(f"❌ Errore nel test flusso completo: {e}")
    
    # Riepilogo
    print("\n📊 RIEPILOGO TEST")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<20} {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nRisultato finale: {success_count}/{total_count} test superati")
    
    if success_count == total_count:
        print("🎉 Tutti i test sono passati!")
        return 0
    else:
        print("⚠️  Alcuni test sono falliti. Controlla la configurazione.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
