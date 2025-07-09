#!/bin/bash

# Script di setup per l'applicazione Analisi MU
# Questo script crea l'ambiente virtuale, installa le dipendenze e prepara l'applicazione

echo "🚀 Setup dell'applicazione Analisi MU"
echo "===================================="

# Verifica che Python sia installato
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non è installato. Installa Python 3 prima di continuare."
    exit 1
fi

echo "✓ Python 3 trovato: $(python3 --version)"

# Crea ambiente virtuale se non esiste
if [ ! -d "venv" ]; then
    echo "📦 Creazione dell'ambiente virtuale..."
    python3 -m venv venv
    echo "✓ Ambiente virtuale creato"
else
    echo "✓ Ambiente virtuale già esistente"
fi

# Attiva l'ambiente virtuale
echo "🔄 Attivazione dell'ambiente virtuale..."
source venv/bin/activate

# Aggiorna pip
echo "⬆️  Aggiornamento di pip..."
pip install --upgrade pip

# Installa le dipendenze
echo "📋 Installazione delle dipendenze..."
pip install -r requirements.txt

# Crea il file .env se non esiste
if [ ! -f ".env" ]; then
    echo "⚙️  Creazione del file .env..."
    cp .env.example .env
    echo "✓ File .env creato da .env.example"
    echo "📝 Modifica il file .env secondo le tue necessità"
else
    echo "✓ File .env già esistente"
fi

# Crea la cartella uploads se non esiste
if [ ! -d "uploads" ]; then
    echo "📁 Creazione cartella uploads..."
    mkdir uploads
    echo "✓ Cartella uploads creata"
else
    echo "✓ Cartella uploads già esistente"
fi

# Inizializza il database
echo "🗄️  Inizializzazione del database..."
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    db.create_all()
    print('✓ Database inizializzato')
"

echo ""
echo "🎉 Setup completato con successo!"
echo ""
echo "Per avviare l'applicazione:"
echo "1. Attiva l'ambiente virtuale: source venv/bin/activate"
echo "2. Avvia l'applicazione: python app.py"
echo "3. Apri il browser su: http://localhost:5000"
echo ""
echo "Account admin predefinito:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "📖 Consulta il README.md per maggiori informazioni"
