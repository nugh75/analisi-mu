#!/usr/bin/env python3
"""
Test per verificare la creazione di post nel forum
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Configura l'ambiente per il test"""
    # Imposta la path del database di sviluppo
    instance_dir = Path('/home/nugh75/Git/analisi-mu/instance_dev')
    dev_db_path = instance_dir / 'analisi_mu_dev.db'
    
    os.environ['DATABASE_URL'] = f'sqlite:///{dev_db_path}'
    os.environ['SECRET_KEY'] = 'dev-secret-key-for-development-only'
    os.environ['UPLOAD_FOLDER'] = 'uploads_dev'

def test_create_post():
    """Test di creazione post"""
    print("🔧 Configurazione ambiente...")
    setup_environment()
    
    print("📦 Importazione moduli...")
    # Importa i moduli dell'app
    from app import create_app
    from models import db, User, ForumCategory, ForumPost
    
    print("🚀 Creazione app...")
    app = create_app()
    
    print("🔗 Connessione al database...")
    
    with app.app_context():
        # Trova il primo utente
        user = User.query.first()
        if not user:
            print("❌ Nessun utente trovato nel database")
            return False
            
        print(f"👤 Utente trovato: {user.username} (ID: {user.id})")
        
        # Trova la prima categoria
        category = ForumCategory.query.first()
        if not category:
            print("❌ Nessuna categoria forum trovata")
            return False
            
        print(f"📁 Categoria trovata: {category.name} (ID: {category.id})")
        
        # Crea un post di test
        test_post = ForumPost(
            title="Test Post Automatico",
            content="Questo è un post di test creato automaticamente per verificare il funzionamento del sistema forum.",
            category_id=category.id,
            author_id=user.id
        )
        
        try:
            db.session.add(test_post)
            db.session.commit()
            print(f"✅ Post creato con successo! ID: {test_post.id}")
            
            # Verifica che sia stato salvato
            saved_post = ForumPost.query.get(test_post.id)
            if saved_post:
                print(f"✅ Post verificato nel database:")
                print(f"   - Titolo: {saved_post.title}")
                print(f"   - Autore: {saved_post.author.username}")
                print(f"   - Categoria: {saved_post.category.name}")
                return True
            else:
                print("❌ Post non trovato dopo la creazione")
                return False
                
        except Exception as e:
            print(f"❌ Errore durante la creazione del post: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = test_create_post()
    print(f"\n{'✅ Test completato con successo!' if success else '❌ Test fallito!'}")
    sys.exit(0 if success else 1)
