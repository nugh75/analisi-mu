#!/home/nugh75/Git/analisi-mu/.venv/bin/python
"""
Script per sincronizzare i colori delle etichette con le categorie
Supporta sia sincronizzazione standard che forzata
Utilizza l'ambiente virtuale .venv del progetto
"""

import os
import sys
import argparse
from datetime import datetime

# Aggiungi il percorso del progetto al sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Cambia nella directory del progetto per accedere al database
os.chdir(project_root)

from app import create_app, db
from models import Label, Category

def sync_label_colors(force=False, verbose=False):
    """
    Sincronizza i colori delle etichette con le categorie
    
    Args:
        force (bool): Se True, forza la sincronizzazione anche per etichette con colori personalizzati
        verbose (bool): Se True, mostra informazioni dettagliate
    
    Returns:
        tuple: (etichette_aggiornate, etichette_totali)
    """
    
    # Trova tutte le etichette che hanno una categoria
    labels_with_category = Label.query.filter(Label.category_id.isnot(None)).all()
    
    if verbose:
        print(f"Trovate {len(labels_with_category)} etichette con categoria")
    
    updated_count = 0
    total_count = len(labels_with_category)
    
    for label in labels_with_category:
        if label.category_obj:
            old_color = label.color
            category_color = label.category_obj.color
            
            # Determina se aggiornare il colore
            should_update = False
            reason = ""
            
            if force:
                should_update = True
                reason = "sincronizzazione forzata"
            elif not label.has_custom_color():
                should_update = True
                reason = "nessun colore personalizzato"
            
            if should_update:
                label.color = category_color
                updated_count += 1
                
                if verbose:
                    print(f"✓ Etichetta '{label.name}': {old_color} → {category_color} ({reason})")
            else:
                if verbose:
                    print(f"- Etichetta '{label.name}': mantenuto colore personalizzato {old_color}")
        else:
            if verbose:
                print(f"! Etichetta '{label.name}': categoria non trovata")
    
    return updated_count, total_count

def main():
    parser = argparse.ArgumentParser(description='Sincronizza i colori delle etichette con le categorie')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Forza la sincronizzazione anche per etichette con colori personalizzati')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostra informazioni dettagliate')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Simula l\'operazione senza salvare le modifiche')
    
    args = parser.parse_args()
    
    # Crea l'app Flask
    app = create_app()
    
    with app.app_context():
        print("=== Sincronizzazione Colori Etichette ===")
        print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Modalità: {'Forzata' if args.force else 'Standard'}")
        
        if args.dry_run:
            print("🔍 MODALITÀ DRY-RUN (nessuna modifica sarà salvata)")
        
        print("-" * 50)
        
        try:
            # Esegui la sincronizzazione
            updated_count, total_count = sync_label_colors(
                force=args.force, 
                verbose=args.verbose
            )
            
            if not args.dry_run and updated_count > 0:
                # Salva le modifiche
                db.session.commit()
                print(f"✅ Database aggiornato!")
            elif args.dry_run:
                print(f"🔍 Dry-run completato (nessuna modifica salvata)")
            
            print("-" * 50)
            print(f"📊 RIEPILOGO:")
            print(f"   • Etichette esaminate: {total_count}")
            print(f"   • Etichette aggiornate: {updated_count}")
            
            if updated_count == 0:
                print("   • Tutte le etichette sono già sincronizzate!")
            
            success_rate = (updated_count / total_count * 100) if total_count > 0 else 0
            print(f"   • Tasso di aggiornamento: {success_rate:.1f}%")
            
        except Exception as e:
            print(f"❌ Errore durante la sincronizzazione: {str(e)}")
            if not args.dry_run:
                db.session.rollback()
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
