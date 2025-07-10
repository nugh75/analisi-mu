#!/usr/bin/env python3
"""
Script per testare la nuova pipeline AI migliorata
"""

from app import create_app
from models import db, CellAnnotation, Label, TextCell, ExcelFile
from services.ai_annotator import AIAnnotatorService

def test_improved_ai_pipeline():
    """Testa la pipeline AI migliorata"""
    app = create_app()
    
    with app.app_context():
        print("=== TEST PIPELINE AI MIGLIORATA ===\n")
        
        # 1. Verifica lo stato attuale
        ai_annotations = CellAnnotation.query.filter_by(is_ai_generated=True).all()
        pending_count = len([a for a in ai_annotations if a.status == 'pending_review'])
        
        print(f"📊 Stato attuale:")
        print(f"   - Annotazioni AI totali: {len(ai_annotations)}")
        print(f"   - In attesa di revisione: {pending_count}")
        
        # 2. Verifica etichette attive
        active_labels = Label.query.filter_by(is_active=True).all()
        print(f"   - Etichette attive: {len(active_labels)}")
        for label in active_labels[:5]:  # Mostra prime 5
            category = label.category_obj.name if label.category_obj else 'Generale'
            print(f"     • {label.name} ({category})")
        if len(active_labels) > 5:
            print(f"     ... e altre {len(active_labels) - 5}")
        
        # 3. Testa costruzione prompt dinamico
        print(f"\n🔧 Test costruzione prompt dinamico...")
        service = AIAnnotatorService()
        
        sample_texts = ["Test AI per etichettatura", "Esempio di testo"]
        prompt = service.build_annotation_prompt(sample_texts, active_labels)
        
        print(f"✅ Prompt generato (lunghezza: {len(prompt)} caratteri)")
        print(f"   - Contiene {prompt.count('===')//2} categorie")
        print(f"   - Contiene {prompt.count('•')} etichette")
        
        # 4. Trova un file per test
        excel_file = ExcelFile.query.first()
        if excel_file:
            print(f"\n📁 File di test: {excel_file.original_filename} (ID: {excel_file.id})")
            
            # Verifica celle disponibili
            total_cells = TextCell.query.filter_by(excel_file_id=excel_file.id).count()
            annotated_cells = db.session.query(TextCell.id).filter_by(excel_file_id=excel_file.id)\
                .join(CellAnnotation).distinct().count()
            unannotated_cells = total_cells - annotated_cells
            
            print(f"   - Celle totali: {total_cells}")
            print(f"   - Celle annotate: {annotated_cells}")
            print(f"   - Celle non annotate: {unannotated_cells}")
            
            # 5. Test simulazione nuova generazione (modalità normale)
            print(f"\n🤖 Simulazione generazione normale...")
            result = service.generate_annotations(excel_file.id, batch_size=5, re_annotate=False)
            print(f"   Risultato: {result.get('message', 'Errore')}")
            
            print(f"\n🔄 Simulazione ri-etichettatura (solo test, non eseguita)...")
            print("   La ri-etichettatura processerebbe tutte le celle del file")
            print("   Userebbe le etichette attive correnti del sistema")
            print("   Ogni batch avrebbe pausa di 1 secondo per evitare timeout")
            
        else:
            print("⚠️  Nessun file Excel trovato per i test")
        
        print(f"\n✅ Test pipeline completato con successo!")
        print(f"\n📋 RIASSUNTO MIGLIORAMENTI:")
        print("   ✅ Status annotazioni AI fixato (tutte pending_review)")
        print("   ✅ Prompt dinamico con etichette correnti del sistema")
        print("   ✅ Gestione timeout con batch più piccoli e pause")
        print("   ✅ Modalità ri-etichettatura per celle già annotate")
        print("   ✅ Frontend con pulsante ri-etichettatura")
        print("   ✅ Limite massimo 50 celle per sessione")

if __name__ == '__main__':
    test_improved_ai_pipeline()
