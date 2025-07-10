#!/usr/bin/env python3
"""
Script per aggiungere la tabella AnnotationAction al database esistente.
"""

from app import create_app
from models import db, AnnotationAction

def migrate_database():
    """Crea la nuova tabella AnnotationAction"""
    app = create_app()
    
    with app.app_context():
        print("Creazione tabella AnnotationAction...")
        
        try:
            # Crea solo la nuova tabella
            AnnotationAction.__table__.create(db.engine, checkfirst=True)
            print("✓ Tabella AnnotationAction creata con successo!")
            
        except Exception as e:
            print(f"❌ Errore durante la creazione della tabella: {e}")
            return False
            
        return True

if __name__ == '__main__':
    success = migrate_database()
    if success:
        print("Migrazione completata con successo!")
    else:
        print("Migrazione fallita!")
