#!/bin/bash
# Script di inizializzazione per permessi Docker

# Assicura che le directory esistano e abbiano i permessi corretti
mkdir -p /app/instance /app/uploads /app/backups

# Fix permessi per i volumi montati
if [ -w /app/instance ]; then
    echo "✅ Directory instance scrivibile"
else
    echo "❌ Directory instance non scrivibile, tentativo fix..."
    chmod 777 /app/instance
fi

if [ -w /app/uploads ]; then
    echo "✅ Directory uploads scrivibile"
else
    echo "❌ Directory uploads non scrivibile, tentativo fix..."
    chmod 777 /app/uploads
fi

if [ -w /app/backups ]; then
    echo "✅ Directory backups scrivibile"
else
    echo "❌ Directory backups non scrivibile, tentativo fix..."
    chmod 777 /app/backups
fi

# Verifica che il database sia scrivibile se esiste
if [ -f /app/instance/analisi_mu.db ]; then
    if [ -w /app/instance/analisi_mu.db ]; then
        echo "✅ Database esistente e scrivibile"
    else
        echo "❌ Database esistente ma non scrivibile, tentativo fix..."
        chmod 666 /app/instance/analisi_mu.db
    fi
fi

echo "🚀 Avvio applicazione Flask..."
exec python app.py
