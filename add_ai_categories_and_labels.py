#!/usr/bin/env python3
"""
Script per aggiungere categorie e etichette di esempio su ostacoli, facilitazioni, benefici, pro e contro dell'uso dell'AI.
"""
from app import create_app
from models import db, Category, Label

def add_ai_categories_and_labels():
    app = create_app()
    with app.app_context():
        # Categorie da aggiungere
        categories = [
            {"name": "Ostacoli AI", "description": "Ostacoli e barriere all'uso dell'Intelligenza Artificiale", "color": "#e74c3c"},
            {"name": "Facilitazioni AI", "description": "Fattori che facilitano l'adozione dell'Intelligenza Artificiale", "color": "#2ecc71"},
            {"name": "Benefici AI", "description": "Benefici percepiti nell'uso dell'Intelligenza Artificiale", "color": "#3498db"},
            {"name": "Pro AI", "description": "Aspetti positivi e vantaggi dell'uso dell'AI", "color": "#1abc9c"},
            {"name": "Contro AI", "description": "Aspetti negativi, rischi o limiti dell'uso dell'AI", "color": "#f39c12"}
        ]
        # Etichette di esempio per ciascuna categoria
        labels = {
            "Ostacoli AI": [
                ("Mancanza di competenze", "Difficoltà dovute a scarsa formazione sull'AI"),
                ("Resistenza al cambiamento", "Timore o diffidenza verso l'adozione di nuove tecnologie"),
                ("Problemi di privacy", "Preoccupazioni per la gestione dei dati personali"),
                ("Costi elevati", "Difficoltà economiche nell'implementazione dell'AI")
            ],
            "Facilitazioni AI": [
                ("Formazione specifica", "Corsi e risorse per apprendere l'uso dell'AI"),
                ("Supporto istituzionale", "Incentivi o linee guida da parte di enti o università"),
                ("Accesso a strumenti AI", "Disponibilità di software e piattaforme AI facilmente accessibili")
            ],
            "Benefici AI": [
                ("Risparmio di tempo", "Automazione di compiti ripetitivi e velocizzazione del lavoro"),
                ("Personalizzazione dell'apprendimento", "Adattamento dei contenuti alle esigenze dello studente"),
                ("Miglioramento delle decisioni", "Supporto all'analisi e alla valutazione tramite AI")
            ],
            "Pro AI": [
                ("Efficienza", "Aumento della produttività e riduzione degli errori"),
                ("Innovazione", "Introduzione di nuove metodologie e strumenti didattici"),
                ("Accessibilità", "Maggiore accesso a risorse e informazioni grazie all'AI")
            ],
            "Contro AI": [
                ("Dipendenza dalla tecnologia", "Rischio di affidarsi troppo agli strumenti AI"),
                ("Perdita di senso critico", "Riduzione della capacità di analisi autonoma"),
                ("Disuguaglianze digitali", "Differenze di accesso e competenze tra studenti")
            ]
        }
        for cat in categories:
            category = Category.query.filter_by(name=cat["name"]).first()
            if not category:
                category = Category(name=cat["name"], description=cat["description"], color=cat["color"], is_active=True)
                db.session.add(category)
                db.session.flush()
                print(f"✓ Categoria creata: {cat['name']}")
            else:
                print(f"- Categoria già esistente: {cat['name']}")
            # Aggiungi etichette
            for label_name, label_desc in labels[cat["name"]]:
                label = Label.query.filter_by(name=label_name, category_id=category.id).first()
                if not label:
                    label = Label(name=label_name, description=label_desc, category_id=category.id, color=cat["color"])
                    db.session.add(label)
                    print(f"  • Etichetta creata: {label_name}")
                else:
                    print(f"  - Etichetta già esistente: {label_name}")
        try:
            db.session.commit()
            print("\n✅ Categorie e etichette AI aggiunte con successo!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Errore: {e}")

if __name__ == "__main__":
    add_ai_categories_and_labels()
