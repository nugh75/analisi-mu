#!/usr/bin/env python3
"""
Script per aggiornare il database con le nuove tabelle del sistema progetti
"""

import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Assicurati che il percorso del progetto sia nel PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Project, ProjectNote, ProjectCollaborator

def migrate_database():
    """Crea le nuove tabelle per il sistema progetti"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Creazione nuove tabelle per il sistema progetti...")
        
        # Crea le nuove tabelle
        try:
            # Crea solo le tabelle del sistema progetti se non esistono
            db.create_all()
            print("✅ Tabelle create con successo!")
            
            # Verifica che le tabelle siano state create
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['projects', 'project_notes', 'project_collaborators']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️  Tabelle mancanti: {missing_tables}")
            else:
                print("✅ Tutte le tabelle del sistema progetti sono presenti")
            
            # Crea un progetto di esempio per test (solo se non ce ne sono già)
            existing_projects = Project.query.count()
            if existing_projects == 0:
                print("\n📂 Creazione progetto di esempio...")
                
                # Trova il primo utente amministratore
                from models import User
                admin_user = User.query.filter_by(role='amministratore').first()
                
                if admin_user:
                    example_project = Project(
                        name="Progetto di Esempio",
                        description="Questo è un progetto di esempio per testare il nuovo sistema progetti. Puoi eliminarlo quando non serve più.",
                        project_type="mixed",
                        objectives="Testare le funzionalità del sistema progetti multi-file",
                        methodology="Test manuale delle funzionalità base",
                        visibility="private",
                        owner_id=admin_user.id,
                        last_activity=datetime.utcnow()
                    )
                    
                    example_project.tags_list = ["esempio", "test", "demo"]
                    
                    db.session.add(example_project)
                    db.session.commit()
                    
                    print(f"✅ Progetto di esempio creato (ID: {example_project.id})")
                else:
                    print("⚠️  Nessun utente amministratore trovato, progetto di esempio non creato")
            else:
                print(f"📂 Trovati {existing_projects} progetti esistenti")
            
            print("\n🎉 Migrazione completata con successo!")
            print("\nℹ️  Prossimi passi:")
            print("   1. Riavvia l'applicazione")
            print("   2. Vai su /projects per vedere la nuova sezione")
            print("   3. Crea il tuo primo progetto")
            print("   4. Carica file Excel e documenti di testo nel progetto")
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {str(e)}")
            db.session.rollback()
            raise
        
        return True

def verify_existing_data():
    """Verifica che i dati esistenti siano ancora integri"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Verifica integrità dati esistenti...")
        
        try:
            from models import User, ExcelFile, TextDocument, Label, Category
            
            # Conta i dati esistenti
            users_count = User.query.count()
            excel_files_count = ExcelFile.query.count()
            text_docs_count = TextDocument.query.count()
            labels_count = Label.query.count()
            categories_count = Category.query.count()
            
            print(f"   👥 Utenti: {users_count}")
            print(f"   📊 File Excel: {excel_files_count}")
            print(f"   📄 Documenti testo: {text_docs_count}")
            print(f"   🏷️  Etichette: {labels_count}")
            print(f"   📁 Categorie: {categories_count}")
            
            print("✅ Verifica completata - dati esistenti integri")
            
        except Exception as e:
            print(f"❌ Errore durante la verifica: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    print("🚀 Avvio migrazione database per sistema progetti")
    print("=" * 50)
    
    try:
        # Verifica dati esistenti
        if not verify_existing_data():
            print("❌ Verifica dati fallita, interrompo la migrazione")
            sys.exit(1)
        
        # Esegui migrazione
        if migrate_database():
            print("\n🎉 Migrazione completata con successo!")
            sys.exit(0)
        else:
            print("\n❌ Migrazione fallita")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Migrazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Errore critico: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
