#!/usr/bin/env python3
"""
Script per aggiungere il campo category alla tabella ai_prompt_template
"""

from app import create_app, db
from models import AIPromptTemplate
from sqlalchemy import text

def migrate_add_category():
    """Aggiunge il campo category alla tabella ai_prompt_template"""
    app = create_app()
    
    with app.app_context():
        try:
            # Controlla se la colonna esiste già
            result = db.session.execute(text("""
                PRAGMA table_info(ai_prompt_template);
            """)).fetchall()
            
            has_category = any(col[1] == 'category' for col in result)
            
            if has_category:
                print("✅ Campo 'category' già presente nella tabella ai_prompt_template")
                return True
            
            # Aggiungi la colonna category
            print("📝 Aggiunta colonna 'category' alla tabella ai_prompt_template...")
            db.session.execute(text("""
                ALTER TABLE ai_prompt_template 
                ADD COLUMN category VARCHAR(100) NOT NULL DEFAULT 'Generale';
            """))
            
            # Aggiorna i record esistenti con categorie appropriate
            print("📝 Aggiornamento dei record esistenti...")
            
            # Template per commenti
            db.session.execute(text("""
                UPDATE ai_prompt_template 
                SET category = 'Commenti'
                WHERE name LIKE '%comment%' OR name LIKE '%commento%'
                   OR description LIKE '%comment%' OR description LIKE '%commento%';
            """))
            
            # Template per analisi generale
            db.session.execute(text("""
                UPDATE ai_prompt_template 
                SET category = 'Analisi Generale'
                WHERE name LIKE '%general%' OR name LIKE '%generale%'
                   OR name LIKE '%standard%' OR name LIKE '%base%';
            """))
            
            # Template per sentimenti/emozioni
            db.session.execute(text("""
                UPDATE ai_prompt_template 
                SET category = 'Sentimenti'
                WHERE name LIKE '%sentiment%' OR name LIKE '%emotion%' 
                   OR name LIKE '%sentimento%' OR name LIKE '%emozione%';
            """))
            
            # Template per competenze
            db.session.execute(text("""
                UPDATE ai_prompt_template 
                SET category = 'Competenze'
                WHERE name LIKE '%skill%' OR name LIKE '%competenz%' 
                   OR name LIKE '%abilit%';
            """))
            
            db.session.commit()
            print("✅ Migrazione completata con successo!")
            
            # Mostra i risultati
            templates = AIPromptTemplate.query.all()
            print(f"\n📊 Template trovati ({len(templates)}):")
            for template in templates:
                print(f"   - {template.name} [{template.category}]")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 Avvio migrazione campo category per ai_prompt_template...")
    success = migrate_add_category()
    
    if success:
        print("\n🎉 Migrazione completata con successo!")
    else:
        print("\n💥 Migrazione fallita!")
