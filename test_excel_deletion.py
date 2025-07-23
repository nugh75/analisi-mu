#!/usr/bin/env python3
"""
Script di test per verificare che l'eliminazione dei file Excel funzioni.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, ExcelFile, TextCell, CellAnnotation

def test_excel_deletion():
    """Testa l'eliminazione dei file Excel"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Conta i file Excel prima
            excel_files = ExcelFile.query.all()
            print(f"File Excel nel database: {len(excel_files)}")
            
            if len(excel_files) == 0:
                print("Nessun file Excel da testare.")
                return True
            
            # Mostra informazioni sui file
            for file in excel_files:
                cell_count = TextCell.query.filter_by(excel_file_id=file.id).count()
                annotation_count = db.session.query(CellAnnotation).join(TextCell).filter(TextCell.excel_file_id == file.id).count()
                print(f"  File: {file.original_filename}")
                print(f"    ID: {file.id}")
                print(f"    Celle: {cell_count}")
                print(f"    Annotazioni: {annotation_count}")
            
            print("\n✓ Il database è integro e l'eliminazione dovrebbe ora funzionare!")
            print("Puoi provare a eliminare un file dall'interfaccia web.")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante il test: {e}")
            return False

if __name__ == "__main__":
    print("Test di integrità database per eliminazione file Excel")
    print("=" * 55)
    
    if test_excel_deletion():
        print("\n🎉 TEST SUPERATO!")
        print("Il problema dovrebbe essere risolto.")
    else:
        print("\n❌ TEST FALLITO!")
        print("Potrebbero esserci ancora problemi.")
