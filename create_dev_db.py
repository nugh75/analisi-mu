#!/usr/bin/env python3
"""
Script per creare un database di sviluppo locale con le tabelle del forum
"""

import os
import sys
import shutil
from pathlib import Path

# Aggiungi la directory del progetto al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa l'app
from app import create_app
from models import db

def create_dev_database():
    """Crea un database di sviluppo separato"""
    
    # Percorsi - usiamo la directory del progetto invece di instance
    original_db = 'instance/analisi_mu.db'
    dev_db = 'analisi_mu_dev.db'  # Nella directory root del progetto
    
    print("🔧 Creazione database di sviluppo...")
    
    # Copia il database esistente se non esiste già il dev
    if not os.path.exists(dev_db):
        if os.path.exists(original_db):
            print(f"📋 Copiando {original_db} -> {dev_db}")
            shutil.copy2(original_db, dev_db)
        else:
            print("⚠️  Database originale non trovato, creo un nuovo database")
    
    # Imposta permessi di scrittura
    if os.path.exists(dev_db):
        os.chmod(dev_db, 0o666)
        print(f"✅ Permessi di scrittura applicati a {dev_db}")
    
    # Configura l'app per usare il database di sviluppo
    os.environ['DATABASE_URL'] = f'sqlite:///{os.path.abspath(dev_db)}'
    
    # Crea l'app e le tabelle
    app = create_app()
    
    with app.app_context():
        # Crea tutte le tabelle (incluse quelle del forum)
        print("🏗️  Creando tabelle del forum...")
        db.create_all()
        print("✅ Tabelle create con successo!")
        
        # Verifica che le tabelle del forum esistano
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        forum_tables = ['forum_category', 'forum_post', 'forum_comment']
        for table in forum_tables:
            if table in tables:
                print(f"✅ Tabella {table} creata correttamente")
            else:
                print(f"❌ Tabella {table} NON trovata")
    
    print(f"\n🎉 Database di sviluppo creato: {os.path.abspath(dev_db)}")
    print("💡 Per usarlo, imposta: export DATABASE_URL=sqlite:///$(pwd)/analisi_mu_dev.db")
    
    return dev_db

if __name__ == '__main__':
    create_dev_database()
