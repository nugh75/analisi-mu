#!/usr/bin/env python3
"""
Script per migrare il database esistente con le nuove tabelle AI
"""

from app import create_app
from models import db, AIConfiguration, OpenRouterModel, OllamaModel, CellAnnotation, User
from sqlalchemy import text
import sys

def migrate_database():
    """Migra il database aggiungendo le nuove tabelle e colonne AI"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Inizio migrazione database per supporto AI...")
            
            # Crea le nuove tabelle
            print("📊 Creazione nuove tabelle...")
            db.create_all()
            
            # Aggiungi le colonne AI alla tabella cell_annotation se non esistono
            print("🔧 Aggiornamento tabella cell_annotation...")
            
            # Controlla se le colonne esistono già
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('cell_annotation')]
            
            ai_columns = [
                ('is_ai_generated', 'BOOLEAN DEFAULT FALSE'),
                ('ai_confidence', 'FLOAT'),
                ('ai_model', 'VARCHAR(100)'),
                ('ai_provider', 'VARCHAR(20)'),
                ('status', 'VARCHAR(20) DEFAULT "active"'),
                ('reviewed_by', 'INTEGER'),
                ('reviewed_at', 'DATETIME')
            ]
            
            for column_name, column_def in ai_columns:
                if column_name not in columns:
                    try:
                        # SQLite
                        db.session.execute(text(f'ALTER TABLE cell_annotation ADD COLUMN {column_name} {column_def}'))
                        print(f"✅ Aggiunta colonna {column_name}")
                    except Exception as e:
                        print(f"⚠️  Colonna {column_name} già esistente o errore: {e}")
            
            # Crea o aggiorna l'utente AI
            print("🤖 Configurazione utente AI...")
            ai_user = User.query.filter_by(username='ai_assistant').first()
            
            if not ai_user:
                ai_user = User(
                    username='ai_assistant',
                    email='ai@system.local',
                    role='annotatore'
                )
                ai_user.set_password('N/A')
                db.session.add(ai_user)
                print("✅ Utente AI creato")
            else:
                print("✅ Utente AI già esistente")
            
            # Popola modelli OpenRouter predefiniti
            print("🌐 Popolamento modelli OpenRouter...")
            
            from services.openrouter_client import KNOWN_FREE_MODELS, POPULAR_PAID_MODELS
            
            for model in KNOWN_FREE_MODELS:
                existing = OpenRouterModel.query.filter_by(model_id=model['id']).first()
                if not existing:
                    or_model = OpenRouterModel(
                        model_id=model['id'],
                        name=model['name'],
                        description=model['description'],
                        context_length=model['context_length'],
                        pricing_prompt=float(model['pricing']['prompt']),
                        pricing_completion=float(model['pricing']['completion']),
                        is_free=True
                    )
                    db.session.add(or_model)
            
            for model in POPULAR_PAID_MODELS:
                existing = OpenRouterModel.query.filter_by(model_id=model['id']).first()
                if not existing:
                    or_model = OpenRouterModel(
                        model_id=model['id'],
                        name=model['name'],
                        description=model['description'],
                        context_length=model['context_length'],
                        pricing_prompt=float(model['pricing']['prompt']),
                        pricing_completion=float(model['pricing']['completion']),
                        is_free=False
                    )
                    db.session.add(or_model)
            
            print("✅ Modelli OpenRouter popolati")
            
            # Crea una configurazione AI di esempio
            print("⚙️  Creazione configurazione AI di esempio...")
            
            example_config = AIConfiguration.query.first()
            if not example_config:
                example_config = AIConfiguration(
                    provider='ollama',
                    name='Configurazione Ollama di esempio',
                    ollama_url='http://192.168.12.14:11345',
                    ollama_model='llama3',
                    is_active=False,
                    max_tokens=1000,
                    temperature=0.7,
                    system_prompt='Sei un assistente specializzato nell\'etichettatura di testi educativi. Analizza ogni testo e assegna l\'etichetta più appropriata dalla lista fornita.'
                )
                db.session.add(example_config)
                print("✅ Configurazione AI di esempio creata")
            else:
                print("✅ Configurazione AI già esistente")
            
            # Commit delle modifiche
            db.session.commit()
            
            print("\n🎉 Migrazione completata con successo!")
            print("\n📋 Riepilogo modifiche:")
            print("   • Aggiunte tabelle: AIConfiguration, OpenRouterModel, OllamaModel")
            print("   • Aggiornata tabella: CellAnnotation (nuove colonne AI)")
            print("   • Creato utente AI: ai_assistant")
            print("   • Popolati modelli OpenRouter predefiniti")
            print("   • Creata configurazione AI di esempio")
            print("\n🔗 Prossimi passi:")
            print("   1. Vai su /admin/ai-config per configurare l'AI")
            print("   2. Testa la connessione con Ollama o OpenRouter")
            print("   3. Inizia ad usare l'etichettatura automatica!")
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {e}")
            db.session.rollback()
            return False
        
        return True

def verify_migration():
    """Verifica che la migrazione sia andata a buon fine"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🔍 Verifica migrazione...")
            
            # Controlla le tabelle
            tables = ['ai_configuration', 'openrouter_model', 'ollama_model']
            for table in tables:
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                    print(f"✅ Tabella {table}: {result} record")
                except Exception as e:
                    print(f"❌ Errore tabella {table}: {e}")
                    return False
            
            # Controlla l'utente AI
            ai_user = User.query.filter_by(username='ai_assistant').first()
            if ai_user:
                print(f"✅ Utente AI: {ai_user.username} (ID: {ai_user.id})")
            else:
                print("❌ Utente AI non trovato")
                return False
            
            # Controlla colonne AI in cell_annotation
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('cell_annotation')]
            ai_columns = ['is_ai_generated', 'ai_confidence', 'ai_model', 'ai_provider', 'status']
            
            for col in ai_columns:
                if col in columns:
                    print(f"✅ Colonna {col} presente in cell_annotation")
                else:
                    print(f"❌ Colonna {col} mancante in cell_annotation")
                    return False
            
            print("\n✅ Verifica completata con successo!")
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la verifica: {e}")
            return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_migration()
    else:
        if migrate_database():
            verify_migration()
        else:
            print("❌ Migrazione fallita")
            sys.exit(1)
