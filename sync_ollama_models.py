#!/usr/bin/env python3
"""
Script per sincronizzare i modelli Ollama con il database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_client import OllamaClient
from models import db, OllamaModel
from app import create_app
from datetime import datetime

def sync_ollama_models():
    """Sincronizza i modelli Ollama con il database"""
    
    app = create_app()
    
    with app.app_context():
        client = OllamaClient('http://192.168.129.14:11435')
        
        print("Testing Ollama connection...")
        if not client.test_connection():
            print("❌ Impossibile connettersi a Ollama")
            return False
        
        print("✅ Connessione a Ollama riuscita")
        
        # Ottieni i modelli da Ollama
        print("Recupero modelli da Ollama...")
        ollama_models = client.list_models()
        
        if not ollama_models:
            print("❌ Nessun modello trovato su Ollama")
            return False
        
        print(f"📦 Trovati {len(ollama_models)} modelli su Ollama")
        
        # Sincronizza con il database
        for model_data in ollama_models:
            name = model_data.get('name', '')
            
            # Estrai nome e tag
            if ':' in name:
                model_name, tag = name.split(':', 1)
            else:
                model_name = name
                tag = 'latest'
            
            # Cerca se il modello esiste già
            existing_model = OllamaModel.query.filter_by(name=model_name, tag=tag).first()
            
            details = model_data.get('details', {})
            
            if existing_model:
                # Aggiorna modello esistente
                existing_model.size = model_data.get('size', 0)
                existing_model.digest = model_data.get('digest', '')
                existing_model.modified_at = datetime.fromisoformat(
                    model_data.get('modified_at', '').replace('Z', '+00:00')
                ) if model_data.get('modified_at') else None
                existing_model.is_pulled = True
                existing_model.pull_progress = 100.0
                existing_model.updated_at = datetime.utcnow()
                
                print(f"🔄 Aggiornato: {model_name}:{tag}")
            else:
                # Crea nuovo modello
                new_model = OllamaModel(
                    name=model_name,
                    tag=tag,
                    size=model_data.get('size', 0),
                    digest=model_data.get('digest', ''),
                    modified_at=datetime.fromisoformat(
                        model_data.get('modified_at', '').replace('Z', '+00:00')
                    ) if model_data.get('modified_at') else None,
                    is_pulled=True,
                    pull_progress=100.0
                )
                
                db.session.add(new_model)
                print(f"➕ Aggiunto: {model_name}:{tag}")
        
        # Segna come non disponibili i modelli che non sono più su Ollama
        db_models = OllamaModel.query.all()
        ollama_model_names = set()
        for model_data in ollama_models:
            name = model_data.get('name', '')
            if ':' in name:
                model_name, tag = name.split(':', 1)
            else:
                model_name = name
                tag = 'latest'
            ollama_model_names.add(f"{model_name}:{tag}")
        
        for db_model in db_models:
            db_model_name = f"{db_model.name}:{db_model.tag}"
            if db_model_name not in ollama_model_names and db_model.is_pulled:
                db_model.is_pulled = False
                db_model.pull_progress = 0.0
                print(f"❌ Rimosso: {db_model_name}")
        
        try:
            db.session.commit()
            print("✅ Sincronizzazione completata con successo!")
            
            # Mostra riepilogo
            print("\n📊 Riepilogo modelli:")
            models = OllamaModel.query.filter_by(is_pulled=True).all()
            for model in models:
                size_gb = model.size / (1024**3) if model.size else 0
                print(f"  - {model.name}:{model.tag} ({size_gb:.1f} GB)")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore nel salvataggio: {e}")
            return False

if __name__ == '__main__':
    success = sync_ollama_models()
    sys.exit(0 if success else 1)
