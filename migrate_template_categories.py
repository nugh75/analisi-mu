#!/usr/bin/env python3
"""
Migrazione per aggiungere il campo category alla tabella ai_prompt_template
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIPromptTemplate
from sqlalchemy import text

def add_category_column():
    """Aggiunge la colonna category alla tabella ai_prompt_template se non esiste"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verifica se la colonna esiste già
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM pragma_table_info('ai_prompt_template') 
                WHERE name = 'category'
            """)).fetchone()
            
            if result[0] == 0:
                print("🔧 Aggiunta colonna 'category' alla tabella ai_prompt_template...")
                db.session.execute(text("""
                    ALTER TABLE ai_prompt_template 
                    ADD COLUMN category VARCHAR(100)
                """))
                
                # Aggiorna i template esistenti con categorie predefinite
                print("📝 Aggiornamento template esistenti con categorie...")
                
                # Mappa ID -> Categoria basata sui template hardcoded conosciuti
                category_mapping = {
                    1: 'Sentiment Analysis',
                    2: 'Usage Patterns', 
                    3: 'Benefits Analysis',
                    4: 'Ethical Concerns',
                    5: 'Educational Experience',
                    6: 'Future Perspectives'
                }
                
                for template_id, category in category_mapping.items():
                    db.session.execute(text("""
                        UPDATE ai_prompt_template 
                        SET category = :category 
                        WHERE id = :id
                    """), {"category": category, "id": template_id})
                
                db.session.commit()
                print("✅ Migrazione completata con successo!")
                
                # Mostra i template aggiornati
                templates = AIPromptTemplate.query.all()
                print(f"\n📊 Template nel database ({len(templates)}):")
                for t in templates:
                    status = "🟢" if t.is_active else "🔴"
                    category = t.category or "Nessuna categoria"
                    print(f"  {status} ID:{t.id} - {t.name} - {category}")
                    
            else:
                print("ℹ️  La colonna 'category' esiste già nella tabella")
                
                # Mostra comunque i template esistenti
                templates = AIPromptTemplate.query.all()
                print(f"\n📊 Template nel database ({len(templates)}):")
                for t in templates:
                    status = "🟢" if t.is_active else "🔴"
                    category = t.category or "Nessuna categoria"
                    print(f"  {status} ID:{t.id} - {t.name} - {category}")
                
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {str(e)}")
            db.session.rollback()
            return False
            
    return True

if __name__ == '__main__':
    print("🚀 Avvio migrazione template AI...")
    success = add_category_column()
    
    if success:
        print("\n🎉 Migrazione completata! Ora puoi utilizzare la gestione template AI.")
        print("📱 Accedi a: /admin/templates")
    else:
        print("\n💥 Migrazione fallita. Controlla i log per i dettagli.")
        sys.exit(1)
