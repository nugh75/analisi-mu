#!/usr/bin/env python3

# Test semplice del classificatore
from question_classifier import QuestionClassifier, QuestionType

def main():
    classifier = QuestionClassifier()
    
    print("=== TEST CLASSIFICATORE DOMANDE ===\n")
    
    # Test cases
    tests = [
        ("Descrivi la tua esperienza con l'AI", "È stata molto positiva perché mi ha aiutato nel lavoro"),
        ("Hai mai usato ChatGPT? Sì/No", "Sì"),
        ("Età:", "25"),
        ("Quanto sei soddisfatto? (scala 1-10)", "8"),
        ("Cosa pensi dell'intelligenza artificiale?", "Penso che sia uno strumento utile ma va usato con attenzione"),
        ("Seleziona: a) Utile b) Inutile", "a) Utile"),
        ("Come utilizzi l'AI nel tuo lavoro quotidiano?", "La uso per scrivere email e fare ricerche")
    ]
    
    for question, response in tests:
        question_type, confidence = classifier.classify_question(question, response)
        should_annotate = classifier.should_annotate(question, response)
        
        print(f"Domanda: {question}")
        print(f"Risposta: {response}")
        print(f"Tipo: {question_type.value}")
        print(f"Confidenza: {confidence:.2f}")
        print(f"Deve essere annotata: {'SÌ' if should_annotate else 'NO'}")
        print("-" * 50)

if __name__ == "__main__":
    main()
