#!/usr/bin/env python3
"""
Script per rimuovere il constraint UNIQUE da cell_annotation
e permettere multiple annotazioni della stessa etichetta sulla stessa cella
"""

import sqlite3
from app import create_app
from models import db
import os

def remove_unique_constraint():
    """Rimuove il constraint UNIQUE dalla tabella cell_annotation"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                # Se il percorso è relativo, aggiungi il percorso della cartella instance
                db_path = os.path.join(app.instance_path, db_path)
        else:
            db_path = db_uri.replace('sqlite:///', '')
        
        print(f"Connessione al database: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ File database non trovato: {db_path}")
            return
        
        # Backup del database
        backup_path = f"{db_path}.backup_before_constraint_removal"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✓ Backup creato: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Verifica il schema attuale
            cursor.execute("SELECT sql FROM sqlite_master WHERE name='cell_annotation'")
            current_schema = cursor.fetchone()[0]
            print(f"Schema attuale:\n{current_schema}")
            
            # Crea una nuova tabella senza il constraint UNIQUE
            cursor.execute("""
                CREATE TABLE cell_annotation_new (
                    id INTEGER PRIMARY KEY,
                    text_cell_id INTEGER NOT NULL,
                    label_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_ai_generated BOOLEAN DEFAULT 0,
                    ai_confidence REAL,
                    ai_model VARCHAR(100),
                    ai_provider VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'active',
                    reviewed_by INTEGER,
                    reviewed_at DATETIME,
                    FOREIGN KEY (text_cell_id) REFERENCES text_cell(id),
                    FOREIGN KEY (label_id) REFERENCES label(id),
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (reviewed_by) REFERENCES user(id)
                )
            """)
            print("✓ Nuova tabella creata senza constraint UNIQUE")
            
            # Copia i dati dalla vecchia tabella
            cursor.execute("""
                INSERT INTO cell_annotation_new 
                SELECT * FROM cell_annotation
            """)
            print("✓ Dati copiati nella nuova tabella")
            
            # Rimuovi la vecchia tabella
            cursor.execute("DROP TABLE cell_annotation")
            print("✓ Vecchia tabella rimossa")
            
            # Rinomina la nuova tabella
            cursor.execute("ALTER TABLE cell_annotation_new RENAME TO cell_annotation")
            print("✓ Nuova tabella rinominata")
            
            conn.commit()
            print("✓ Constraint UNIQUE rimosso con successo!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Errore: {e}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    remove_unique_constraint()
