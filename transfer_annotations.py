#!/usr/bin/env python3
"""
Script per trasferire le annotazioni dal database di sviluppo a quello di produzione
"""

import sqlite3
import sys
from datetime import datetime

def transfer_annotations():
    """Trasferisce le annotazioni dal database dev a quello di produzione"""
    
    # Percorsi dei database
    dev_db = 'instance_dev/analisi_mu_dev.db'
    prod_db = 'instance/analisi_mu.db'
    
    try:
        # Connessione ai database
        dev_conn = sqlite3.connect(dev_db)
        prod_conn = sqlite3.connect(prod_db)
        
        dev_cursor = dev_conn.cursor()
        prod_cursor = prod_conn.cursor()
        
        print("🔍 Analisi database di sviluppo...")
        
        # Controlla quante annotazioni ci sono nel dev
        dev_cursor.execute("SELECT COUNT(*) FROM cell_annotation")
        dev_annotations = dev_cursor.fetchone()[0]
        print(f"📊 Annotazioni nel database dev: {dev_annotations}")
        
        # Controlla quante annotazioni ci sono nel prod
        prod_cursor.execute("SELECT COUNT(*) FROM cell_annotation")
        prod_annotations = prod_cursor.fetchone()[0]
        print(f"📊 Annotazioni nel database prod (prima): {prod_annotations}")
        
        if dev_annotations == 0:
            print("⚠️  Nessuna annotazione trovata nel database di sviluppo")
            return
        
        # Ottieni tutte le annotazioni dal database dev
        dev_cursor.execute("""
            SELECT text_cell_id, label_id, created_at, updated_at, user_id, status
            FROM cell_annotation
        """)
        annotations = dev_cursor.fetchall()
        
        print(f"📦 Trasferimento di {len(annotations)} annotazioni...")
        
        # Inserisci le annotazioni nel database di produzione
        # Prima cancella eventuali annotazioni esistenti per evitare duplicati
        prod_cursor.execute("DELETE FROM cell_annotation")
        
        # Inserisci le nuove annotazioni
        for annotation in annotations:
            try:
                prod_cursor.execute("""
                    INSERT INTO cell_annotation 
                    (text_cell_id, label_id, created_at, updated_at, user_id, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, annotation)
            except sqlite3.IntegrityError as e:
                print(f"⚠️  Errore inserimento annotazione: {e}")
                continue
        
        # Commit delle modifiche
        prod_conn.commit()
        
        # Verifica finale
        prod_cursor.execute("SELECT COUNT(*) FROM cell_annotation")
        final_annotations = prod_cursor.fetchone()[0]
        print(f"✅ Annotazioni nel database prod (dopo): {final_annotations}")
        
        # Trasferisci anche le etichette se necessario
        print("\n🏷️  Verifica etichette...")
        
        dev_cursor.execute("SELECT COUNT(*) FROM label")
        dev_labels = dev_cursor.fetchone()[0]
        
        prod_cursor.execute("SELECT COUNT(*) FROM label")
        prod_labels = prod_cursor.fetchone()[0]
        
        print(f"📊 Etichette dev: {dev_labels}, prod: {prod_labels}")
        
        if dev_labels > prod_labels:
            print("🔄 Trasferimento etichette...")
            
            # Ottieni tutte le etichette dal dev
            dev_cursor.execute("SELECT id, name, description, category_id, created_at FROM label")
            labels = dev_cursor.fetchall()
            
            # Cancella e reinserisci le etichette
            prod_cursor.execute("DELETE FROM label")
            
            for label in labels:
                try:
                    prod_cursor.execute("""
                        INSERT INTO label (id, name, description, category_id, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, label)
                except sqlite3.IntegrityError as e:
                    print(f"⚠️  Errore inserimento etichetta: {e}")
                    continue
            
            prod_conn.commit()
            
            prod_cursor.execute("SELECT COUNT(*) FROM label")
            final_labels = prod_cursor.fetchone()[0]
            print(f"✅ Etichette trasferite: {final_labels}")
        
        print(f"\n🎉 Trasferimento completato alle {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Errore durante il trasferimento: {e}")
        return False
    
    finally:
        if 'dev_conn' in locals():
            dev_conn.close()
        if 'prod_conn' in locals():
            prod_conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Avvio trasferimento annotazioni...")
    success = transfer_annotations()
    if success:
        print("✅ Trasferimento completato con successo!")
    else:
        print("❌ Trasferimento fallito!")
        sys.exit(1)
