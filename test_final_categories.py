#!/usr/bin/env python3
"""
Test finale per verificare che le categorie siano visualizzate correttamente
in tutti i contesti dopo le correzioni di eager loading
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Label, Category, db

app = create_app()

with app.app_context():
    print("=== TEST FINALE: CATEGORIE SPECIFICHE ===\n")
    
    # Test specifico per le categorie che avevano problemi
    test_categories = ['Miglioramenti Studenti', 'Miglioramenti docente']
    
    for cat_name in test_categories:
        category = Category.query.filter_by(name=cat_name).first()
        if category:
            print(f"Categoria: {category.name} (ID: {category.id})")
            
            # Test con eager loading
            labels = Label.query.options(db.joinedload(Label.category_obj))\
                              .filter_by(category_id=category.id).all()
            
            print(f"  Label trovati: {len(labels)}")
            
            for label in labels:
                display_category = label.category_obj.name if label.category_obj else 'ERROR: Nessuna categoria'
                status = "✓" if display_category == cat_name else "✗"
                print(f"    {status} {label.name} -> '{display_category}'")
            
            print()
    
    print("=== TEST FILTRO 'NESSUNA CATEGORIA' ===\n")
    
    # Test per etichette senza categoria
    uncategorized = Label.query.options(db.joinedload(Label.category_obj))\
                              .filter(Label.category_id.is_(None)).limit(5).all()
    
    print(f"Etichette senza categoria (prime 5): {len(uncategorized)}")
    
    for label in uncategorized:
        display_category = label.category_obj.name if label.category_obj else 'Nessuna categoria'
        status = "✓" if display_category == 'Nessuna categoria' else "✗"
        print(f"  {status} {label.name} -> '{display_category}'")
    
    print("\n=== RIEPILOGO CORREZIONI APPLICATE ===")
    print("1. ✓ Aggiunto eager loading con db.joinedload(Label.category_obj)")
    print("2. ✓ Aggiornato template per usare label.category_obj.name")
    print("3. ✓ Corretto API search per usare category_obj.name")
    print("4. ✓ Corretto API suggest-merge con eager loading")
    print("5. ✓ Corretto API labels-for-ai con eager loading")
    print("6. ✓ Corretto funzione merge_labels con eager loading")
    print("\n=== TEST COMPLETATO ===")
