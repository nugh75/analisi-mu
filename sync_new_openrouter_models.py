#!/usr/bin/env python3
"""
Script per sincronizzare i nuovi modelli OpenRouter gratuiti nel database
"""

import os
import sys
from datetime import datetime

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, OpenRouterModel
from services.openrouter_client import KNOWN_FREE_MODELS

def sync_new_models():
    """Sincronizza i nuovi modelli OpenRouter nel database"""
    app = create_app()
    with app.app_context():
        added_count = 0
        updated_count = 0
        
        print("Sincronizzazione modelli OpenRouter gratuiti...")
        print(f"Modelli da sincronizzare: {len(KNOWN_FREE_MODELS)}")
        
        for model_data in KNOWN_FREE_MODELS:
            model_id = model_data['id']
            
            # Verifica se il modello esiste già
            existing_model = OpenRouterModel.query.filter_by(model_id=model_id).first()
            
            if existing_model:
                # Aggiorna il modello esistente
                existing_model.name = model_data['name']
                existing_model.description = model_data.get('description', '')
                existing_model.context_length = model_data.get('context_length', 0)
                existing_model.pricing_prompt = float(model_data.get('pricing', {}).get('prompt', '0'))
                existing_model.pricing_completion = float(model_data.get('pricing', {}).get('completion', '0'))
                existing_model.is_free = True
                existing_model.is_available = True
                existing_model.updated_at = datetime.utcnow()
                updated_count += 1
                print(f"  ✓ Aggiornato: {model_data['name']}")
            else:
                # Crea un nuovo modello
                new_model = OpenRouterModel(
                    model_id=model_id,
                    name=model_data['name'],
                    description=model_data.get('description', ''),
                    context_length=model_data.get('context_length', 0),
                    pricing_prompt=float(model_data.get('pricing', {}).get('prompt', '0')),
                    pricing_completion=float(model_data.get('pricing', {}).get('completion', '0')),
                    is_free=True,
                    is_available=True
                )
                db.session.add(new_model)
                added_count += 1
                print(f"  + Aggiunto: {model_data['name']}")
        
        # Commit delle modifiche
        try:
            db.session.commit()
            print(f"\n✅ Sincronizzazione completata!")
            print(f"   - Modelli aggiunti: {added_count}")
            print(f"   - Modelli aggiornati: {updated_count}")
            print(f"   - Totale modelli gratuiti: {len(KNOWN_FREE_MODELS)}")
            
            # Mostra statistiche del database
            total_models = OpenRouterModel.query.count()
            free_models = OpenRouterModel.query.filter_by(is_free=True).count()
            print(f"\n📊 Statistiche database:")
            print(f"   - Modelli totali: {total_models}")
            print(f"   - Modelli gratuiti: {free_models}")
            print(f"   - Modelli a pagamento: {total_models - free_models}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Errore durante la sincronizzazione: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    print("=== Sincronizzazione Modelli OpenRouter ===\n")
    
    # Verifica che il database esista
    db_path = os.path.join('instance', 'analisi_mu.db')
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        print("   Esegui prima 'python init_database.py' per creare il database")
        sys.exit(1)
    
    # Esegui la sincronizzazione
    success = sync_new_models()
    
    if success:
        print("\n✨ Tutti i modelli sono stati sincronizzati con successo!")
        print("   Ora puoi utilizzare i nuovi modelli gratuiti nell'applicazione.")
    else:
        print("\n⚠️  La sincronizzazione ha riscontrato degli errori.")
        sys.exit(1)