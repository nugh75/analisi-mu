#!/usr/bin/env python3
"""
Script di test per verificare il fix dell'endpoint AI prompt/preview
"""
import sys
import os

# Aggiungi la directory corrente al path
sys.path.append('.')

from app import create_app
from models import db, Label
from sqlalchemy.orm import joinedload

def test_ai_fix():
    """Test del fix per l'endpoint AI"""
    print("🧪 Testing AI fix...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test della query con joinedload
            print("📊 Testing Label query with joinedload...")
            labels = Label.query.options(joinedload(Label.category_obj)).filter_by(is_active=True).limit(5).all()
            print(f"✅ Query labels OK: {len(labels)} labels trovati")
            
            for label in labels:
                category_name = label.category_obj.name if label.category_obj else 'Generale'
                print(f"  - {label.name} -> {category_name}")
            
            # Test del servizio AI
            print("\n🤖 Testing AIAnnotatorService...")
            from services.ai_annotator import AIAnnotatorService
            service = AIAnnotatorService()
            print("✅ AIAnnotatorService instantiation OK")
            
            if labels:
                test_texts = ['Test text 1', 'Test text 2']
                prompt = service.build_annotation_prompt(test_texts, labels[:3])
                print(f"✅ build_annotation_prompt OK: {len(prompt)} caratteri")
                print(f"📝 Preview prompt (primi 200 caratteri):")
                print(prompt[:200] + "...")
            else:
                print("⚠️ Nessun label disponibile per il test")
            
            print("\n🎉 Tutti i test completati con successo!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    success = test_ai_fix()
    sys.exit(0 if success else 1)
