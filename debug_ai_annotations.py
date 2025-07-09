#!/usr/bin/env python3
"""
Script per debuggare le annotazioni AI nella pagina di revisione
"""

from app import create_app
from models import db, CellAnnotation, TextCell
from sqlalchemy import text

def debug_ai_annotations():
    app = create_app()
    
    with app.app_context():
        print("=== DEBUG ANNOTAZIONI AI ===\n")
        
        # Controlla tabelle esistenti
        print("1. Controllo struttura database...")
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%annotation%'"))
        tables = result.fetchall()
        print(f"Tabelle annotazioni trovate: {[t[0] for t in tables]}")
        
        # Controlla annotazioni AI
        print("\n2. Controllo annotazioni AI...")
        try:
            # Prova prima CellAnnotation con is_ai_generated
            ai_annotations = CellAnnotation.query.filter(
                CellAnnotation.is_ai_generated == True
            ).all()
            print(f"Annotazioni AI (CellAnnotation): {len(ai_annotations)}")
            
            for ann in ai_annotations[:5]:
                print(f"  - ID: {ann.id}, Status: {getattr(ann, 'status', 'N/A')}, Label: {ann.label.name if ann.label else 'N/A'}")
                
        except Exception as e:
            print(f"Errore con CellAnnotation: {e}")
        
        # Non c'è una tabella AIAnnotation separata
        print("\nLe annotazioni AI sono memorizzate in CellAnnotation con is_ai_generated=True")
        
        # Controlla colonne di CellAnnotation
        print("\n3. Controllo struttura CellAnnotation...")
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(cell_annotation)"))
        columns = result.fetchall()
        print("Colonne in cell_annotation:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Controlla tutte le annotazioni
        print("\n4. Controllo tutte le annotazioni...")
        all_annotations = CellAnnotation.query.all()
        print(f"Totale annotazioni: {len(all_annotations)}")
        
        # Controlla se ci sono annotazioni con provider
        ai_with_provider = CellAnnotation.query.filter(
            CellAnnotation.provider.isnot(None)
        ).all()
        print(f"Annotazioni con provider AI: {len(ai_with_provider)}")
        
        for ann in ai_with_provider[:3]:
            print(f"  - ID: {ann.id}, Provider: {ann.provider}, Model: {getattr(ann, 'model', 'N/A')}")

if __name__ == '__main__':
    debug_ai_annotations()
