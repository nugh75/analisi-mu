#!/usr/bin/env python3
"""
Script per debuggare le categorie del forum
Mostra quali file Excel hanno categorie e quali no
"""

import os
import sys
from pathlib import Path

# Aggiungi il percorso del progetto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configura l'ambiente
os.environ['DATABASE_URL'] = f'sqlite:///{project_root}/instance_dev/analisi_mu_dev.db'

from models import db, ExcelFile, ForumCategory, TextCell
from app import create_app

def main():
    app = create_app()
    
    with app.app_context():
        print("🔍 ANALISI CATEGORIE FORUM")
        print("=" * 60)
        
        # Ottieni tutti i file Excel
        files = ExcelFile.query.all()
        
        print(f"📊 Trovati {len(files)} file Excel")
        print()
        
        for file in files:
            print(f"📁 File: {file.original_filename}")
            print(f"   ID: {file.id}")
            
            # Conta le categorie
            categories = ForumCategory.query.filter_by(excel_file_id=file.id).all()
            print(f"   🏷️  Categorie: {len(categories)}")
            
            if categories:
                for cat in categories:
                    print(f"      - {cat.name} ({'Sistema' if cat.is_system else 'Utente'})")
            
            # Conta le colonne distinte (domande potenziali)
            distinct_columns = db.session.query(TextCell.column_name)\
                                        .filter_by(excel_file_id=file.id)\
                                        .filter(TextCell.column_name.isnot(None))\
                                        .distinct().all()
            
            column_names = [col[0] for col in distinct_columns if col[0] and col[0].strip()]
            print(f"   ❓ Domande (colonne): {len(column_names)}")
            
            if len(column_names) <= 5:  # Mostra solo se ci sono poche colonne
                for col in column_names:
                    print(f"      - {col[:60]}{'...' if len(col) > 60 else ''}")
            
            # Diagnosi
            if len(categories) == 0:
                print(f"   ⚠️  PROBLEMA: Nessuna categoria creata!")
                print(f"      💡 Soluzione: Accedi al forum del file per creare le categorie automaticamente")
            elif len(categories) == 1 and categories[0].name.startswith("💬"):
                print(f"   ⚠️  SOLO CATEGORIA GENERALE: Mancano le categorie per le domande")
                print(f"      💡 Soluzione: Usa il pulsante 'Rigenera Categorie' nel forum")
            elif len(categories) < len(column_names):
                print(f"   ⚠️  CATEGORIE INCOMPLETE: {len(categories)} categorie vs {len(column_names)} domande")
                print(f"      💡 Soluzione: Usa il pulsante 'Rigenera Categorie' nel forum")
            else:
                print(f"   ✅ OK: Categorie complete")
            
            print()

if __name__ == '__main__':
    main()
