#!/usr/bin/env python3
"""
Script completo per riparare i vincoli di chiave estera.
Questo script pulisce tutti i riferimenti orfani nel database.
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Crea un backup del database prima della modifica"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup creato: {backup_path}")
    return backup_path

def fix_foreign_keys():
    """Risolve il problema dei vincoli di chiave estera"""
    
    # Path al database
    db_path = 'instance/analisi_mu.db'
    
    if not os.path.exists(db_path):
        print("Database non trovato!")
        return False
    
    # Crea backup
    backup_path = backup_database(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Inizio riparazione completa...")
        
        # Disabilita temporaneamente i vincoli di chiave estera
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 1. Elimina le annotazioni che fanno riferimento a celle inesistenti
        print("Controllo e pulizia annotazioni orfane...")
        
        cursor.execute("""
            DELETE FROM cell_annotation 
            WHERE text_cell_id NOT IN (SELECT id FROM text_cell)
        """)
        deleted_annotations = cursor.rowcount
        print(f"  Eliminate {deleted_annotations} annotazioni orfane")
        
        # 2. Elimina le azioni che fanno riferimento a celle inesistenti
        cursor.execute("""
            DELETE FROM annotation_action 
            WHERE text_cell_id NOT IN (SELECT id FROM text_cell)
        """)
        deleted_actions = cursor.rowcount
        print(f"  Eliminate {deleted_actions} azioni con celle inesistenti")
        
        # 3. Elimina le azioni che fanno riferimento a etichette inesistenti
        cursor.execute("""
            DELETE FROM annotation_action 
            WHERE label_id NOT IN (SELECT id FROM label)
        """)
        deleted_label_actions = cursor.rowcount
        print(f"  Eliminate {deleted_label_actions} azioni con etichette inesistenti")
        
        # 4. Elimina le azioni che fanno riferimento a utenti inesistenti nel campo performed_by
        cursor.execute("""
            DELETE FROM annotation_action 
            WHERE performed_by NOT IN (SELECT id FROM user)
        """)
        deleted_user_actions = cursor.rowcount
        print(f"  Eliminate {deleted_user_actions} azioni con utenti inesistenti")
        
        # 5. Rimuovi riferimenti a utenti inesistenti (imposta NULL dove possibile)
        cursor.execute("""
            UPDATE cell_annotation 
            SET reviewed_by = NULL 
            WHERE reviewed_by IS NOT NULL 
            AND reviewed_by NOT IN (SELECT id FROM user)
        """)
        updated_reviews = cursor.rowcount
        print(f"  Aggiornate {updated_reviews} revisioni con utenti inesistenti")
        
        # 6. Rimuovi riferimenti a annotazioni inesistenti
        cursor.execute("""
            UPDATE annotation_action 
            SET annotation_id = NULL 
            WHERE annotation_id IS NOT NULL 
            AND annotation_id NOT IN (SELECT id FROM cell_annotation)
        """)
        updated_actions = cursor.rowcount
        print(f"  Aggiornate {updated_actions} azioni con annotazioni inesistenti")
        
        # 7. Rimuovi riferimenti a utenti target inesistenti
        cursor.execute("""
            UPDATE annotation_action 
            SET target_user_id = NULL 
            WHERE target_user_id IS NOT NULL 
            AND target_user_id NOT IN (SELECT id FROM user)
        """)
        updated_target_users = cursor.rowcount
        print(f"  Aggiornate {updated_target_users} azioni con utenti target inesistenti")
        
        # 8. Aggiorna il campo uploaded_by per permettere NULL
        cursor.execute("""
            UPDATE excel_file 
            SET uploaded_by = NULL 
            WHERE uploaded_by IS NOT NULL 
            AND uploaded_by NOT IN (SELECT id FROM user)
        """)
        updated_files = cursor.rowcount
        print(f"  Aggiornati {updated_files} file con utenti inesistenti")
        
        # 9. Pulisci annotazioni delle celle con etichette inesistenti
        cursor.execute("""
            DELETE FROM cell_annotation 
            WHERE label_id NOT IN (SELECT id FROM label)
        """)
        deleted_cell_label_annotations = cursor.rowcount
        print(f"  Eliminate {deleted_cell_label_annotations} annotazioni di celle con etichette inesistenti")
        
        # 10. Pulisci annotazioni delle celle con utenti inesistenti
        cursor.execute("""
            DELETE FROM cell_annotation 
            WHERE user_id NOT IN (SELECT id FROM user)
        """)
        deleted_cell_user_annotations = cursor.rowcount
        print(f"  Eliminate {deleted_cell_user_annotations} annotazioni di celle con utenti inesistenti")
        
        # 11. Pulisci annotazioni di testo con documenti inesistenti (se esistono)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='text_annotations'")
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM text_annotations 
                WHERE document_id NOT IN (SELECT id FROM text_documents)
            """)
            deleted_text_doc_annotations = cursor.rowcount
            print(f"  Eliminate {deleted_text_doc_annotations} annotazioni di testo con documenti inesistenti")
            
            cursor.execute("""
                DELETE FROM text_annotations 
                WHERE label_id NOT IN (SELECT id FROM label)
            """)
            deleted_text_label_annotations = cursor.rowcount
            print(f"  Eliminate {deleted_text_label_annotations} annotazioni di testo con etichette inesistenti")
            
            cursor.execute("""
                DELETE FROM text_annotations 
                WHERE user_id NOT IN (SELECT id FROM user)
            """)
            deleted_text_user_annotations = cursor.rowcount
            print(f"  Eliminate {deleted_text_user_annotations} annotazioni di testo con utenti inesistenti")
            
            cursor.execute("""
                UPDATE text_annotations 
                SET reviewed_by = NULL 
                WHERE reviewed_by IS NOT NULL 
                AND reviewed_by NOT IN (SELECT id FROM user)
            """)
            updated_text_reviews = cursor.rowcount
            print(f"  Aggiornate {updated_text_reviews} revisioni di testo con utenti inesistenti")
        
        # 12. Pulisci documenti di testo con utenti inesistenti (se esistono)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='text_documents'")
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM text_documents 
                WHERE user_id NOT IN (SELECT id FROM user)
            """)
            deleted_text_docs = cursor.rowcount
            print(f"  Eliminati {deleted_text_docs} documenti di testo con utenti inesistenti")
        
        # Riabilita i vincoli di chiave estera
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Verifica l'integrità
        print("Verifica integrità finale...")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        
        if violations:
            print(f"ATTENZIONE: Trovate ancora {len(violations)} violazioni di integrità:")
            for violation in violations[:10]:  # Mostra solo le prime 10
                print(f"  {violation}")
            return False
        
        conn.commit()
        print("Riparazione completata con successo!")
        print("Il database ora dovrebbe permettere l'eliminazione dei file Excel.")
        return True
        
    except Exception as e:
        print(f"Errore durante la riparazione: {e}")
        print(f"Ripristino del backup da {backup_path}")
        
        conn.rollback()
        conn.close()
        
        # Ripristina il backup
        shutil.copy2(backup_path, db_path)
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def test_delete_functionality():
    """Testa se l'eliminazione funziona ora"""
    try:
        from app import create_app
        from models import db, ExcelFile
        
        app = create_app()
        with app.app_context():
            # Conta i file prima
            files_before = ExcelFile.query.count()
            print(f"File Excel nel database: {files_before}")
            
            if files_before > 0:
                print("Test: La funzionalità di eliminazione dovrebbe ora funzionare.")
                print("Prova a eliminare un file dall'interfaccia web.")
            
    except Exception as e:
        print(f"Non è stato possibile testare: {e}")

if __name__ == "__main__":
    print("Script per riparare tutti i vincoli di chiave estera")
    print("=" * 60)
    
    if fix_foreign_keys():
        print("\nRiparazione completata!")
        test_delete_functionality()
    else:
        print("\nRiparazione fallita!")
