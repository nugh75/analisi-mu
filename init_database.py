#!/usr/bin/env python3
"""
Script per inizializzare/aggiornare il database con le nuove tabelle.
"""

from app import create_app
from models import db

def init_database():
    """Inizializza o aggiorna il database"""
    
    app = create_app()
    with app.app_context():
        print("Inizializzazione database...")
        
        try:
            # Crea tutte le tabelle (se non esistono)
            db.create_all()
            print("✅ Database inizializzato con successo!")
            
            # Verifica le tabelle create
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\nTabelle presenti nel database:")
            for table in tables:
                print(f"  • {table}")
                
            if 'category' in tables:
                print("\n✓ La tabella 'category' è stata creata correttamente")
            else:
                print("\n⚠️  La tabella 'category' non è stata trovata")
                
        except Exception as e:
            print(f"❌ Errore durante l'inizializzazione: {e}")

if __name__ == '__main__':
    init_database()
