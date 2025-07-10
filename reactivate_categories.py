#!/usr/bin/env python3
"""
Script per riattivare tutte le categorie che sono state disattivate durante la migrazione
"""

import sqlite3
import os
from datetime import datetime

def reactivate_categories():
    """Riattiva tutte le categorie che sono state disattivate"""
    db_path = os.path.join('instance', 'analisi_mu.db')
    
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Conta le categorie inattive
        cursor.execute("SELECT COUNT(*) FROM category WHERE is_active = 0")
        inactive_count = cursor.fetchone()[0]
        
        # Conta le etichette inattive
        cursor.execute("SELECT COUNT(*) FROM label WHERE is_active = 0")
        inactive_labels_count = cursor.fetchone()[0]
        
        print(f"Trovate {inactive_count} categorie inattive")
        print(f"Trovate {inactive_labels_count} etichette inattive")
        
        if inactive_count > 0:
            response = input(f"Vuoi riattivare tutte le {inactive_count} categorie inattive? (y/n): ")
            if response.lower() == 'y':
                cursor.execute("UPDATE category SET is_active = 1 WHERE is_active = 0")
                print(f"✓ Riattivate {inactive_count} categorie")
        
        if inactive_labels_count > 0:
            response = input(f"Vuoi riattivare tutte le {inactive_labels_count} etichette inattive? (y/n): ")
            if response.lower() == 'y':
                cursor.execute("UPDATE label SET is_active = 1 WHERE is_active = 0")
                print(f"✓ Riattivate {inactive_labels_count} etichette")
        
        conn.commit()
        print("✓ Operazione completata con successo!")
        return True
        
    except Exception as e:
        print(f"Errore durante l'operazione: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def show_stats():
    """Mostra le statistiche delle categorie ed etichette"""
    db_path = os.path.join('instance', 'analisi_mu.db')
    
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Statistiche categorie
        cursor.execute("SELECT COUNT(*) FROM category WHERE is_active = 1")
        active_categories = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM category WHERE is_active = 0")
        inactive_categories = cursor.fetchone()[0]
        
        # Statistiche etichette
        cursor.execute("SELECT COUNT(*) FROM label WHERE is_active = 1")
        active_labels = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM label WHERE is_active = 0")
        inactive_labels = cursor.fetchone()[0]
        
        print("\n=== STATISTICHE ATTUALI ===")
        print(f"Categorie attive: {active_categories}")
        print(f"Categorie inattive: {inactive_categories}")
        print(f"Etichette attive: {active_labels}")
        print(f"Etichette inattive: {inactive_labels}")
        print(f"Totale categorie: {active_categories + inactive_categories}")
        print(f"Totale etichette: {active_labels + inactive_labels}")
        
    except Exception as e:
        print(f"Errore durante la lettura delle statistiche: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("=== Riattivazione Categorie e Etichette ===")
    
    # Mostra statistiche attuali
    show_stats()
    
    # Offri opzione di riattivazione
    print("\nDesideri riattivare categorie e/o etichette?")
    if reactivate_categories():
        print("\n=== STATISTICHE DOPO LA RIATTIVAZIONE ===")
        show_stats()
    else:
        print("\n✗ Operazione annullata o fallita!")
