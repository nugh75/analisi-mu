#!/usr/bin/env python3
"""
Rimuove la classificazione automatica delle domande e aggiunge interfaccia manuale
"""

import sys
import os

# Aggiungi il percorso radice del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import TextCell
from sqlalchemy import text

def remove_classification():
    """Rimuove i campi di classificazione automatica"""
    
    with app.app_context():
        try:
            # Rimuovi le colonne di classificazione
            connection = db.engine.connect()
            
            # Rimuovi question_type
            try:
                connection.execute(text('ALTER TABLE text_cell DROP COLUMN question_type'))
                print("✓ Rimossa colonna question_type")
            except Exception as e:
                print(f"Colonna question_type già rimossa o non esistente: {e}")
            
            # Rimuovi is_annotatable 
            try:
                connection.execute(text('ALTER TABLE text_cell DROP COLUMN is_annotatable'))
                print("✓ Rimossa colonna is_annotatable")
            except Exception as e:
                print(f"Colonna is_annotatable già rimossa o non esistente: {e}")
                
            # Rimuovi classification_confidence
            try:
                connection.execute(text('ALTER TABLE text_cell DROP COLUMN classification_confidence'))
                print("✓ Rimossa colonna classification_confidence")
            except Exception as e:
                print(f"Colonna classification_confidence già rimossa o non esistente: {e}")
            
            connection.close()
            
            # Aggiungi solo question_type per classificazione manuale (nullable)
            connection = db.engine.connect()
            try:
                connection.execute(text('ALTER TABLE text_cell ADD COLUMN question_type TEXT'))
                print("✓ Aggiunta colonna question_type per classificazione manuale")
            except Exception as e:
                print(f"Errore aggiungendo question_type manuale: {e}")
            
            connection.close()
            
            print("\n✅ Classificazione automatica rimossa con successo!")
            print("Ora potrai classificare manualmente le domande dalla panoramica.")
            
        except Exception as e:
            print(f"❌ Errore durante la rimozione: {e}")
            return False
    
    return True

if __name__ == "__main__":
    remove_classification()
