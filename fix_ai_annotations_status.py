#!/usr/bin/env python3
"""
Script per correggere lo status delle annotazioni AI da rejected a pending_review
"""

from app import create_app
from models import db, CellAnnotation

def fix_ai_annotations_status():
    """Corregge lo status delle annotazioni AI"""
    app = create_app()
    
    with app.app_context():
        print("=== FIX STATUS ANNOTAZIONI AI ===\n")
        
        # Trova tutte le annotazioni AI con status rejected
        rejected_ai_annotations = CellAnnotation.query.filter(
            CellAnnotation.is_ai_generated == True,
            CellAnnotation.status == 'rejected'
        ).all()
        
        print(f"Trovate {len(rejected_ai_annotations)} annotazioni AI con status 'rejected'")
        
        if rejected_ai_annotations:
            confirm = input("Vuoi cambiarle a 'pending_review'? (y/N): ")
            if confirm.lower() == 'y':
                for annotation in rejected_ai_annotations:
                    annotation.status = 'pending_review'
                    annotation.reviewed_by = None
                    annotation.reviewed_at = None
                
                try:
                    db.session.commit()
                    print(f"✅ Aggiornate {len(rejected_ai_annotations)} annotazioni AI a status 'pending_review'")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Errore nell'aggiornamento: {e}")
            else:
                print("Operazione annullata")
        else:
            print("Nessuna annotazione AI da correggere")

if __name__ == '__main__':
    fix_ai_annotations_status()
