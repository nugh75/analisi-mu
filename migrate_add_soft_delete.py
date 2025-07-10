#!/usr/bin/env python3
"""
Script per aggiungere i campi is_active per il soft delete
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Aggiunge i campi is_active alle tabelle Category e Label"""
    db_path = os.path.join('instance', 'analisi_mu.db')
    
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return False
    
    # Crea un backup
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"Backup creato: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se la colonna is_active esiste già in Category
        cursor.execute("PRAGMA table_info(category)")
        category_columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in category_columns:
            print("Aggiunta colonna is_active alla tabella Category...")
            cursor.execute("ALTER TABLE category ADD COLUMN is_active BOOLEAN DEFAULT 1")
            cursor.execute("UPDATE category SET is_active = 1 WHERE is_active IS NULL")
            print("✓ Colonna is_active aggiunta alla tabella Category")
        else:
            print("✓ Colonna is_active già presente nella tabella Category")
        
        # Verifica se la colonna is_active esiste già in Label
        cursor.execute("PRAGMA table_info(label)")
        label_columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in label_columns:
            print("Aggiunta colonna is_active alla tabella Label...")
            cursor.execute("ALTER TABLE label ADD COLUMN is_active BOOLEAN DEFAULT 1")
            cursor.execute("UPDATE label SET is_active = 1 WHERE is_active IS NULL")
            print("✓ Colonna is_active aggiunta alla tabella Label")
        else:
            print("✓ Colonna is_active già presente nella tabella Label")
        
        conn.commit()
        print("✓ Migrazione completata con successo!")
        return True
        
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=== Migrazione Soft Delete ===")
    print("Aggiunta campi is_active a Category e Label...")
    
    if migrate_database():
        print("\n✓ Migrazione completata con successo!")
        print("Le categorie e le etichette ora supportano il soft delete.")
    else:
        print("\n✗ Migrazione fallita!")
