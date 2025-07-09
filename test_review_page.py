#!/usr/bin/env python3
"""
Test per verificare cosa viene mostrato nella pagina di revisione AI
"""

import requests

def test_review_page():
    # Test accesso alla pagina
    try:
        response = requests.get('http://localhost:5001/ai/review/file/1')
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 302:
            print("Reindirizzamento (probabilmente login richiesto)")
            print(f"Location: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 200:
            print("Pagina caricata correttamente")
            
            # Cerca elementi chiave nel HTML
            html = response.text
            
            if 'pending_annotations' in html:
                print("✅ Variabile pending_annotations trovata nel template")
            else:
                print("❌ Variabile pending_annotations NON trovata")
                
            if 'annotation-card' in html:
                print("✅ Elementi annotation-card trovati")
            else:
                print("❌ Nessun elemento annotation-card trovato")
                
            if 'accept-btn' in html:
                print("✅ Pulsanti accept-btn trovati")
            else:
                print("❌ Nessun pulsante accept-btn trovato")
                
            if 'initializeEventListeners' in html:
                print("✅ Funzione JavaScript trovata")
            else:
                print("❌ JavaScript NON trovato")
                
            # Conta occorrenze
            card_count = html.count('annotation-card')
            btn_count = html.count('accept-btn')
            print(f"📊 Conteggi: {card_count} cards, {btn_count} pulsanti accetta")
            
            # Mostra parte dell'HTML per debug
            if 'Nessuna Annotazione da Rivedere' in html:
                print("⚠️  Stato vuoto: nessuna annotazione da rivedere")
                
        else:
            print(f"Errore HTTP: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Errore nella richiesta: {e}")

if __name__ == "__main__":
    test_review_page()
