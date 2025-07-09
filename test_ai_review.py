#!/usr/bin/env python3
"""
Script per testare la generazione e revisione delle annotazioni AI
"""

import os
import sys
import requests
import json

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, CellAnnotation, TextCell, ExcelFile, Label, User

def test_ai_review_system():
    app = create_app()
    
    with app.app_context():
        print("=== TEST SISTEMA REVISIONE AI ===\n")
        
        # 1. Verifica se abbiamo file Excel
        files = ExcelFile.query.all()
        if not files:
            print("❌ Nessun file Excel trovato")
            return
        
        file = files[0]
        print(f"✅ File di test: {file.original_filename}")
        
        # 2. Verifica se abbiamo celle di testo
        cells = TextCell.query.filter_by(excel_file_id=file.id).limit(5).all()
        if not cells:
            print("❌ Nessuna cella di testo trovata")
            return
        
        print(f"✅ Celle di testo disponibili: {len(cells)}")
        
        # 3. Verifica se abbiamo etichette
        labels = Label.query.all()
        if not labels:
            print("❌ Nessuna etichetta trovata")
            return
        
        label = labels[0]
        print(f"✅ Etichetta di test: {label.name}")
        
        # 4. Verifica utente admin
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = User.query.first()
        
        if not admin_user:
            print("❌ Nessun utente trovato")
            return
        
        print(f"✅ Utente di test: {admin_user.username}")
        
        # 5. Crea annotazioni AI di test se non esistono
        existing_ai = CellAnnotation.query.filter_by(is_ai_generated=True).first()
        
        if not existing_ai:
            print("\n📝 Creando annotazioni AI di test...")
            
            for i, cell in enumerate(cells[:3]):
                # Controlla se la cella ha già annotazioni
                existing = CellAnnotation.query.filter_by(text_cell_id=cell.id).first()
                if existing:
                    continue
                    
                annotation = CellAnnotation(
                    text_cell_id=cell.id,
                    label_id=label.id,
                    user_id=admin_user.id,
                    is_ai_generated=True,
                    status='pending_review',
                    ai_confidence=0.85 - (i * 0.1),
                    ai_model='llama3:latest',
                    ai_provider='ollama'
                )
                db.session.add(annotation)
            
            try:
                db.session.commit()
                print("✅ Annotazioni AI di test create")
            except Exception as e:
                print(f"❌ Errore nella creazione: {e}")
                db.session.rollback()
                return
        
        # 6. Verifica annotazioni AI pending
        pending_annotations = CellAnnotation.query.filter(
            CellAnnotation.is_ai_generated == True,
            CellAnnotation.status == 'pending_review'
        ).all()
        
        print(f"\n📊 Annotazioni AI in attesa: {len(pending_annotations)}")
        
        if pending_annotations:
            for ann in pending_annotations[:3]:
                print(f"   - ID: {ann.id}, Label: {ann.label.name}, Confidence: {ann.ai_confidence}")
        
        # 7. Test endpoint di revisione
        if pending_annotations:
            annotation_id = pending_annotations[0].id
            
            # Test via API diretta (senza web server)
            print(f"\n🧪 Test revisione annotazione ID: {annotation_id}")
            
            # Simula accettazione
            try:
                from services.ai_annotator import AIAnnotatorService
                ai_service = AIAnnotatorService()
                
                # Test accettazione
                success = ai_service.review_annotation(annotation_id, 'accept', admin_user.id)
                if success:
                    print("✅ Accettazione funziona")
                    
                    # Ricarica l'annotazione per verificare il cambio di status
                    ann = CellAnnotation.query.get(annotation_id)
                    print(f"   Status dopo accettazione: {ann.status}")
                    
                    # Test rifiuto su un'altra annotazione
                    if len(pending_annotations) > 1:
                        annotation_id_2 = pending_annotations[1].id
                        success = ai_service.review_annotation(annotation_id_2, 'reject', admin_user.id)
                        if success:
                            print("✅ Rifiuto funziona")
                            ann2 = CellAnnotation.query.get(annotation_id_2)
                            print(f"   Status dopo rifiuto: {ann2.status}")
                        else:
                            print("❌ Rifiuto fallito")
                else:
                    print("❌ Accettazione fallita")
                    
            except Exception as e:
                print(f"❌ Errore nel test: {e}")
        
        # 8. Riepilogo finale
        print(f"\n📋 RIEPILOGO FINALE:")
        
        all_ai = CellAnnotation.query.filter_by(is_ai_generated=True).all()
        pending = [ann for ann in all_ai if ann.status == 'pending_review']
        active = [ann for ann in all_ai if ann.status == 'active']
        rejected = [ann for ann in all_ai if ann.status == 'rejected']
        
        print(f"   - Totali AI: {len(all_ai)}")
        print(f"   - Pending: {len(pending)}")
        print(f"   - Active: {len(active)}")
        print(f"   - Rejected: {len(rejected)}")

if __name__ == "__main__":
    test_ai_review_system()
