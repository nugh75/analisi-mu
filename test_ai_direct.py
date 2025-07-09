#!/usr/bin/env python3
"""
Test diretto del sistema AI con llama3:latest
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, TextCell, ExcelFile
from services.ai_annotator import AIAnnotatorService

def test_ai_generation():
    """Test diretto della generazione AI"""
    
    app = create_app()
    
    with app.app_context():
        print("=== TEST GENERAZIONE AI ===\n")
        
        # Verifica configurazione
        config = AIConfiguration.query.filter_by(is_active=True).first()
        if not config:
            print("❌ Nessuna configurazione AI attiva!")
            return
        
        print(f"✅ Configurazione attiva: {config.name}")
        print(f"🔧 Provider: {config.provider}")
        print(f"🤖 Modello: {config.ollama_model}")
        print(f"🌐 URL: {config.ollama_url}")
        
        # Trova un file Excel
        excel_file = ExcelFile.query.first()
        if not excel_file:
            print("❌ Nessun file Excel trovato!")
            return
        
        print(f"📊 File Excel: {excel_file.original_filename}")
        
        # Trova celle non annotate
        unannotated_cells = TextCell.query.filter_by(excel_file_id=excel_file.id).filter(
            ~TextCell.annotations.any()
        ).limit(3).all()
        
        if not unannotated_cells:
            print("❌ Nessuna cella non annotata trovata!")
            return
        
        print(f"📝 Celle da processare: {len(unannotated_cells)}")
        
        # Test del servizio AI
        ai_service = AIAnnotatorService()
        
        print("\n🔄 Iniziando generazione AI...")
        
        # Usa batch_size piccolo per test
        result = ai_service.generate_annotations(excel_file.id, batch_size=2)
        
        print(f"\n📋 RISULTATI:")
        print(f"   Successo: {'✅' if 'error' not in result else '❌'}")
        
        if 'error' in result:
            print(f"   Errore: {result['error']}")
        else:
            print(f"   Messaggio: {result.get('message', 'N/A')}")
            print(f"   Processate: {result.get('total_processed', 0)}")
            print(f"   Annotazioni create: {len(result.get('annotations', []))}")
            
            # Mostra le prime annotazioni
            annotations = result.get('annotations', [])
            if annotations:
                print(f"\n🏷️  PRIME ANNOTAZIONI:")
                for i, ann in enumerate(annotations[:3]):
                    print(f"   {i+1}. Testo: {ann.get('text', 'N/A')[:50]}...")
                    print(f"      Etichetta: {ann.get('label', 'N/A')}")
                    print(f"      Confidenza: {ann.get('confidence', 'N/A')}")
                    print()

if __name__ == "__main__":
    test_ai_generation()
