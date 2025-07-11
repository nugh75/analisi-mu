#!/usr/bin/env python3
"""
Migrazione per creare la tabella PromptTemplate e popolarla con i template di default
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from sqlalchemy import text
import json

def create_prompt_template_table():
    """Crea la tabella PromptTemplate"""
    try:
        # Crea la tabella
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                prompt_content TEXT NOT NULL,
                expected_labels JSON,
                placeholders JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Aggiungi colonne alla tabella CellAnnotation se non esistono
        try:
            db.session.execute(text("""
                ALTER TABLE cell_annotation 
                ADD COLUMN created_by_prompt_template INTEGER
            """))
        except:
            pass  # Colonna già esistente
            
        try:
            db.session.execute(text("""
                ALTER TABLE cell_annotation 
                ADD COLUMN ai_reasoning TEXT
            """))
        except:
            pass  # Colonna già esistente
        
        db.session.commit()
        print("✅ Tabella PromptTemplate creata con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore nella creazione della tabella: {str(e)}")
        db.session.rollback()
        return False

def populate_default_templates():
    """Popola la tabella con i template di default"""
    
    default_templates = [
        {
            "name": "Sentiment Analysis Educativo",
            "category": "Sentiment Analysis",
            "description": "Analizza il sentiment verso l'uso dell'AI nell'educazione",
            "prompt_content": """Analizza il sentiment di queste risposte riguardo all'uso dell'AI nell'educazione.

Domanda: {question}
File: {file_name}
Numero di risposte: {total_responses}

Risposte da analizzare:
{content}

Per ogni risposta, fornisci la classificazione in formato JSON:
{
  "annotations": [
    {
      "response_id": [ID_RISPOSTA],
      "response_text": "[primi 50 caratteri della risposta]",
      "labels": [
        {
          "name": "Sentiment_Positivo|Sentiment_Negativo|Sentiment_Neutro|Sentiment_Ambivalente",
          "confidence": [0.0-1.0],
          "reasoning": "Breve spiegazione della classificazione"
        }
      ]
    }
  ]
}

Etichette disponibili: Sentiment_Positivo, Sentiment_Negativo, Sentiment_Neutro, Sentiment_Ambivalente""",
            "expected_labels": ["Sentiment_Positivo", "Sentiment_Negativo", "Sentiment_Neutro", "Sentiment_Ambivalente"],
            "placeholders": ["content", "question", "file_name", "total_responses", "response_count"]
        },
        {
            "name": "Classificazione Utilizzo AI",
            "category": "Usage Patterns",
            "description": "Identifica i pattern di utilizzo dell'AI nelle risposte",
            "prompt_content": """Analizza i pattern di utilizzo dell'AI descritti in queste risposte alla domanda: {question}

Dataset: {file_name}
Risposte da analizzare ({total_responses}):
{content}

Per ogni risposta, identifica i pattern di utilizzo in formato JSON:
{
  "annotations": [
    {
      "response_id": [ID_RISPOSTA],
      "response_text": "[primi 50 caratteri]",
      "labels": [
        {
          "name": "Utilizzo_Ricerca|Utilizzo_Scrittura|Utilizzo_ProblemSolving|Utilizzo_Creativita|Utilizzo_Programmazione|Utilizzo_Traduzione|Utilizzo_Tutoring",
          "confidence": [0.0-1.0],
          "reasoning": "Motivazione della classificazione"
        }
      ]
    }
  ]
}

Etichette disponibili: Utilizzo_Ricerca, Utilizzo_Scrittura, Utilizzo_ProblemSolving, Utilizzo_Creativita, Utilizzo_Programmazione, Utilizzo_Traduzione, Utilizzo_Tutoring""",
            "expected_labels": ["Utilizzo_Ricerca", "Utilizzo_Scrittura", "Utilizzo_ProblemSolving", "Utilizzo_Creativita", "Utilizzo_Programmazione", "Utilizzo_Traduzione", "Utilizzo_Tutoring"],
            "placeholders": ["content", "question", "file_name", "total_responses", "response_count"]
        },
        {
            "name": "Analisi Benefici AI",
            "category": "Benefits Analysis",
            "description": "Identifica i benefici dell'AI nell'educazione menzionati nelle risposte",
            "prompt_content": """Identifica i benefici dell'AI nell'educazione menzionati in queste risposte.

