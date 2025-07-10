#!/usr/bin/env python3
"""
Test rapido per verificare il funzionamento del CSRF token
"""

from app import app
from flask import render_template_string

def test_csrf_token():
    """Test per verificare che il token CSRF sia disponibile"""
    with app.test_client() as client:
        with app.app_context():
            # Test del token CSRF
            template = "{{ csrf_token() }}"
            try:
                token = render_template_string(template)
                print(f"✓ Token CSRF generato: {token[:10]}...")
                return True
            except Exception as e:
                print(f"✗ Errore generazione token CSRF: {e}")
                return False

if __name__ == '__main__':
    print("=== Test CSRF Token ===")
    
    if test_csrf_token():
        print("✓ CSRF token funziona correttamente")
    else:
        print("✗ Problema con CSRF token")
