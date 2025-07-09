#!/usr/bin/env python3
"""
Script di verifica finale per l'UI Admin AI
"""

import os
import re

def check_template_test_buttons():
    """Verifica che tutti i template abbiano i pulsanti di test"""
    
    template_dir = "/home/nugh75/Git/analisi-mu/templates/admin"
    templates_to_check = [
        "ai_configuration.html",
        "create_ai_config.html", 
        "edit_ai_config.html",
        "ollama_models.html",
        "openrouter_models.html"
    ]
    
    results = {}
    
    for template in templates_to_check:
        file_path = os.path.join(template_dir, template)
        
        if not os.path.exists(file_path):
            results[template] = "❌ File non trovato"
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Cerca pulsanti di test
        test_patterns = [
            r'test.*btn',
            r'Test.*Connessione',
            r'Test.*Configurazione',
            r'Test.*Modello',
            r'data-.*test',
            r'btn.*test'
        ]
        
        found_patterns = []
        for pattern in test_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
        
        if found_patterns:
            results[template] = f"✅ Pulsanti test trovati: {len(found_patterns)} pattern"
        else:
            results[template] = "❌ Nessun pulsante test trovato"
    
    return results

def check_admin_endpoints():
    """Verifica che gli endpoint admin siano implementati"""
    
    admin_file = "/home/nugh75/Git/analisi-mu/routes/admin.py"
    
    if not os.path.exists(admin_file):
        return {"admin.py": "❌ File non trovato"}
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_endpoints = [
        "test_ai_config",
        "test-ai-config-preview", 
        "ollama/test-model",
        "openrouter/test-model"
    ]
    
    results = {}
    for endpoint in required_endpoints:
        if endpoint in content:
            results[endpoint] = "✅ Endpoint implementato"
        else:
            results[endpoint] = "❌ Endpoint mancante"
    
    return results

def main():
    print("🔍 VERIFICA FINALE UI ADMIN AI")
    print("="*50)
    
    # Verifica template
    print("\n📁 VERIFICA TEMPLATE:")
    template_results = check_template_test_buttons()
    for template, status in template_results.items():
        print(f"  {template}: {status}")
    
    # Verifica endpoint
    print("\n🌐 VERIFICA ENDPOINT:")
    endpoint_results = check_admin_endpoints()
    for endpoint, status in endpoint_results.items():
        print(f"  {endpoint}: {status}")
    
    # Conteggio
    template_ok = sum(1 for status in template_results.values() if status.startswith("✅"))
    endpoint_ok = sum(1 for status in endpoint_results.values() if status.startswith("✅"))
    
    print("\n📊 RIEPILOGO:")
    print(f"  Template con pulsanti test: {template_ok}/{len(template_results)}")
    print(f"  Endpoint implementati: {endpoint_ok}/{len(endpoint_results)}")
    
    if template_ok == len(template_results) and endpoint_ok == len(endpoint_results):
        print("\n🎉 VERIFICA COMPLETATA CON SUCCESSO!")
        print("   Tutte le funzionalità di test sono implementate")
    else:
        print("\n⚠️  ALCUNE VERIFICHE FALLITE")
        print("   Controlla i dettagli sopra")

if __name__ == "__main__":
    main()