Contesto: {question}
File: {file_name}
Risposte ({response_count}):
{content}

Per ogni risposta, identifica i benefici in formato JSON:
{
  "annotations": [
    {
      "response_id": [ID_RISPOSTA],
      "response_text": "[primi 50 caratteri]",
      "labels": [
        {
          "name": "Benefici_Personalizzazione|Benefici_Accessibilita|Benefici_Efficienza|Benefici_Motivazione|Benefici_FeedbackIstantaneo|Benefici_Inclusivita",
          "confidence": [0.0-1.0],
          "reasoning": "Motivazione della classificazione"
        }
      ]
    }
  ]
}

Etichette disponibili: Benefici_Personalizzazione, Benefici_Accessibilita, Benefici_Efficienza, Benefici_Motivazione, Benefici_FeedbackIstantaneo, Benefici_Inclusivita""",
            "expected_labels": ["Benefici_Personalizzazione", "Benefici_Accessibilita", "Benefici_Efficienza", "Benefici_Motivazione", "Benefici_FeedbackIstantaneo", "Benefici_Inclusivita"],
            "placeholders": ["content", "question", "file_name", "total_responses", "response_count"]
        },
        {
            "name": "Identificazione Rischi e Preoccupazioni",
            "category": "Ethical Concerns",
            "description": "Identifica rischi e preoccupazioni etiche sull'AI nell'educazione",
            "prompt_content": """Identifica le preoccupazioni etiche e i rischi sull'AI nell'educazione presenti in queste risposte.

Domanda: {question}
File: {file_name}
Numero di risposte: {total_responses}

Risposte:
{content}

Per ogni risposta, identifica rischi e preoccupazioni in formato JSON:
{
  "annotations": [
    {
      "response_id": [ID_RISPOSTA],
      "response_text": "[primi 50 caratteri]",
      "labels": [
        {
          "name": "Rischi_Dipendenza|Rischi_Plagio|Rischi_Perdita_Competenze|Rischi_Privacy|Rischi_Bias|Rischi_Superficialita",
          "confidence": [0.0-1.0],
          "reasoning": "Motivazione della classificazione"
        }
      ]
    }
  ]
}

Etichette disponibili: Rischi_Dipendenza, Rischi_Plagio, Rischi_Perdita_Competenze, Rischi_Privacy, Rischi_Bias, Rischi_Superficialita""",
            "expected_labels": ["Rischi_Dipendenza", "Rischi_Plagio", "Rischi_Perdita_Competenze", "Rischi_Privacy", "Rischi_Bias", "Rischi_Superficialita"],
            "placeholders": ["content", "question", "file_name", "total_responses", "response_count"]
        },
        {
            "name": "Valutazione Esperienza Educativa",
            "category": "Educational Experience",
            "description": "Valuta l'esperienza educativa con strumenti AI",
            "prompt_content": """Valuta l'esperienza educativa con strumenti AI descritta in queste risposte.

Contesto: {question}
File: {file_name}
Risposte da analizzare ({response_count}):
{content}

Per ogni risposta, valuta l'esperienza educativa in formato JSON:
{
  "annotations": [
    {
      "response_id": [ID_RISPOSTA],
      "response_text": "[primi 50 caratteri]",
      "labels": [
        {
          "name": "Esperienza_Apprendimento_Migliorato|Esperienza_Ritenzione_Informazioni|Esperienza_Applicazione_Pratica|Esperienza_Pensiero_Critico|Esperienza_Collaborazione|Esperienza_Autonomia",
          "confidence": [0.0-1.0],
          "reasoning": "Motivazione della classificazione"
        }
      ]
    }
  ]
}

