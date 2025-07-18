#!/usr/bin/env python3
"""
Migrazione per aggiungere i campi di classificazione delle domande al modello TextCell
"""

import os
import sys

# Aggiungi il percorso dell'applicazione
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, TextCell
from sqlalchemy import text

def migrate_add_question_classification():
    """
    Aggiunge i campi per la classificazione automatica delle domande
    """
    app = create_app()
    
    with app.app_context():
        print("=== MIGRAZIONE: Aggiunta classificazione domande ===\n")
        
        # Controlla se i campi esistono già
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('text_cell')]
        
        new_fields = ['question_type', 'is_annotatable', 'classification_confidence']
        missing_fields = [field for field in new_fields if field not in columns]
        
        if not missing_fields:
            print("✓ Tutti i campi di classificazione esistono già")
            return
        
        print(f"Aggiungendo campi mancanti: {missing_fields}")
        
        try:
            # Aggiunge le colonne mancanti usando text()
            with db.engine.connect() as connection:
                for field in missing_fields:
                    if field == 'question_type':
                        connection.execute(
                            text("ALTER TABLE text_cell ADD COLUMN question_type VARCHAR(20)")
                        )
                        connection.commit()
                        print("✓ Aggiunta colonna 'question_type'")
                    
                    elif field == 'is_annotatable':
                        connection.execute(
                            text("ALTER TABLE text_cell ADD COLUMN is_annotatable BOOLEAN DEFAULT 1")
                        )
                        connection.commit()
                        print("✓ Aggiunta colonna 'is_annotatable'")
                    
                    elif field == 'classification_confidence':
                        connection.execute(
                            text("ALTER TABLE text_cell ADD COLUMN classification_confidence FLOAT")
                        )
                        connection.commit()
                        print("✓ Aggiunta colonna 'classification_confidence'")
            
            print("\n✓ Migrazione completata con successo!")
            
            # Statistiche
            total_cells = TextCell.query.count()
            print(f"\nTotale celle nel database: {total_cells}")
            
            if total_cells > 0:
                print("\nSuggerimento: Esegui la classificazione automatica con:")
                print("python -c \"from services.question_filter import QuestionFilterService; QuestionFilterService().reclassify_all_cells()\"")
        
        except Exception as e:
            print(f"✗ Errore durante la migrazione: {e}")
            raise

if __name__ == '__main__':
    migrate_add_question_classification()
