#!/usr/bin/env python3
"""
Script per pulire direttamente i dati orfani dal database.
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Crea un backup del database"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup creato: {backup_path}")
    return backup_path

def clean_database():
    """Pulisce direttamente il database"""
    
    db_path = 'instance/analisi_mu.db'
    
    if not os.path.exists(db_path):
        print("Database non trovato!")
        return False
    
    backup_path = backup_database(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Inizio pulizia database...")
        
        # Disabilita temporaneamente i vincoli di chiave estera
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 1. Elimina le azioni di annotazione che fanno riferimento a etichette inesistenti
        print("Eliminazione azioni con etichette inesistenti...")
        cursor.execute("""
            DELETE FROM annotation_action 
            WHERE label_id NOT IN (SELECT id FROM label)
        """)
        deleted_actions = cursor.rowcount
        print(f"  Eliminate {deleted_actions} azioni con etichette inesistenti")
        
        # 2. Elimina le annotazioni che fanno riferimento a etichette inesistenti
        print("Eliminazione annotazioni con etichette inesistenti...")
        cursor.execute("""
            DELETE FROM cell_annotation 
            WHERE label_id NOT IN (SELECT id FROM label)
        """)
        deleted_annotations = cursor.rowcount
        print(f"  Eliminate {deleted_annotations} annotazioni con etichette inesistenti")
        
        # 3. Elimina le annotazioni di testo che fanno riferimento a etichette inesistenti
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='text_annotations'")
        if cursor.fetchone():
            print("Eliminazione annotazioni testo con etichette inesistenti...")
            cursor.execute("""
                DELETE FROM text_annotations 
                WHERE label_id NOT IN (SELECT id FROM label)
            """)
            deleted_text_annotations = cursor.rowcount
            print(f"  Eliminate {deleted_text_annotations} annotazioni testo con etichette inesistenti")
        
        # 4. Elimina le azioni che fanno riferimento a celle inesistenti
        print("Eliminazione azioni con celle inesistenti...")
        cursor.execute("""
            DELETE FROM annotation_action 
            WHERE text_cell_id NOT IN (SELECT id FROM text_cell)
        """)
        deleted_cell_actions = cursor.rowcount
        print(f"  Eliminate {deleted_cell_actions} azioni con celle inesistenti")
        
        # 5. Elimina le annotazioni che fanno riferimento a celle inesistenti
        print("Eliminazione annotazioni con celle inesistenti...")
        cursor.execute("""
            DELETE FROM cell_annotation 
            WHERE text_cell_id NOT IN (SELECT id FROM text_cell)
        """)
        deleted_cell_annotations = cursor.rowcount
        print(f"  Eliminate {deleted_cell_annotations} annotazioni con celle inesistenti")
        
        # 6. Aggiorna i riferimenti NULL dove necessario
        print("Aggiornamento riferimenti NULL...")
        cursor.execute("""
            UPDATE cell_annotation 
            SET reviewed_by = NULL 
            WHERE reviewed_by IS NOT NULL 
            AND reviewed_by NOT IN (SELECT id FROM user)
        """)
        updated_reviews = cursor.rowcount
        print(f"  Aggiornate {updated_reviews} revisioni con utenti inesistenti")
        
        cursor.execute("""
            UPDATE annotation_action 
            SET annotation_id = NULL 
            WHERE annotation_id IS NOT NULL 
            AND annotation_id NOT IN (SELECT id FROM cell_annotation)
        """)
        updated_annotation_refs = cursor.rowcount
        print(f"  Aggiornati {updated_annotation_refs} riferimenti a annotazioni inesistenti")
        
        cursor.execute("""
            UPDATE annotation_action 
            SET target_user_id = NULL 
            WHERE target_user_id IS NOT NULL 
            AND target_user_id NOT IN (SELECT id FROM user)
        """)
        updated_user_refs = cursor.rowcount
        print(f"  Aggiornati {updated_user_refs} riferimenti a utenti inesistenti")
        
        # Commit delle modifiche
        conn.commit()
        
        # Riabilita i vincoli di chiave estera
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Verifica l'integrità
        print("\nVerifica integrità finale...")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        
        if violations:
            print(f"ATTENZIONE: Ancora {len(violations)} violazioni:")
            for violation in violations[:5]:
                print(f"  {violation}")
            return False
        else:
            print("✓ Nessuna violazione di integrità trovata!")
            print("\n=== SUCCESSO ===")
            print("Il database è stato pulito con successo!")
            print("Ora dovresti essere in grado di eliminare i file Excel senza errori.")
            return True
        
    except Exception as e:
        print(f"Errore durante la pulizia: {e}")
        print(f"Ripristino del backup da {backup_path}")
        
        conn.rollback()
        conn.close()
        
        # Ripristina il backup
        shutil.copy2(backup_path, db_path)
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Script di pulizia database - Risoluzione vincoli chiave estera")
    print("=" * 65)
    
    success = clean_database()
    
    if success:
        print("\n🎉 OPERAZIONE COMPLETATA CON SUCCESSO!")
        print("Il problema di eliminazione dei file Excel dovrebbe essere risolto.")
    else:
        print("\n❌ OPERAZIONE FALLITA!")
        print("Il database è stato ripristinato al backup.")
