#!/usr/bin/env python3
"""
Test della generazione AI con configurazione corretta
"""

import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.ai_annotator import AIAnnotatorService
from models import AIConfiguration, TextCell, ExcelFile

def test_ai_generation():
    """Testa la generazione AI con poche celle"""
    
    app = create_app()
    
    with app.app_context():
        # Verifica configurazione attiva
        config = AIConfiguration.query.filter_by(is_active=True).first()
        if not config:
            print("❌ Nessuna configurazione AI attiva!")
            return
        
        print(f"✅ Configurazione attiva: {config.name} ({config.provider})")
        print(f"🤖 Modello: {config.ollama_model if config.provider == 'ollama' else config.openrouter_model}")
        
        # Trova un file Excel
        excel_file = ExcelFile.query.first()
        if not excel_file:
            print("❌ Nessun file Excel trovato!")
            return
        
        print(f"📁 File test: {excel_file.original_filename}")
        
        # Trova alcune celle non annotate
        test_cells = TextCell.query.filter_by(
            excel_file_id=excel_file.id
        ).filter(
            ~TextCell.annotations.any()
        ).limit(3).all()
        
        if not test_cells:
            print("❌ Nessuna cella non annotata trovata!")
            return
        
        print(f"🔍 Celle di test trovate: {len(test_cells)}")
        
        # Inizializza il servizio AI
        ai_service = AIAnnotatorService()
        
        # Testa la generazione
        print("\n🚀 Avvio test generazione...")
        
        try:
            result = ai_service.generate_annotations(excel_file.id, batch_size=2)
            
            if 'error' in result:
                print(f"❌ Errore generazione: {result['error']}")
            else:
                print(f"✅ Generazione completata!")
                print(f"📊 Risultati: {result}")
                print(f"🏷️  Annotazioni create: {len(result.get('annotations', []))}")
                
                # Mostra alcune annotazioni generate
                for i, annotation in enumerate(result.get('annotations', [])[:3]):
                    print(f"   {i+1}. Cella {annotation.get('cell_id')}: {annotation.get('label_name')} (conf: {annotation.get('confidence', 0):.2f})")
                
        except Exception as e:
            print(f"❌ Errore durante il test: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_ai_generation()
