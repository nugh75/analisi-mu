#!/bin/bash
# Script per configurare l'ambiente virtuale e installare le dipendenze

echo "🔧 Configurazione ambiente virtuale per Analisi MU AI"
echo "================================================="

# Controlla se Python 3 è disponibile
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato. Installalo prima di continuare."
    exit 1
fi

echo "✅ Python 3 trovato: $(python3 --version)"

# Crea virtual environment se non esiste
if [ ! -d "venv" ]; then
    echo "📦 Creazione virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment creato"
    else
        echo "❌ Errore nella creazione del virtual environment"
        exit 1
    fi
else
    echo "✅ Virtual environment già esistente"
fi

# Attiva virtual environment
echo "🔄 Attivazione virtual environment..."
source venv/bin/activate

if [ $? -eq 0 ]; then
    echo "✅ Virtual environment attivato"
else
    echo "❌ Errore nell'attivazione del virtual environment"
    exit 1
fi

# Aggiorna pip
echo "⬆️  Aggiornamento pip..."
pip install --upgrade pip

# Installa dipendenze
echo "📚 Installazione dipendenze..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dipendenze installate con successo"
else
    echo "❌ Errore nell'installazione delle dipendenze"
    exit 1
fi

# Esegui migrazione AI
echo "🤖 Esecuzione migrazione database AI..."
python migrate_ai_database.py

if [ $? -eq 0 ]; then
    echo "✅ Migrazione AI completata"
else
    echo "❌ Errore nella migrazione AI"
    exit 1
fi

echo ""
echo "🎉 Setup completato con successo!"
echo ""
echo "📋 Prossimi passi:"
echo "1. Attiva il virtual environment: source venv/bin/activate"
echo "2. Avvia l'applicazione: python app.py"
echo "3. Vai su /admin/ai-config per configurare l'AI"
echo ""
echo "🧪 Per testare le integrazioni AI:"
echo "   python test_ai_integration.py"
echo ""
echo "📖 Leggi AI_README.md per la documentazione completa"
