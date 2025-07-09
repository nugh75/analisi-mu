#!/usr/bin/env python3
"""
Script per migrare il database esistente aggiungendo le nuove colonne per le categorie
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migra il database esistente aggiungendo le colonne per le categorie"""
    db_path = 'instance/analisi_mu.db'
    
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return False
    
    # Backup del database
    backup_path = f'backups/analisi_mu_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    os.makedirs('backups', exist_ok=True)
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Backup creato: {backup_path}")
    except Exception as e:
        print(f"Errore nella creazione del backup: {e}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se la tabella category esiste
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='category';
        """)
        
        if not cursor.fetchone():
            print("Creazione tabella 'category'...")
            cursor.execute("""
                CREATE TABLE category (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    color VARCHAR(7) DEFAULT '#6c757d',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # Verifica se la colonna category_id esiste nella tabella label
        cursor.execute("PRAGMA table_info(label);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category_id' not in columns:
            print("Aggiunta colonna 'category_id' alla tabella 'label'...")
            cursor.execute("""
                ALTER TABLE label 
                ADD COLUMN category_id INTEGER 
                REFERENCES category(id);
            """)
        
        # Inserisci alcune categorie predefinite
        print("Inserimento categorie predefinite...")
        default_categories = [
            ('Emozioni', 'Sentimenti e stati d\'animo degli studenti', '#e74c3c'),
            ('Opinioni', 'Valutazioni e giudizi personali', '#3498db'),
            ('Strategie', 'Metodi e approcci di apprendimento', '#2ecc71'),
            ('Problemi', 'Difficoltà e criticità riscontrate', '#f39c12'),
            ('Soluzioni', 'Proposte e rimedi suggeriti', '#9b59b6'),
            ('Contenuti', 'Argomenti e materie di studio', '#1abc9c'),
            ('Competenze', 'Abilità e capacità sviluppate', '#34495e'),
            ('Motivazione', 'Interesse e spinta all\'apprendimento', '#e67e22')
        ]
        
        for name, description, color in default_categories:
            cursor.execute("""
                INSERT OR IGNORE INTO category (name, description, color) 
                VALUES (?, ?, ?);
            """, (name, description, color))
        
        # Migra le categorie esistenti dal campo 'category' delle etichette
        print("Migrazione categorie esistenti...")
        cursor.execute("""
            SELECT DISTINCT category FROM label 
            WHERE category IS NOT NULL AND category != '';
        """)
        
        existing_categories = cursor.fetchall()
        for (category_name,) in existing_categories:
            if category_name and category_name.strip():
                # Converti in Title Case usando Python invece di SQL
                clean_name = category_name.strip().title()
                cursor.execute("""
                    INSERT OR IGNORE INTO category (name, description, color) 
                    VALUES (?, ?, ?);
                """, (clean_name, f'Categoria migrata: {category_name}', '#6c757d'))
        
        # Aggiorna le etichette per usare category_id
        print("Aggiornamento riferimenti category_id...")
        
        # Prima ottieni tutte le etichette con categoria
        cursor.execute("""
            SELECT id, category FROM label 
            WHERE category IS NOT NULL AND category != '';
        """)
        
        labels_to_update = cursor.fetchall()
        
        for label_id, category_name in labels_to_update:
            if category_name and category_name.strip():
                clean_name = category_name.strip().title()
                
                # Trova l'ID della categoria corrispondente
                cursor.execute("""
                    SELECT id FROM category 
                    WHERE name = ? OR name = ?;
                """, (category_name.strip(), clean_name))
                
                category_result = cursor.fetchone()
                if category_result:
                    category_id = category_result[0]
                    
                    # Aggiorna l'etichetta
                    cursor.execute("""
                        UPDATE label 
                        SET category_id = ? 
                        WHERE id = ?;
                    """, (category_id, label_id))
        
        conn.commit()
        print("Migrazione completata con successo!")
        
        # Mostra statistiche
        cursor.execute("SELECT COUNT(*) FROM category;")
        cat_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM label WHERE category_id IS NOT NULL;")
        label_with_cat = cursor.fetchone()[0]
        
        print(f"Categorie create: {cat_count}")
        print(f"Etichette con categoria: {label_with_cat}")
        
        return True
        
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    if migrate_database():
        print("Migrazione completata. Ora puoi riavviare l'applicazione.")
    else:
        print("Migrazione fallita. Controlla i messaggi di errore.")
