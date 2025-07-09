#!/usr/bin/env python3
"""
Script semplice per verificare le annotazioni AI
"""

import os
import sys

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, CellAnnotation, TextCell, ExcelFile

def check_ai_annotations():
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICA ANNOTAZIONI AI ===\n")
        
        # 1. Conta tutte le annotazioni
        all_annotations = CellAnnotation.query.all()
        print(f"1. Annotazioni totali: {len(all_annotations)}")
        
        # 2. Conta annotazioni AI
        ai_annotations = CellAnnotation.query.filter(
            CellAnnotation.is_ai_generated == True
        ).all()
        print(f"2. Annotazioni AI: {len(ai_annotations)}")
        
        # 3. Conta annotazioni AI per status
        if ai_annotations:
            pending = [ann for ann in ai_annotations if ann.status == 'pending_review']
            active = [ann for ann in ai_annotations if ann.status == 'active']
            rejected = [ann for ann in ai_annotations if ann.status == 'rejected']
            
            print(f"   - Pending review: {len(pending)}")
            print(f"   - Active: {len(active)}")
            print(f"   - Rejected: {len(rejected)}")
            
            # 4. Mostra dettagli delle prime 3 annotazioni AI
            print(f"\n3. Dettagli prime 3 annotazioni AI:")
            for i, ann in enumerate(ai_annotations[:3]):
                print(f"   {i+1}. ID: {ann.id}")
                print(f"      Status: {ann.status}")
                print(f"      Label: {ann.label.name if ann.label else 'None'}")
                print(f"      AI Model: {ann.ai_model}")
                print(f"      AI Provider: {ann.ai_provider}")
                print(f"      Confidence: {ann.ai_confidence}")
                print(f"      Text: {ann.text_cell.text_content[:100]}..." if ann.text_cell else "No text")
                print()
        
        # 5. Conta file con annotazioni AI
        files_with_ai = db.session.query(ExcelFile).join(TextCell).join(CellAnnotation).filter(
            CellAnnotation.is_ai_generated == True
        ).distinct().all()
        
        print(f"4. File con annotazioni AI: {len(files_with_ai)}")
        for file in files_with_ai:
            ai_count = CellAnnotation.query.join(TextCell).filter(
                TextCell.excel_file_id == file.id,
                CellAnnotation.is_ai_generated == True
            ).count()
            print(f"   - {file.original_filename}: {ai_count} annotazioni AI")

if __name__ == "__main__":
    check_ai_annotations()
