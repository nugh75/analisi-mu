#!/usr/bin/env python3
"""
Script per popolare il database con i template AI iniziali
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, AIPromptTemplate

def create_initial_templates():
    """Crea i template AI iniziali se il database è vuoto"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verifica se ci sono già template
            existing_count = AIPromptTemplate.query.count()
            
            if existing_count > 0:
                print(f"ℹ️  Trovati {existing_count} template esistenti nel database")
                return True
            
            print("🔧 Creazione template AI iniziali...")
            
            # Template iniziali basati sui prompt hardcoded
            initial_templates = [
                {
                    'id': 1,
                    'name': 'Sentiment Analysis Educativo',
                    'category': 'Sentiment Analysis',
                    'description': 'Analizza il sentiment di feedback e commenti in contesti educativi, identificando emozioni positive, negative e neutre.',
                    'base_prompt': '''Sei un esperto analista di sentiment specializzato in contesti educativi.

Analizza i seguenti testi e identifica il sentiment generale e le emozioni specifiche.

OBIETTIVI:
1. Identifica il sentiment principale (positivo, negativo, neutro)
2. Rileva emozioni specifiche (soddisfazione, frustrazione, curiosità, confusione)
3. Considera il contesto educativo e formativo
4. Assegna 1-3 etichette più appropriate per ogni testo

FORMATO RISPOSTA:
Per ogni testo, rispondi con: "Testo N: [etichetta1, etichetta2, etichetta3]"

IMPORTANTE: Usa SOLO etichette dalla lista fornita qui sotto.'''
                },
                {
                    'id': 2,
                    'name': 'Classificazione Utilizzo AI',
                    'category': 'Usage Patterns',
                    'description': 'Classifica come gli utenti utilizzano strumenti AI, identificando pattern di uso, frequenza e modalità di interazione.',
                    'base_prompt': '''Sei un esperto nell'analisi dei pattern di utilizzo dell'Intelligenza Artificiale.

Analizza i seguenti testi per identificare come vengono utilizzati gli strumenti AI.

OBIETTIVI:
1. Identifica il tipo di utilizzo (studio, lavoro, ricerca, svago)
2. Rileva la frequenza d'uso (occasionale, regolare, intensivo)
3. Classifica le modalità di interazione
4. Assegna le etichette più appropriate

FORMATO RISPOSTA:
Per ogni testo, rispondi con: "Testo N: [etichetta1, etichetta2]"

IMPORTANTE: Usa SOLO etichette dalla lista fornita qui sotto.'''
                },
                {
                    'id': 3,
                    'name': 'Analisi Benefici AI',
                    'category': 'Benefits Analysis',
                    'description': 'Identifica i benefici e vantaggi che gli utenti riportano dall\'utilizzo di strumenti AI in ambito educativo e professionale.',
                    'base_prompt': '''Sei un analista specializzato nell'identificazione dei benefici dell'Intelligenza Artificiale.

Analizza i seguenti testi per identificare i benefici e vantaggi riportati dagli utenti.

OBIETTIVI:
1. Identifica benefici diretti (risparmio tempo, miglior comprensione, efficienza)
2. Rileva benefici indiretti (motivazione, creatività, problem-solving)
3. Classifica l'impatto sui risultati educativi o professionali
4. Assegna le etichette più appropriate

FORMATO RISPOSTA:
Per ogni testo, rispondi con: "Testo N: [etichetta1, etichetta2]"

IMPORTANTE: Usa SOLO etichette dalla lista fornita qui sotto.'''
                },
                {
                    'id': 4,
                    'name': 'Identificazione Rischi e Preoccupazioni',
                    'category': 'Ethical Concerns',
                    'description': 'Identifica preoccupazioni etiche, rischi e problematiche legate all\'uso dell\'AI, come privacy, dipendenza e bias.',
                    'base_prompt': '''Sei un esperto in etica dell'AI e analisi dei rischi tecnologici.

Analizza i seguenti testi per identificare preoccupazioni, rischi e problematiche etiche.

OBIETTIVI:
1. Identifica preoccupazioni sulla privacy e sicurezza dei dati
2. Rileva timori su dipendenza e over-reliance
3. Classifica problemi di bias, equità e discriminazione
4. Identifica altre problematiche etiche o sociali
5. Assegna le etichette più appropriate

FORMATO RISPOSTA:
Per ogni testo, rispondi con: "Testo N: [etichetta1, etichetta2]"

IMPORTANTE: Usa SOLO etichette dalla lista fornita qui sotto.'''
                },
                {
                    'id': 5,
                    'name': 'Valutazione Esperienza Educativa',
                    'category': 'Educational Experience',
                    'description': 'Valuta l\'impatto dell\'AI sull\'esperienza educativa, analizzando apprendimento, coinvolgimento e risultati formativi.',
                    'base_prompt': '''Sei un esperto in tecnologie educative e valutazione dell'apprendimento.

Analizza i seguenti testi per valutare l'impatto dell'AI sull'esperienza educativa.

OBIETTIVI:
1. Valuta l'impatto sull'apprendimento e la comprensione
2. Identifica cambiamenti nel coinvolgimento e motivazione
3. Analizza l'effetto sui metodi di studio e ricerca
4. Classifica i risultati formativi e educativi
5. Assegna le etichette più appropriate

FORMATO RISPOSTA:
Per ogni testo, rispondi con: "Testo N: [etichetta1, etichetta2]"

IMPORTANTE: Usa SOLO etichette dalla lista fornita qui sotto.'''
                },
                {
                    'id': 6,
                    'name': 'Analisi Prospettive Future',
                    'category': 'Future Perspectives',
                    'description': 'Analizza visioni, aspettative e previsioni sul futuro dell\'AI nell\'educazione e nel lavoro.',
                    'base_prompt': '''Sei un futurologo specializzato nell'evoluzione dell'Intelligenza Artificiale.

Analizza i seguenti testi per identificare prospettive e aspettative sul futuro dell'AI.

OBIETTIVI:
1. Identifica visioni ottimistiche vs pessimistiche
2. Rileva aspettative su sviluppi tecnologici futuri
3. Classifica previsioni su impatti sociali ed educativi
4. Analizza piani e intenzioni d'uso future
5. Assegna le etichette più appropriate

FORMATO RISPOSTA:
Per ogni testo, rispondi con: "Testo N: [etichetta1, etichetta2]"

IMPORTANTE: Usa SOLO etichette dalla lista fornita qui sotto.'''
                }
            ]
            
            # Crea i template
            created_count = 0
            for template_data in initial_templates:
                template = AIPromptTemplate(
                    name=template_data['name'],
                    category=template_data['category'],
                    description=template_data['description'],
                    base_prompt=template_data['base_prompt'],
                    is_active=True
                )
                
                db.session.add(template)
                created_count += 1
                print(f"  ✅ Creato: {template_data['name']} ({template_data['category']})")
            
            db.session.commit()
            print(f"\n🎉 Creati {created_count} template AI con successo!")
            
            # Verifica finale
            final_count = AIPromptTemplate.query.count()
            print(f"📊 Template totali nel database: {final_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la creazione dei template: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 Inizializzazione template AI...")
    success = create_initial_templates()
    
    if success:
        print("\n🎉 Inizializzazione completata!")
        print("📱 Puoi ora gestire i template da: /admin/templates")
    else:
        print("\n💥 Inizializzazione fallita. Controlla i log per i dettagli.")
        sys.exit(1)
