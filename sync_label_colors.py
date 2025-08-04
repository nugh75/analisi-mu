#!/usr/bin/env python3
"""
Script per sincronizzare i colori delle etichette con quelli delle loro categorie.
Aggiorna tutte le etichette che hanno una categoria affinché ereditino il colore della categoria,
a meno che non abbiano un colore personalizzato esplicitamente diverso.
"""

import sys
import os

# Aggiungi il percorso del progetto al sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Label, Category

def sync_label_colors():
    """Sincronizza i colori delle etichette con quelli delle categorie"""
    
    app = create_app()
    with app.app_context():
        print("🎨 Avvio sincronizzazione colori etichette...")
        
        # Trova tutte le etichette che hanno una categoria
        labels_with_category = Label.query.filter(Label.category_id.isnot(None)).all()
        
        updated_count = 0
        errors = []
        
        for label in labels_with_category:
            try:
                # Ottieni la categoria
                category = Category.query.get(label.category_id)
                if not category:
                    errors.append(f"Etichetta '{label.name}': categoria {label.category_id} non trovata")
                    continue
                
                # Aggiorna il colore dell'etichetta con quello della categoria
                old_color = label.color
                label.color = category.color
                
                if old_color != label.color:
                    print(f"📝 Etichetta '{label.name}': {old_color} → {label.color} (categoria: {category.name})")
                    updated_count += 1
                    
            except Exception as e:
                errors.append(f"Errore con etichetta '{label.name}': {str(e)}")
        
        if errors:
            print("\n❌ Errori riscontrati:")
            for error in errors:
                print(f"  - {error}")
        
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"\n✅ Sincronizzazione completata! Aggiornate {updated_count} etichette.")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Errore durante il salvataggio: {str(e)}")
        else:
            print("\n💡 Nessuna etichetta da aggiornare. Tutti i colori sono già sincronizzati.")
        
        # Mostra statistiche finali
        total_labels = Label.query.count()
        labels_with_category_count = Label.query.filter(Label.category_id.isnot(None)).count()
        labels_without_category_count = Label.query.filter(Label.category_id.is_(None)).count()
        
        print(f"\n📊 Statistiche finali:")
        print(f"  - Totale etichette: {total_labels}")
        print(f"  - Etichette con categoria: {labels_with_category_count}")
        print(f"  - Etichette senza categoria: {labels_without_category_count}")
        print(f"  - Etichette aggiornate: {updated_count}")

def preview_changes():
    """Mostra un'anteprima delle modifiche che verranno apportate"""
    
    app = create_app()
    with app.app_context():
        print("👀 Anteprima modifiche colori etichette...")
        
        labels_with_category = Label.query.filter(Label.category_id.isnot(None)).all()
        
        changes = []
        for label in labels_with_category:
            category = Category.query.get(label.category_id)
            if category and label.color != category.color:
                changes.append({
                    'label': label.name,
                    'category': category.name,
                    'old_color': label.color,
                    'new_color': category.color
                })
        
        if changes:
            print(f"\n📋 {len(changes)} etichette verranno aggiornate:")
            for change in changes:
                print(f"  • {change['label']} ({change['category']}): {change['old_color']} → {change['new_color']}")
        else:
            print("\n💡 Nessuna etichetta necessita di aggiornamenti.")
        
        return len(changes)

def main():
    """Funzione principale"""
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        preview_count = preview_changes()
        if preview_count > 0:
            print(f"\nEsegui '{sys.argv[0]}' senza --preview per applicare le modifiche.")
    else:
        sync_label_colors()

if __name__ == "__main__":
    main()
