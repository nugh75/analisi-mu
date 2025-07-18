#!/usr/bin/env python3
"""
Test per verificare che la visualizzazione delle categorie sia corretta.
"""

import os
import sys

# Aggiungi il percorso dell'applicazione
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Label, Category, db

def test_category_display():
    """
    Test per verificare che i labels mostrino correttamente le categorie
    """
    app = create_app()
    
    with app.app_context():
        print("=== Test Visualizzazione Categorie ===\n")
        
        # Query con eager loading
        labels = Label.query.options(db.joinedload(Label.category_obj)).all()
        
        print(f"Trovati {len(labels)} label totali\n")
        
        for label in labels:
            print(f"Label: {label.name}")
            print(f"  ID: {label.id}")
            print(f"  category_id: {label.category_id}")
            print(f"  category (property): {label.category}")
            
            # Test della relazione category_obj
            if label.category_obj:
                print(f"  category_obj.name: {label.category_obj.name}")
                print(f"  category_obj.id: {label.category_obj.id}")
            else:
                print(f"  category_obj: None")
            
            print(f"  is_active: {label.is_active}")
            print("---")
        
        print("\n=== Test Specifico per Categorie Esistenti ===")
        
        # Verifica le categorie esistenti
        categories = Category.query.all()
        print(f"Categorie esistenti: {len(categories)}")
        for cat in categories:
            print(f"  - {cat.name} (ID: {cat.id})")
        
        print("\n=== Test Label per Categoria ===")
        
        # Verifica i label per ogni categoria
        for category in categories:
            labels_in_cat = Label.query.options(db.joinedload(Label.category_obj))\
                                     .filter_by(category_id=category.id).all()
            
            print(f"\nCategoria '{category.name}' (ID: {category.id}):")
            print(f"  Label trovati: {len(labels_in_cat)}")
            
            for label in labels_in_cat:
                display_cat = label.category_obj.name if label.category_obj else 'Nessuna categoria'
                print(f"    - {label.name} -> '{display_cat}'")
        
        # Test label senza categoria
        uncategorized = Label.query.options(db.joinedload(Label.category_obj))\
                                  .filter(Label.category_id.is_(None)).all()
        
        print(f"\nLabel senza categoria: {len(uncategorized)}")
        for label in uncategorized:
            display_cat = label.category_obj.name if label.category_obj else 'Nessuna categoria'
            print(f"    - {label.name} -> '{display_cat}'")

if __name__ == '__main__':
    test_category_display()
