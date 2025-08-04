#!/usr/bin/env python3
"""
Script per sincronizzare i colori delle etichette con quelli delle categorie
"""

import sys
import os

# Aggiungi il percorso dell'applicazione
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def sync_label_colors():
    """Sincronizza i colori delle etichette con le categorie"""
    
    # Import locale per evitare problemi di configurazione
    from app import create_app
    from models import db, Label, Category
    
    app = create_app()
    
    with app.app_context():
        print("Sincronizzazione colori etichette...")
        
        # Trova tutte le etichette che hanno una categoria
        labels_with_category = Label.query.filter(Label.category_id.isnot(None)).all()
        
        updated_count = 0
        for label in labels_with_category:
            if label.category_obj:
                # Se l'etichetta non ha un colore personalizzato, eredita quello della categoria
                if not label.has_custom_color():
                    old_color = label.color
                    label.color = label.category_obj.color
                    print(f"  Etichetta '{label.name}': {old_color} -> {label.color}")
                    updated_count += 1
                else:
                    print(f"  Etichetta '{label.name}': mantiene colore personalizzato {label.color}")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ Sincronizzate {updated_count} etichette")
        else:
            print("\n✅ Nessuna etichetta da sincronizzare")
        
        # Statistiche finali
        total_labels = Label.query.count()
        labels_with_categories = Label.query.filter(Label.category_id.isnot(None)).count()
        labels_without_categories = total_labels - labels_with_categories
        
        print(f"\n📊 Statistiche:")
        print(f"   - Etichette totali: {total_labels}")
        print(f"   - Con categoria: {labels_with_categories}")
        print(f"   - Senza categoria: {labels_without_categories}")
        print(f"   - Sincronizzate: {updated_count}")

if __name__ == '__main__':
    try:
        sync_label_colors()
    except Exception as e:
        print(f"❌ Errore durante la sincronizzazione: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
