#!/usr/bin/env python3
"""
Script per testare i miglioramenti al sistema AI
"""

import os
import sys
import requests
import json

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIConfiguration, ExcelFile, Label, Category

def test_ai_improvements():
    """Testa i miglioramenti al sistema AI"""
    app = create_app()
    
    with app.app_context():
        print("=== Test Miglioramenti Sistema AI ===\n")
        
        # 1. Test caricamento template
        print("1. Test caricamento template...")
        from services.ai_annotator import AIAnnotatorService
        
        ai_service = AIAnnotatorService()
        templates = ai_service.get_available_templates()
        
        print(f"   Template disponibili: {len(templates)}")
        for tid, template in templates.items():
            print(f"   - ID {tid}: {template['name']} - {template['description']}")
        
        # 2. Test validazione configurazione
        print("\n2. Test validazione configurazione AI...")
        config = ai_service.get_active_configuration()
        if config:
            print(f"   ✓ Configurazione attiva trovata: {config.name}")
            print(f"   - Provider: {config.provider}")
            print(f"   - Modello: {config.ollama_model or config.openrouter_model}")
        else:
            print("   ⚠️  Nessuna configurazione AI attiva")
        
        # 3. Test conteggio etichette
        print("\n3. Test etichette disponibili...")
        active_labels = Label.query.filter_by(is_active=True).all()
        print(f"   Etichette attive: {len(active_labels)}")
        
        # Raggruppa per categoria
        from collections import defaultdict
        categories_count = defaultdict(int)
        for label in active_labels:
            cat_name = label.category_obj.name if label.category_obj else 'Generale'
            categories_count[cat_name] += 1
        
        for cat, count in categories_count.items():
            print(f"   - {cat}: {count} etichette")
        
        # 4. Test costruzione prompt
        print("\n4. Test costruzione prompt...")
        if active_labels:
            # Simula alcuni testi
            test_texts = [
                "Qual è la capitale d'Italia?",
                "Calcola l'area di un triangolo con base 5 e altezza 3",
                "Spiega il concetto di fotosintesi"
            ]
            
            try:
                prompt = ai_service.build_annotation_prompt(test_texts, active_labels, 1)
                print(f"   ✓ Prompt generato con successo ({len(prompt)} caratteri)")
                
                # Verifica che il prompt contenga elementi chiave
                checks = [
                    ("ETICHETTE DISPONIBILI" in prompt, "Lista etichette"),
                    ("TESTI DA ETICHETTARE" in prompt, "Sezione testi"),
                    ("JSON" in prompt, "Formato risposta"),
                    (len([line for line in prompt.split('\n') if line.strip().startswith('•')]) > 0, "Etichette formattate")
                ]
                
                for check, desc in checks:
                    status = "✓" if check else "✗"
                    print(f"   {status} {desc}")
                    
            except Exception as e:
                print(f"   ✗ Errore nella generazione prompt: {e}")
        
        # 5. Test parsing risposta AI
        print("\n5. Test parsing risposta AI...")
        test_responses = [
            '[{"index": 0, "label": "Geografia", "confidence": 0.95}]',
            '```json\n[{"index": 0, "label": "Test", "confidence": 0.8}]\n```',
            'Ecco la risposta: [{"index": 0, "label": "Esempio", "confidence": 0.7}]',
            '{"index": 0, "label": "Singolo", "confidence": 0.6}'
        ]
        
        for i, response in enumerate(test_responses):
            try:
                parsed = ai_service._parse_ai_response(response)
                print(f"   Test {i+1}: ✓ Parsed {len(parsed)} elementi")
            except Exception as e:
                print(f"   Test {i+1}: ✗ Errore: {e}")
        
        print("\n=== Test completato ===")

if __name__ == "__main__":
    test_ai_improvements()
