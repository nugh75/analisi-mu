#!/usr/bin/env python3
"""
Script per rimuovere la classificazione automatica e resettare le domande
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from sqlalchemy import text

def main():
    app = create_app()
    
    with app.app_context():
        with db.engine.connect() as connection:
            trans = connection.begin()
            
            try:
                # Prima verifichiamo le colonne esistenti
                result = connection.execute(text('PRAGMA table_info(text_cell)'))
                columns = result.fetchall()
                print('Colonne attuali della tabella text_cell:')
                existing_columns = []
                for col in columns:
                    print(f'  - {col[1]} ({col[2]})')
                    existing_columns.append(col[1])
                
                # Rimuovi colonne della classificazione automatica se esistono
                if 'is_annotatable' in existing_columns:
                    try:
                        connection.execute(text('ALTER TABLE text_cell DROP COLUMN is_annotatable'))
                        print('✓ Rimossa colonna is_annotatable')
                    except Exception as e:
                        print(f'- Errore rimozione is_annotatable: {e}')
                else:
                    print('- is_annotatable non presente')
                
                if 'classification_confidence' in existing_columns:
                    try:
                        connection.execute(text('ALTER TABLE text_cell DROP COLUMN classification_confidence'))
                        print('✓ Rimossa colonna classification_confidence')
                    except Exception as e:
                        print(f'- Errore rimozione classification_confidence: {e}')
                else:
                    print('- classification_confidence non presente')
                
                # Reset della colonna question_type se esiste
                if 'question_type' in existing_columns:
                    try:
                        connection.execute(text('UPDATE text_cell SET question_type = NULL'))
                        count_result = connection.execute(text('SELECT COUNT(*) FROM text_cell'))
                        total_count = count_result.fetchone()[0]
                        print(f'✓ Reset question_type per {total_count} celle')
                    except Exception as e:
                        print(f'Errore reset question_type: {e}')
                else:
                    print('- question_type non presente')
                    
                trans.commit()
                print('\n✅ Reset completato! Ora puoi classificare manualmente le domande.')
                
            except Exception as e:
                trans.rollback()
                print(f'❌ Errore durante il reset: {e}')

if __name__ == '__main__':
    main()
