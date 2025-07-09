#!/usr/bin/env python3
"""
Script per creare categorie ed etichette specifiche per l'analisi dell'uso dell'AI.
Include pro/contro, ostacoli, facilitazioni e benefici.
"""

from app import create_app
from models import db, Category, Label

def create_ai_categories_and_labels():
    """Crea categorie ed etichette specifiche per l'analisi dell'AI"""
    
    # Definizione delle categorie e relative etichette
    ai_categories = {
        'Pro AI': {
            'description': 'Aspetti positivi e vantaggi dell\'utilizzo dell\'AI',
            'color': '#27ae60',  # Verde
            'labels': [
                {'name': 'Efficienza', 'description': 'Miglioramento dell\'efficienza e velocità'},
                {'name': 'Automazione', 'description': 'Automatizzazione di compiti ripetitivi'},
                {'name': 'Personalizzazione', 'description': 'Personalizzazione dell\'esperienza utente'},
                {'name': 'Precisione', 'description': 'Maggiore precisione e accuratezza'},
                {'name': 'Innovazione', 'description': 'Promozione dell\'innovazione e creatività'},
                {'name': 'Accessibilità', 'description': 'Miglioramento dell\'accessibilità'},
                {'name': 'Supporto Decisionale', 'description': 'Aiuto nel processo decisionale'},
                {'name': 'Riduzione Errori', 'description': 'Riduzione degli errori umani'}
            ]
        },
        'Contro AI': {
            'description': 'Aspetti negativi e svantaggi dell\'utilizzo dell\'AI',
            'color': '#e74c3c',  # Rosso
            'labels': [
                {'name': 'Perdita Lavoro', 'description': 'Preoccupazioni per la perdita di posti di lavoro'},
                {'name': 'Dipendenza Tecnologica', 'description': 'Eccessiva dipendenza dalla tecnologia'},
                {'name': 'Mancanza Controllo', 'description': 'Perdita di controllo sui processi'},
                {'name': 'Disumanizzazione', 'description': 'Riduzione del fattore umano'},
                {'name': 'Complessità', 'description': 'Eccessiva complessità tecnologica'},
                {'name': 'Costi Elevati', 'description': 'Costi di implementazione e mantenimento'},
                {'name': 'Bias Algoritmico', 'description': 'Pregiudizi incorporati negli algoritmi'},
                {'name': 'Obsolescenza Competenze', 'description': 'Rischio di obsolescenza delle competenze attuali'}
            ]
        },
        'Ostacoli AI': {
            'description': 'Barriere e ostacoli nell\'adozione dell\'AI',
            'color': '#f39c12',  # Arancione
            'labels': [
                {'name': 'Competenze Tecniche', 'description': 'Mancanza di competenze tecniche necessarie'},
                {'name': 'Resistenza al Cambiamento', 'description': 'Resistenza organizzativa o personale'},
                {'name': 'Costi Implementazione', 'description': 'Elevati costi di implementazione'},
                {'name': 'Problemi Privacy', 'description': 'Preoccupazioni per la privacy dei dati'},
                {'name': 'Infrastruttura Inadeguata', 'description': 'Infrastruttura tecnologica inadeguata'},
                {'name': 'Formazione Insufficiente', 'description': 'Mancanza di formazione adeguata'},
                {'name': 'Regolamentazione Unclear', 'description': 'Incertezza normativa e regolamentare'},
                {'name': 'Integrazione Sistemi', 'description': 'Difficoltà di integrazione con sistemi esistenti'},
                {'name': 'Scetticismo', 'description': 'Scetticismo verso la tecnologia AI'},
                {'name': 'Tempi Implementazione', 'description': 'Lunghi tempi di implementazione'}
            ]
        },
        'Facilitatori AI': {
            'description': 'Fattori che facilitano l\'adozione dell\'AI',
            'color': '#3498db',  # Blu
            'labels': [
                {'name': 'Formazione Adeguata', 'description': 'Programmi di formazione efficaci'},
                {'name': 'Supporto Organizzativo', 'description': 'Supporto da parte dell\'organizzazione'},
                {'name': 'Risorse Disponibili', 'description': 'Disponibilità di risorse necessarie'},
                {'name': 'Cultura Innovativa', 'description': 'Cultura organizzativa orientata all\'innovazione'},
                {'name': 'Leadership Supportiva', 'description': 'Leadership che supporta il cambiamento'},
                {'name': 'Collaborazione', 'description': 'Spirito collaborativo e di squadra'},
                {'name': 'Mentoring', 'description': 'Presenza di mentori e guide'},
                {'name': 'Incentivi', 'description': 'Incentivi per l\'adozione della tecnologia'},
                {'name': 'Comunicazione Chiara', 'description': 'Comunicazione chiara degli obiettivi'},
                {'name': 'Gradualità', 'description': 'Implementazione graduale e progressiva'}
            ]
        },
        'Benefici AI': {
            'description': 'Benefici concreti derivanti dall\'uso dell\'AI',
            'color': '#2ecc71',  # Verde chiaro
            'labels': [
                {'name': 'Risparmio Tempo', 'description': 'Significativo risparmio di tempo'},
                {'name': 'Miglior Qualità', 'description': 'Miglioramento della qualità del lavoro'},
                {'name': 'Nuove Opportunità', 'description': 'Creazione di nuove opportunità'},
                {'name': 'Sviluppo Competenze', 'description': 'Sviluppo di nuove competenze'},
                {'name': 'Maggiore Creatività', 'description': 'Liberazione del potenziale creativo'},
                {'name': 'Analisi Dati Avanzata', 'description': 'Capacità di analisi dati più sofisticate'},
                {'name': 'Decisioni Informate', 'description': 'Decisioni basate su dati più completi'},
                {'name': 'Scalabilità', 'description': 'Possibilità di scalare le operazioni'},
                {'name': 'Competitività', 'description': 'Maggiore competitività sul mercato'},
                {'name': 'Soddisfazione Utente', 'description': 'Maggiore soddisfazione degli utenti finali'}
            ]
        },
        'Impatti Sociali AI': {
            'description': 'Impatti dell\'AI sulla società e comunità',
            'color': '#9b59b6',  # Viola
            'labels': [
                {'name': 'Equità Sociale', 'description': 'Impatti sull\'equità e giustizia sociale'},
                {'name': 'Digital Divide', 'description': 'Divario digitale e disuguaglianze'},
                {'name': 'Cambiamento Sociale', 'description': 'Trasformazioni sociali e culturali'},
                {'name': 'Inclusione', 'description': 'Promozione dell\'inclusività'},
                {'name': 'Democrazia', 'description': 'Impatti sui processi democratici'},
                {'name': 'Educazione Società', 'description': 'Trasformazione dei sistemi educativi'},
                {'name': 'Relazioni Umane', 'description': 'Cambiamenti nelle relazioni interpersonali'},
                {'name': 'Welfare Sociale', 'description': 'Impatti sul welfare e benessere sociale'}
            ]
        }
    }
    
    app = create_app()
    with app.app_context():
        print("Creazione categorie ed etichette specifiche per l'analisi dell'AI...")
        
        categories_created = 0
        labels_created = 0
        
        for cat_name, cat_data in ai_categories.items():
            # Verifica se la categoria esiste già
            existing_category = Category.query.filter_by(name=cat_name).first()
            
            if not existing_category:
                # Crea la categoria
                category = Category(
                    name=cat_name,
                    description=cat_data['description'],
                    color=cat_data['color'],
                    is_active=True
                )
                db.session.add(category)
                db.session.flush()  # Per ottenere l'ID
                categories_created += 1
                print(f"✓ Creata categoria: {cat_name}")
            else:
                category = existing_category
                print(f"- Categoria già esistente: {cat_name}")
            
            # Crea le etichette per questa categoria
            for label_data in cat_data['labels']:
                existing_label = Label.query.filter_by(name=label_data['name']).first()
                
                if not existing_label:
                    label = Label(
                        name=label_data['name'],
                        description=label_data['description'],
                        category_id=category.id,
                        color=cat_data['color']  # Usa il colore della categoria
                    )
                    db.session.add(label)
                    labels_created += 1
                    print(f"  ✓ Creata etichetta: {label_data['name']}")
                else:
                    print(f"  - Etichetta già esistente: {label_data['name']}")
        
        try:
            db.session.commit()
            print(f"\n✅ Creazione completata con successo!")
            print(f"Nuove categorie create: {categories_created}")
            print(f"Nuove etichette create: {labels_created}")
            
            # Mostra il riepilogo finale
            total_categories = Category.query.count()
            total_labels = Label.query.count()
            print(f"\nTotale categorie nel database: {total_categories}")
            print(f"Totale etichette nel database: {total_labels}")
            
            # Mostra le categorie AI
            print(f"\nCategorie AI create:")
            for cat_name in ai_categories.keys():
                cat = Category.query.filter_by(name=cat_name).first()
                if cat:
                    labels_count = Label.query.filter_by(category_id=cat.id).count()
                    print(f"  • {cat.name}: {labels_count} etichette ({cat.color})")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Errore durante la creazione: {e}")

if __name__ == '__main__':
    create_ai_categories_and_labels()
