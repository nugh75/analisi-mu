#!/usr/bin/env python3
"""
Script di migrazione AI semplificato - senza dipendenze esterne
"""

import sqlite3
import os
import sys
from datetime import datetime

def run_migration():
    """Esegue la migrazione SQL diretta"""
    db_path = "instance/analisi_mu.db"
    
    if not os.path.exists(db_path):
        print("❌ Database non trovato in instance/analisi_mu.db")
        return False
    
    print(f"🔧 Migrazione database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Crea tabella ai_configuration
        print("📊 Creazione tabella ai_configuration...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                ollama_url VARCHAR(255),
                ollama_model VARCHAR(100),
                openrouter_api_key VARCHAR(255),
                openrouter_model VARCHAR(100),
                is_active BOOLEAN DEFAULT 0,
                max_tokens INTEGER DEFAULT 1000,
                temperature REAL DEFAULT 0.7,
                system_prompt TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Crea tabella openrouter_model
        print("📊 Creazione tabella openrouter_model...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS openrouter_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id VARCHAR(100) NOT NULL UNIQUE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                context_length INTEGER,
                pricing_prompt REAL,
                pricing_completion REAL,
                is_free BOOLEAN DEFAULT 0,
                is_available BOOLEAN DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Crea tabella ollama_model
        print("📊 Creazione tabella ollama_model...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ollama_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                tag VARCHAR(50) NOT NULL,
                size BIGINT,
                digest VARCHAR(100),
                modified_at DATETIME,
                is_pulled BOOLEAN DEFAULT 0,
                pull_progress REAL DEFAULT 0.0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, tag)
            )
        """)
        
        # 4. Crea tabella category se non esiste
        print("📊 Creazione tabella category...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                color VARCHAR(7) DEFAULT '#6c757d',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. Aggiorna tabella cell_annotation con colonne AI
        print("🔧 Aggiornamento tabella cell_annotation...")
        
        # Controlla se le colonne esistono già
        cursor.execute("PRAGMA table_info(cell_annotation)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        ai_columns = [
            ("is_ai_generated", "BOOLEAN DEFAULT 0"),
            ("ai_confidence", "REAL"),
            ("ai_model", "VARCHAR(100)"),
            ("ai_provider", "VARCHAR(20)"),
            ("status", "VARCHAR(20) DEFAULT 'active'"),
            ("reviewed_by", "INTEGER"),
            ("reviewed_at", "DATETIME")
        ]
        
        for column_name, column_def in ai_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE cell_annotation ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Aggiunta colonna {column_name}")
                except sqlite3.Error as e:
                    print(f"⚠️  Colonna {column_name}: {e}")
        
        # 6. Crea utente AI se non esiste
        print("🤖 Configurazione utente AI...")
        cursor.execute("SELECT id FROM user WHERE username = 'ai_assistant'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO user (username, email, password_hash, role, created_at, updated_at)
                VALUES ('ai_assistant', 'ai@system.local', 'N/A', 'annotatore', ?, ?)
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            print("✅ Utente AI creato")
        else:
            print("✅ Utente AI già esistente")
        
        # 7. Popola modelli OpenRouter di esempio
        print("🌐 Popolamento modelli OpenRouter...")
        
        free_models = [
            ("microsoft/phi-3-mini-128k-instruct:free", "Phi-3 Mini 128K (Free)", "Microsoft's small but capable model", 128000, 0, 0, 1),
            ("mistralai/mistral-7b-instruct:free", "Mistral 7B Instruct (Free)", "Mistral's 7B parameter model", 32768, 0, 0, 1),
            ("google/gemma-7b-it:free", "Gemma 7B Instruct (Free)", "Google's Gemma 7B model", 8192, 0, 0, 1)
        ]
        
        for model_data in free_models:
            cursor.execute("SELECT id FROM openrouter_model WHERE model_id = ?", (model_data[0],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO openrouter_model 
                    (model_id, name, description, context_length, pricing_prompt, pricing_completion, is_free)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, model_data)
        
        # 8. Crea configurazione AI di esempio
        print("⚙️  Creazione configurazione AI di esempio...")
        cursor.execute("SELECT id FROM ai_configuration LIMIT 1")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO ai_configuration 
                (provider, name, ollama_url, ollama_model, is_active, system_prompt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'ollama', 
                'Configurazione Ollama di esempio',
                'http://192.168.12.14:11345',
                'llama3',
                0,
                'Sei un assistente specializzato nell\'etichettatura di testi educativi.'
            ))
            print("✅ Configurazione AI di esempio creata")
        else:
            print("✅ Configurazione AI già esistente")
        
        # Commit delle modifiche
        conn.commit()
        print("💾 Modifiche salvate")
        
        # Verifica
        print("\n🔍 Verifica migrazione...")
        
        tables = ['ai_configuration', 'openrouter_model', 'ollama_model', 'category']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Tabella {table}: {count} record")
        
        cursor.execute("SELECT COUNT(*) FROM user WHERE username = 'ai_assistant'")
        ai_user_count = cursor.fetchone()[0]
        print(f"✅ Utente AI: {ai_user_count} trovato")
        
        conn.close()
        
        print("\n🎉 Migrazione completata con successo!")
        print("\n📋 Prossimi passi:")
        print("   1. Avvia l'applicazione: python app.py")
        print("   2. Vai su /admin/ai-config per configurare l'AI")
        print("   3. Testa le funzionalità AI nell'interfaccia web")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("🚀 MIGRAZIONE DATABASE AI - Versione Semplificata")
    print("=" * 55)
    
    if run_migration():
        print("\n✅ Migrazione completata!")
        sys.exit(0)
    else:
        print("\n❌ Migrazione fallita!")
        sys.exit(1)
