#!/usr/bin/env python3
"""
Script per ottimizzare e fixare la pipeline AI
"""

from app import create_app
from models import db, CellAnnotation, TextCell, Label
from services.ai_annotator import AIAnnotatorService

def fix_ai_pipeline():
    """Ottimizza la pipeline AI"""
    app = create_app()
    
    with app.app_context():
        print("=== OTTIMIZZAZIONE PIPELINE AI ===\n")
        
        # 1. Verifica stato attuale
        ai_annotations = CellAnnotation.query.filter_by(is_ai_generated=True).all()
        pending = [a for a in ai_annotations if a.status == 'pending_review']
        
        print(f"📊 Stato annotazioni AI:")
        print(f"   - Totali: {len(ai_annotations)}")
        print(f"   - Pending: {len(pending)}")
        
        # 2. Test batch size ottimale
        test_file_id = 1
        target_cells = TextCell.query.filter(
            TextCell.excel_file_id == test_file_id,
            ~TextCell.id.in_(
                db.session.query(CellAnnotation.text_cell_id).distinct()
            )
        ).limit(10).all()  # Test con solo 10 celle
        
        print(f"\n🧪 Test con {len(target_cells)} celle...")
        
        ai_service = AIAnnotatorService()
        
        # Test normale
        print("\n🆕 Test generazione normale (batch piccolo)...")
        result = ai_service.generate_annotations(test_file_id, batch_size=5, re_annotate=False)
        
        if 'error' in result:
            print(f"❌ Errore: {result['error']}")
        else:
            print(f"✅ Generazione completata:")
            print(f"   - Processate: {result.get('total_processed', 0)} celle")
            print(f"   - Annotazioni create: {len(result.get('annotations', []))}")
        
        # Test ri-etichettatura
        print("\n🔄 Test ri-etichettatura...")
        result_re = ai_service.generate_annotations(test_file_id, batch_size=3, re_annotate=True)
        
        if 'error' in result_re:
            print(f"❌ Errore: {result_re['error']}")
        else:
            print(f"✅ Ri-etichettatura completata:")
            print(f"   - Processate: {result_re.get('total_processed', 0)} celle")
            print(f"   - Annotazioni create: {len(result_re.get('annotations', []))}")

if __name__ == '__main__':
    fix_ai_pipeline()
