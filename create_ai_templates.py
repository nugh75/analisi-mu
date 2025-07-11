#!/usr/bin/env python3
"""
Script per creare i template di prompt AI nel database
"""

from app import create_app
from models import db, PromptTemplate
from datetime import datetime

# Template di prompt definiti
TEMPLATES = [
    {
        'name': 'Sentiment Analysis Educativo',
        'category': 'Sentiment Analysis',
        'description': 'Analizza il sentiment delle risposte rispetto all\'uso dell\'AI in ambito educativo',
        'template_text': '''Analizza il sentiment della seguente risposta riguardo all'uso dell'intelligenza artificiale in ambito educativo.

TESTO DA ANALIZZARE:
{text_content}

ETICHETTE DISPONIBILI:
{labels}

ISTRUZIONI:
1. Leggi attentamente il testo
2. Identifica l'atteggiamento generale verso l'AI (positivo, negativo, neutro, ambivalente)
3. Considera il contesto educativo
4. Seleziona l'etichetta più appropriata dalle opzioni disponibili

Rispondi solo con il nome dell'etichetta più appropriata.'''
    },
    {
        'name': 'Classificazione Utilizzo AI',
        'category': 'Usage Patterns',
        'description': 'Classifica i diversi modi di utilizzo dell\'AI menzionati nelle risposte',
        'template_text': '''Classifica il tipo di utilizzo dell'intelligenza artificiale descritto nella seguente risposta.

TESTO DA ANALIZZARE:
{text_content}

ETICHETTE DISPONIBILI:
{labels}

ISTRUZIONI:
1. Identifica come viene utilizzata l'AI nel testo
2. Considera i diversi ambiti di applicazione (ricerca, scrittura, problem solving, creatività, etc.)
3. Seleziona l'etichetta che meglio descrive l'uso principale

Rispondi solo con il nome dell'etichetta più appropriata.'''
    },
    {
        'name': 'Analisi Benefici AI',
        'category': 'Benefits Analysis',
        'description': 'Identifica i benefici dell\'AI menzionati nelle risposte',
        'template_text': '''Identifica i principali benefici dell'intelligenza artificiale menzionati nella seguente risposta.

TESTO DA ANALIZZARE:
{text_content}

ETICHETTE DISPONIBILI:
{labels}

ISTRUZIONI:
1. Cerca menzioni di vantaggi, benefici o aspetti positivi dell'AI
2. Focalizzati sui benefici specifici come personalizzazione, efficienza, accessibilità, etc.
3. Seleziona l'etichetta che meglio rappresenta il beneficio principale discusso

Rispondi solo con il nome dell'etichetta più appropriata.'''
    },
    {
        'name': 'Identificazione Rischi e Preoccupazioni',
        'category': 'Ethical Concerns',
        'description': 'Identifica rischi, preoccupazioni etiche e problematiche relative all\'AI',
        'template_text': '''Identifica i principali rischi o preoccupazioni riguardo l'intelligenza artificiale menzionati nella seguente risposta.

TESTO DA ANALIZZARE:
{text_content}

ETICHETTE DISPONIBILI:
{labels}

ISTRUZIONI:
1. Cerca menzioni di rischi, preoccupazioni, problemi o aspetti negativi dell'AI
2. Considera aspetti etici, dipendenza, privacy, bias, perdita di competenze, etc.
3. Seleziona l'etichetta che meglio rappresenta la preoccupazione principale

Rispondi solo con il nome dell'etichetta più appropriata.'''
    },
    {
        'name': 'Valutazione Esperienza Educativa',
        'category': 'Educational Experience',
        'description': 'Valuta l\'impatto dell\'AI sull\'esperienza educativa complessiva',
        'template_text': '''Valuta l'impatto dell'intelligenza artificiale sull'esperienza educativa descritto nella seguente risposta.

TESTO DA ANALIZZARE:
{text_content}

ETICHETTE DISPONIBILI:
{labels}

ISTRUZIONI:
1. Analizza come l'AI influenza l'apprendimento e l'esperienza educativa
2. Considera aspetti come motivazione, engagement, qualità dell'apprendimento
3. Valuta se l'impatto è positivo, negativo o misto
4. Seleziona l'etichetta più appropriata

Rispondi solo con il nome dell'etichetta più appropriata.'''
    },
    {
        'name': 'Analisi Prospettive Future',
        'category': 'Future Perspectives',
        'description': 'Analizza le prospettive future e le aspettative riguardo l\'AI in educazione',
        'template_text': '''Analizza le prospettive future riguardo l'intelligenza artificiale in educazione menzionate nella seguente risposta.

TESTO DA ANALIZZARE:
{text_content}

ETICHETTE DISPONIBILI:
{labels}

ISTRUZIONI:
1. Cerca riferimenti al futuro dell'AI in educazione
2. Identifica aspettative, previsioni, speranze o timori futuri
3. Considera l'evoluzione prevista della tecnologia e del suo uso
4. Seleziona l'etichetta che meglio rappresenta la prospettiva futura espressa

Rispondi solo con il nome dell'etichetta più appropriata.'''
    }
]

def create_prompt_templates():
    """Crea i template nel database"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Creazione template di prompt AI...")
        
        # Controlla se i template esistono già
        existing_count = PromptTemplate.query.count()
        print(f"📊 Template esistenti: {existing_count}")
        
        if existing_count > 0:
            response = input("❓ Esistono già dei template. Vuoi sovrascriverli? (s/n): ")
            if response.lower() != 's':
                print("❌ Operazione annullata")
                return
            
            # Elimina i template esistenti
            PromptTemplate.query.delete()
            db.session.commit()
            print("🗑️ Template esistenti eliminati")
        
        # Crea i nuovi template
        created_count = 0
        for template_data in TEMPLATES:
            try:
                template = PromptTemplate(
                    name=template_data['name'],
                    category=template_data['category'],
                    description=template_data['description'],
                    template_text=template_data['template_text'],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(template)
                created_count += 1
                print(f"✅ Creato: {template.name} ({template.category})")
                
            except Exception as e:
                print(f"❌ Errore nella creazione di {template_data['name']}: {e}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
            print(f"\n🎉 Creati {created_count} template con successo!")
            
            # Verifica finale
            total_templates = PromptTemplate.query.count()
            active_templates = PromptTemplate.query.filter_by(is_active=True).count()
            
            print(f"📈 Totale template nel database: {total_templates}")
            print(f"🟢 Template attivi: {active_templates}")
            
            print("\n📋 Template creati:")
            templates = PromptTemplate.query.order_by(PromptTemplate.category, PromptTemplate.name).all()
            for t in templates:
                status = "🟢" if t.is_active else "🔴"
                print(f"   {status} {t.name} ({t.category})")
            
        except Exception as e:
            print(f"❌ Errore nel commit finale: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_prompt_templates()
