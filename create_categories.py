#!/usr/bin/env python3
"""
Script per creare alcune categorie predefinite nel database.
Esegui questo script dopo aver avviato l'app per la prima volta con il nuovo modello Category.
"""

from app import create_app
from models import db, Category

def create_default_categories():
    """Crea le categorie predefinite"""
    
    default_categories = [
        {
            'name': 'Emozioni',
            'description': 'Sentimenti ed emozioni espresse dagli studenti',
            'color': '#e74c3c'  # Rosso
        },
        {
            'name': 'Opinioni',
            'description': 'Valutazioni, giudizi e opinioni personali',
            'color': '#3498db'  # Blu
        },
        {
            'name': 'Strategie',
            'description': 'Metodi, tecniche e strategie di apprendimento',
            'color': '#2ecc71'  # Verde
        },
        {
            'name': 'Problemi',
            'description': 'Difficoltà, ostacoli e criticità riscontrate',
            'color': '#f39c12'  # Arancione
        },
        {
            'name': 'Soluzioni',
            'description': 'Proposte, rimedi e soluzioni suggerite',
            'color': '#9b59b6'  # Viola
        },
        {
            'name': 'Competenze',
            'description': 'Abilità, competenze e conoscenze',
            'color': '#1abc9c'  # Turchese
        },
        {
            'name': 'Motivazione',
            'description': 'Aspetti motivazionali e atteggiamenti',
            'color': '#e67e22'  # Arancione scuro
        },
        {
            'name': 'Valutazione',
            'description': 'Aspetti valutativi e di feedback',
            'color': '#34495e'  # Grigio scuro
        }
    ]
    
    app = create_app()
    with app.app_context():
        print("Creazione categorie predefinite...")
        
        for cat_data in default_categories:
            # Verifica se la categoria esiste già
            existing = Category.query.filter_by(name=cat_data['name']).first()
            
            if not existing:
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    color=cat_data['color'],
                    is_active=True
                )
                db.session.add(category)
                print(f"✓ Creata categoria: {cat_data['name']}")
            else:
                print(f"- Categoria già esistente: {cat_data['name']}")
        
        try:
            db.session.commit()
            print("\n✅ Categorie create con successo!")
            
            # Mostra il riepilogo
            categories = Category.query.all()
            print(f"\nTotale categorie nel database: {len(categories)}")
            for cat in categories:
                print(f"  • {cat.name} ({cat.color})")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Errore durante la creazione delle categorie: {e}")

if __name__ == '__main__':
    create_default_categories()