Etichette disponibili: Esperienza_Apprendimento_Migliorato, Esperienza_Ritenzione_Informazioni, Esperienza_Applicazione_Pratica, Esperienza_Pensiero_Critico, Esperienza_Collaborazione, Esperienza_Autonomia""",
            "expected_labels": ["Esperienza_Apprendimento_Migliorato", "Esperienza_Ritenzione_Informazioni", "Esperienza_Applicazione_Pratica", "Esperienza_Pensiero_Critico", "Esperienza_Collaborazione", "Esperienza_Autonomia"],
            "placeholders": ["content", "question", "file_name", "total_responses", "response_count"]
        },
        {
            "name": "Analisi Prospettive Future",
            "category": "Future Perspectives",
            "description": "Analizza le prospettive future sull'AI nell'educazione",
            "prompt_content": """Analizza le prospettive future sull'AI nell'educazione espresse in queste risposte.

Domanda: {question}
File: {file_name}
Risposte ({total_responses}):
{content}

Per ogni risposta, analizza le prospettive future in formato JSON:
{
  "annotations": [
    {
      "response_id": [ID_RISPOSTA],
      "response_text": "[primi 50 caratteri]",
      "labels": [
        {
          "name": "Prospettive_Ottimista|Prospettive_Pessimista|Prospettive_Realista|Prospettive_Visionario|Prospettive_Conservatore|Prospettive_Progressista",
          "confidence": [0.0-1.0],
          "reasoning": "Motivazione della classificazione"
        }
      ]
    }
  ]
}

Etichette disponibili: Prospettive_Ottimista, Prospettive_Pessimista, Prospettive_Realista, Prospettive_Visionario, Prospettive_Conservatore, Prospettive_Progressista""",
            "expected_labels": ["Prospettive_Ottimista", "Prospettive_Pessimista", "Prospettive_Realista", "Prospettive_Visionario", "Prospettive_Conservatore", "Prospettive_Progressista"],
            "placeholders": ["content", "question", "file_name", "total_responses", "response_count"]
        }
    ]
    
    try:
        # Controlla se ci sono già template
        existing_count = db.session.execute(text("SELECT COUNT(*) FROM prompt_template")).scalar()
        if existing_count > 0:
            print(f"ℹ️  Trovati {existing_count} template esistenti. Aggiungo solo nuovi template.")
        
        # Inserisci i template
        for template in default_templates:
            # Controlla se esiste già
            existing = db.session.execute(text(
                "SELECT id FROM prompt_template WHERE name = :name"
            ), {"name": template["name"]}).first()
            
            if not existing:
                db.session.execute(text("""
                    INSERT INTO prompt_template 
                    (name, category, description, prompt_content, expected_labels, placeholders, is_active)
                    VALUES (:name, :category, :description, :prompt_content, :expected_labels, :placeholders, :is_active)
                """), {
                    "name": template["name"],
                    "category": template["category"],
                    "description": template["description"],
                    "prompt_content": template["prompt_content"],
                    "expected_labels": json.dumps(template["expected_labels"]),
                    "placeholders": json.dumps(template["placeholders"]),
                    "is_active": True
                })
                print(f"✅ Template '{template['name']}' aggiunto")
            else:
                print(f"ℹ️  Template '{template['name']}' già esistente")
        
        db.session.commit()
        print("✅ Template di default popolati con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore nel popolare i template: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Esegue la migrazione completa"""
    print("🚀 Avvio migrazione PromptTemplate...")
    
    app = create_app()
    with app.app_context():
        # Crea la tabella
        if create_prompt_template_table():
            # Popola con i template di default
            if populate_default_templates():
                print("🎉 Migrazione completata con successo!")
                
                # Mostra sommario
                count = db.session.execute(text("SELECT COUNT(*) FROM prompt_template")).scalar()
                print(f"\n📊 Sommario:")
                print(f"   - Template totali: {count}")
                
                # Mostra categorie
                categories = db.session.execute(text(
                    "SELECT category, COUNT(*) FROM prompt_template GROUP BY category"
                )).fetchall()
                
                print(f"   - Categorie:")
                for cat, count in categories:
                    print(f"     * {cat}: {count} template")
                    
            else:
                print("❌ Errore nel popolare i template")
        else:
            print("❌ Errore nella creazione della tabella")

if __name__ == "__main__":
    main()
