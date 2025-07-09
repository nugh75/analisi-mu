#!/usr/bin/env python3
"""
Script per debug della configurazione AI
"""

import os
import sys
import json

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, OpenRouterModel, TextCell
from services.openrouter_client import OpenRouterClient
from services.ollama_client import OllamaClient

def debug_ai_configuration():
    """Debug completo della configurazione AI"""
    app = create_app()
    
    with app.app_context():
        print("=== DEBUG CONFIGURAZIONE AI ===\n")
        
        # 1. Verifica configurazioni
        configs = AIConfiguration.query.all()
        print(f"📋 Configurazioni totali: {len(configs)}")
        
        for config in configs:
            print(f"\n🔧 CONFIG {config.id}: {config.name}")
            print(f"   Provider: {config.provider}")
            print(f"   Attiva: {config.is_active}")
            print(f"   Max Tokens: {config.max_tokens}")
            print(f"   Temperature: {config.temperature}")
            
            if config.provider == 'ollama':
                print(f"   URL: {config.ollama_url}")
                print(f"   Modello: {config.ollama_model}")
            elif config.provider == 'openrouter':
                print(f"   Modello: {config.openrouter_model}")
                api_key = config.openrouter_api_key
                if api_key:
                    print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
                else:
                    print("   ⚠️  API Key: MANCANTE!")
            
            # Test connessione
            print("   Test connessione:", end=" ")
            try:
                if config.provider == 'ollama':
                    client = OllamaClient(config.ollama_url)
                    if client.test_connection():
                        models = client.list_models()
                        print(f"✅ OK ({len(models)} modelli)")
                        # Verifica se il modello specifico è disponibile
                        model_names = [m['name'] for m in models]
                        if config.ollama_model in model_names:
                            print(f"   ✅ Modello '{config.ollama_model}' disponibile")
                        else:
                            print(f"   ❌ Modello '{config.ollama_model}' NON disponibile")
                            print(f"   📝 Modelli disponibili: {', '.join(model_names[:3])}...")
                    else:
                        print("❌ FALLITO")
                elif config.provider == 'openrouter':
                    if config.openrouter_api_key:
                        client = OpenRouterClient(config.openrouter_api_key)
                        if client.test_connection():
                            print("✅ OK")
                        else:
                            print("❌ FALLITO")
                            
                        # Test con un prompt semplice
                        print("   Test prompt semplice:", end=" ")
                        response = client.generate_chat(
                            config.openrouter_model,
                            [{"role": "user", "content": "Ciao, rispondi solo 'OK'"}],
                            0.1,
                            10
                        )
                        if response and 'error' not in response:
                            print("✅ OK")
                        else:
                            print("❌ FALLITO")
                            print(f"       Errore: {response}")
                    else:
                        print("❌ API Key mancante")
            except Exception as e:
                print(f"❌ ERRORE: {str(e)}")
        
        # 2. Verifica modelli OpenRouter
        print("\n📡 MODELLI OPENROUTER")
        or_models = OpenRouterModel.query.filter_by(is_available=True).limit(5).all()
        for model in or_models:
            print(f"   • {model.name} ({'GRATUITO' if model.is_free else 'A PAGAMENTO'})")
        
        # 3. Verifica dati di test
        print("\n📊 DATI DI TEST")
        text_cells = TextCell.query.limit(3).all()
        for cell in text_cells:
            print(f"   • Cella {cell.id}: {cell.text_content[:50]}...")
        
        # 4. Test completo con configurazione attiva
        active_config = AIConfiguration.query.filter_by(is_active=True).first()
        if active_config:
            print(f"\n🎯 TEST CON CONFIGURAZIONE ATTIVA: {active_config.name}")
            
            if active_config.provider == 'openrouter' and active_config.openrouter_api_key:
                test_openrouter_detailed(active_config)
        else:
            print("\n⚠️  Nessuna configurazione attiva!")

def test_openrouter_detailed(config: AIConfiguration):
    """Test dettagliato di OpenRouter"""
    try:
        client = OpenRouterClient(config.openrouter_api_key)
        
        # Test 1: Modelli disponibili
        print("   📋 Verifica modelli...", end=" ")
        models = client.list_models()
        if models:
            print(f"✅ {len(models)} modelli trovati")
            
            # Cerca il modello configurato
            model_found = False
            for model in models:
                if model.get('id') == config.openrouter_model:
                    model_found = True
                    print(f"   ✅ Modello '{config.openrouter_model}' trovato")
                    break
            
            if not model_found:
                print(f"   ❌ Modello '{config.openrouter_model}' NON trovato!")
                print("   📝 Primi 5 modelli disponibili:")
                for model in models[:5]:
                    print(f"      - {model.get('id', 'N/A')}")
        else:
            print("❌ Nessun modello trovato")
        
        # Test 2: Chat semplice
        print("   💬 Test chat semplice...", end=" ")
        messages = [{"role": "user", "content": "Rispondi solo: OK"}]
        response = client.generate_chat(
            config.openrouter_model,
            messages,
            0.1,
            10
        )
        
        if response and 'error' not in response:
            print("✅ OK")
            choices = response.get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                print(f"   📝 Risposta: '{content.strip()}'")
        else:
            print("❌ FALLITO")
            print(f"   📝 Errore dettagliato: {json.dumps(response, indent=2)}")
        
        # Test 3: Prompt di etichettatura
        print("   🏷️  Test etichettatura...", end=" ")
        prompt = '''Analizza questo testo e assegna un'etichetta appropriata:
        
Testo: "ChatGPT mi aiuta molto a scrivere i saggi universitari"

Etichette disponibili: Positivo, Negativo, Scrittura, Studio

Rispondi in JSON: {"label": "nome_etichetta", "confidence": 0.8}'''
        
        messages = [
            {"role": "system", "content": "Sei un assistente per l'etichettatura di testi educativi."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.generate_chat(
            config.openrouter_model,
            messages,
            config.temperature,
            config.max_tokens
        )
        
        if response and 'error' not in response:
            print("✅ OK")
            choices = response.get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                print(f"   📝 Risposta: {content.strip()[:100]}...")
        else:
            print("❌ FALLITO")
            print(f"   📝 Errore: {response}")
            
    except Exception as e:
        print(f"   ❌ ERRORE: {str(e)}")

if __name__ == "__main__":
    debug_ai_configuration()
