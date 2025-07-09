#!/usr/bin/env python3
"""
Script semplificato per verificare le annotazioni AI
"""

import sqlite3
import os

def check_annotations():
    db_path = "/home/nugh75/Git/analisi-mu/instance/analisi_mu.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Conta tutte le annotazioni
        cursor.execute("SELECT COUNT(*) FROM cell_annotation")
        total = cursor.fetchone()[0]
        print(f"📊 Annotazioni totali: {total}")
        
        # 2. Conta annotazioni AI
        cursor.execute("SELECT COUNT(*) FROM cell_annotation WHERE is_ai_generated = 1")
        ai_total = cursor.fetchone()[0]
        print(f"🤖 Annotazioni AI totali: {ai_total}")
        
        # 3. Conta annotazioni AI pending
        cursor.execute("SELECT COUNT(*) FROM cell_annotation WHERE is_ai_generated = 1 AND status = 'pending_review'")
        ai_pending = cursor.fetchone()[0]
        print(f"⏳ Annotazioni AI pending: {ai_pending}")
        
        # 4. Verifica per file specifico
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cell_annotation ca 
            JOIN text_cell tc ON ca.text_cell_id = tc.id 
            WHERE ca.is_ai_generated = 1 
            AND ca.status = 'pending_review' 
            AND tc.excel_file_id = 1
        """)
        file_pending = cursor.fetchone()[0]
        print(f"📁 Annotazioni AI pending per file 1: {file_pending}")
        
        # 5. Mostra dettagli delle prime 3 annotazioni AI pending
        if ai_pending > 0:
            cursor.execute("""
                SELECT ca.id, ca.status, l.name as label_name, ca.ai_confidence, tc.excel_file_id
                FROM cell_annotation ca
                LEFT JOIN label l ON ca.label_id = l.id
                LEFT JOIN text_cell tc ON ca.text_cell_id = tc.id
                WHERE ca.is_ai_generated = 1 AND ca.status = 'pending_review'
                LIMIT 3
            """)
            
            print("\n🔍 Prime 3 annotazioni AI pending:")
            for row in cursor.fetchall():
                print(f"  - ID: {row[0]}, Status: {row[1]}, Label: {row[2]}, Confidence: {row[3]}, File: {row[4]}")
        
        # 6. Verifica file Excel
        cursor.execute("SELECT id, original_filename FROM excel_file")
        files = cursor.fetchall()
        print(f"\n📂 File Excel disponibili: {len(files)}")
        for file_id, filename in files:
            print(f"  - ID: {file_id}, Nome: {filename}")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_annotations()
