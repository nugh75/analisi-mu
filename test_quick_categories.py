#!/usr/bin/env python3
"""
Test rapido per verificare le relazioni categoria-label dopo le correzioni
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Label, Category, db

app = create_app()

with app.app_context():
    print("=== TEST EAGER LOADING CATEGORIE ===\n")
    
    # Test con eager loading
    labels = Label.query.options(db.joinedload(Label.category_obj)).limit(10).all()
    
    print(f"Primi 10 label con eager loading:\n")
    
    for label in labels:
        category_display = label.category_obj.name if label.category_obj else 'Nessuna categoria'
        print(f"• {label.name:<30} -> {category_display}")
        print(f"  category_id: {label.category_id}")
        if label.category_obj:
            print(f"  category_obj.id: {label.category_obj.id}")
        print()
    
    print("\n=== TEST SPECIFICO CATEGORIE ESISTENTI ===\n")
    
    # Test delle categorie con label
    categories = Category.query.filter_by(is_active=True).all()
    
    for category in categories:
        labels_in_cat = Label.query.options(db.joinedload(Label.category_obj))\
                                 .filter_by(category_id=category.id)\
                                 .limit(3).all()
        
        print(f"Categoria: {category.name} (ID: {category.id})")
        print(f"  Label in questa categoria: {len(labels_in_cat)}")
        
        for label in labels_in_cat:
            display_cat = label.category_obj.name if label.category_obj else 'ERROR!'
            print(f"    - {label.name} -> '{display_cat}'")
        print()
    
    print("=== TEST COMPLETATO ===")
