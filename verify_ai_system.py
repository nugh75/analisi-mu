#!/usr/bin/env python3
"""
Script di verifica finale del sistema AI
"""

import os
import sys
import time

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, OpenRouterModel, ExcelFile, TextCell, CellAnnotation

def verify_ai_system():
    """Verifica completa del sistema AI"""
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICA SISTEMA AI ===\n")
        
        all_ok = True
        
        # 1. Verifica configurazione AI
        print("1. CONFIGURAZIONE AI")
        print("-" * 50)
        ai_config = AIConfiguration.query.filter_by(is_active=True).first()
        if ai_config:
            print("✓ Configurazione attiva trovata:")
            print(f"  - Nome: {ai_config.name}")
            print(f"  - Provider: {ai_config.provider}")
            if ai_config.provider == 'ollama':
                print(f"  - Modello: {ai_config.ollama_model}")
                print(f"  - URL: {ai_config.ollama_url}")
            else:
                print(f"  - Modello: {ai_config.openrouter_model}")
            print(f"  - Max Tokens: {ai_config.max_tokens}")
            print(f"  - Temperature: {ai_config.temperature}")
        else:
            print("✗ Nessuna configurazione AI attiva!")
            all_ok = False
        
        # 2. Verifica modelli OpenRouter
        print("\n2. MODELLI OPENROUTER")
        print("-" * 50)
        total_models = OpenRouterModel.query.count()
        free_models = OpenRouterModel.query.filter_by(is_free=True).count()
        print(f"✓ Modelli totali: {total_models}")
        print(f"✓ Modelli gratuiti: {free_models}")
        
        # Mostra alcuni modelli gratuiti
        print("\nAlcuni modelli gratuiti disponibili:")
        sample_models = OpenRouterModel.query.filter_by(is_free=True).limit(5).all()
        for model in sample_models:
            print(f"  - {model.name} ({model.model_id})")
        
        # 3. Verifica file Excel e celle
        print("\n3. DATI FILE EXCEL")
        print("-" * 50)
        excel_files = ExcelFile.query.all()
        print(f"✓ File Excel totali: {len(excel_files)}")
        
        if excel_files:
            for file in excel_files:
                cell_count = TextCell.query.filter_by(excel_file_id=file.id).count()
                ai_annotations = CellAnnotation.query.join(TextCell).filter(
                    TextCell.excel_file_id == file.id,
                    CellAnnotation.is_ai_generated == True
                ).count()
                print(f"\n  File: {file.original_filename}")
                print(f"  - ID: {file.id}")
                print(f"  - Celle totali: {cell_count}")
                print(f"  - Annotazioni AI: {ai_annotations}")
        else:
            print("⚠️  Nessun file Excel caricato")
        
        # 4. Test connessione AI
        print("\n4. TEST CONNESSIONE AI")
        print("-" * 50)
        if ai_config:
            if ai_config.provider == 'ollama':
                from services.ollama_client import OllamaClient
                try:
                    client = OllamaClient(ai_config.ollama_url)
                    models = client.list_models()
                    if models:
                        print(f"✓ Connessione Ollama OK - {len(models)} modelli disponibili")
                        print(f"  Modelli: {', '.join([m['name'] for m in models[:3]])}...")
                    else:
                        print("⚠️  Connessione OK ma nessun modello trovato")
                except Exception as e:
                    print(f"✗ Errore connessione Ollama: {str(e)}")
                    all_ok = False
            
            elif ai_config.provider == 'openrouter':
                from services.openrouter_client import OpenRouterClient
                try:
                    client = OpenRouterClient(ai_config.openrouter_api_key)
                    if client.test_connection():
                        print("✓ Connessione OpenRouter OK")
                    else:
                        print("✗ Test connessione OpenRouter fallito")
                        all_ok = False
                except Exception as e:
                    print(f"✗ Errore connessione OpenRouter: {str(e)}")
                    all_ok = False
        
        # 5. Verifica UI
        print("\n5. VERIFICA INTERFACCIA UTENTE")
        print("-" * 50)
        print("Controlli da effettuare manualmente:")
        print("  □ Badge di stato AI con sfondo colorato corretto")
        print("  □ Pulsante 'Genera Etichette AI' abilitato")
        print("  □ Pulsante 'Rivedi Suggerimenti' mostra il conteggio corretto")
        print("  □ Configurazione AI accessibile dal pulsante ingranaggio")
        print("  □ Modelli OpenRouter gratuiti visibili nella selezione")
        
        # Riepilogo
        print("\n" + "=" * 50)
        if all_ok:
            print("✅ SISTEMA AI FUNZIONANTE CORRETTAMENTE")
            print("\nProssimi passi:")
            print("1. Accedi all'applicazione: http://localhost:5004")
            print("2. Login: admin / admin123")
            print("3. Apri un file Excel")
            print("4. Verifica che lo stato AI sia 'OLLAMA (qwen3:32b)'")
            print("5. Clicca 'Genera Etichette AI' per testare la generazione")
        else:
            print("⚠️  ALCUNI PROBLEMI RILEVATI")
            print("\nVerifica i problemi segnalati sopra.")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    verify_ai_system()