"""
Script per aggiungere le tabelle del forum al database
"""

from models import db, ForumCategory, ForumPost, ForumComment
from flask import current_app

def create_forum_tables():
    """Crea le tabelle per il forum se non esistono"""
    with current_app.app_context():
        print("🔧 Creazione tabelle del forum...")
        
        # Crea tutte le tabelle definite nei modelli
        db.create_all()
        
        print("✅ Tabelle del forum create con successo!")
        print("📋 Tabelle create:")
        print("   - forum_category: Categorie del forum")
        print("   - forum_post: Post delle discussioni")
        print("   - forum_comment: Commenti ai post")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    
    with app.app_context():
        create_forum_tables()
