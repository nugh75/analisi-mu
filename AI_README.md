# 🤖 Sistema di Etichettatura AI - Analisi MU

## Panoramica

Il sistema di etichettatura AI integra **Ollama** (locale) e **OpenRouter** (cloud) per automatizzare l'annotazione di testi, mantenendo il controllo umano attraverso un sistema di revisione.

## 🚀 Caratteristiche Principali

### Multi-Provider AI
- **Ollama**: Modelli AI locali per privacy e controllo completo
- **OpenRouter**: Accesso ai migliori modelli cloud (GPT-4, Claude, Gemini)

### Etichettatura Intelligente
- Analisi automatica di centinaia di testi in batch
- Suggerimenti con punteggio di confidenza
- Revisione umana per ogni suggerimento

### Gestione Modelli Avanzata
- Download e gestione modelli Ollama stile OpenWebUI
- Catalogo modelli OpenRouter (gratuiti e a pagamento)
- Monitoraggio utilizzo e costi

## 📋 Prerequisiti

### Per Ollama
- Server Ollama in esecuzione su `http://192.168.12.14:11345`
- Almeno un modello scaricato (es. `llama3`, `mistral`)

### Per OpenRouter
- Account OpenRouter attivo
- API Key valida
- Crediti sufficienti per modelli a pagamento

## 🛠 Installazione e Configurazione

### 1. Migrazione Database
```bash
# Esegui la migrazione per aggiungere le tabelle AI
python migrate_ai_database.py

# Verifica la migrazione
python migrate_ai_database.py --verify
```

### 2. Installazione Dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configurazione AI
1. Vai su **Amministrazione → Configurazione AI**
2. Crea una nuova configurazione:
   - **Ollama**: URL server + modello
   - **OpenRouter**: API key + modello
3. Testa la connessione
4. Attiva la configurazione

### 4. Test Integrazioni
```bash
# Test completo delle integrazioni
python test_ai_integration.py

# Per testare OpenRouter, imposta la variabile d'ambiente
export OPENROUTER_API_KEY="sk-or-..."
python test_ai_integration.py
```

## 🎯 Utilizzo

### Etichettatura Automatica

1. **Accedi a un file Excel** con domande da etichettare
2. **Clicca "Genera Etichette AI"** nel pannello AI
3. **Attendi l'elaborazione** (progress bar in tempo reale)
4. **Rivedi i suggerimenti** cliccando "Rivedi Suggerimenti"

### Revisione Suggerimenti

La pagina di revisione offre:
- **Vista dettagliata** di ogni suggerimento
- **Filtri** per confidenza, etichetta, data
- **Azioni in blocco** per accettare/rifiutare multiple annotazioni
- **Testo completo** espandibile per decisioni informate

### Gestione Modelli

#### Ollama
- **Lista modelli installati** con informazioni dettagliate
- **Scarica nuovi modelli** dal catalogo integrato
- **Elimina modelli** non utilizzati
- **Monitoraggio spazio** e performance

#### OpenRouter
- **Modelli gratuiti** sempre disponibili
- **Modelli premium** con pricing trasparente
- **Monitoraggio utilizzo** e costi in tempo reale

## 🔧 Configurazioni Avanzate

### Prompt di Sistema Personalizzato
```
Sei un assistente specializzato nell'etichettatura di testi educativi. 
Analizza ogni testo e assegna l'etichetta più appropriata dalla lista fornita. 
Considera il contesto educativo e sii coerente nelle tue scelte.
```

### Parametri di Generazione
- **Temperature** (0-2): Controllo creatività
  - 0.1-0.3: Conservativo, coerente
  - 0.7: Bilanciato (raccomandato)
  - 1.5-2.0: Creativo, variabile

- **Max Tokens** (100-4000): Lunghezza risposta
  - 500-1000: Ottimale per etichettatura
  - 1000+: Per analisi dettagliate

## 📊 Monitoraggio e Statistiche

### Dashboard AI
- Annotazioni totali generate
- Tasso di accettazione suggerimenti
- Performance per modello
- Utilizzo risorse

### Metriche di Qualità
- **Confidence Score**: Affidabilità predizione
- **Acceptance Rate**: Percentuale approvazioni umane
- **Time Savings**: Tempo risparmiato vs annotazione manuale

## 🔒 Sicurezza e Privacy

### Dati Locali (Ollama)
- Tutti i dati rimangono sul server locale
- Nessuna trasmissione esterna
- Controllo completo su modelli e configurazioni

### Dati Cloud (OpenRouter)
- Testi inviati ai provider esterni
- Conformità GDPR dei provider
- Logs e audit trail completi

### Utente AI
- Utente virtuale `ai_assistant` per tracciabilità
- Tutte le annotazioni AI sono marcate
- Storico completo delle revisioni umane

## 🚨 Risoluzione Problemi

### Errori Comuni

#### Ollama Non Connesso
```bash
# Verifica stato Ollama
curl http://192.168.12.14:11345/api/tags

# Riavvia Ollama se necessario
systemctl restart ollama
```

#### OpenRouter API Key Non Valida
- Verifica l'API key su https://openrouter.ai/keys
- Controlla i crediti disponibili
- Testa la connessione dalla configurazione AI

#### Modelli Non Trovati
- Ollama: Scarica modelli tramite l'interfaccia
- OpenRouter: Verifica disponibilità modello

### Performance

#### Ollama Lento
- Verifica risorse server (RAM, CPU)
- Usa modelli più piccoli (7B vs 70B)
- Riduci batch_size nella configurazione

#### Timeout OpenRouter
- Riduci max_tokens
- Aumenta timeout nelle chiamate API
- Verifica connettività internet

## 🔄 Aggiornamenti

### Aggiornamento Modelli OpenRouter
I modelli disponibili sono aggiornati automaticamente quando:
- Si carica la pagina modelli OpenRouter
- Si testa una configurazione
- Database viene re-sincronizzato

### Nuovi Modelli Ollama
- Nuovi modelli appaiono nel catalogo
- Download tramite interfaccia web
- Gestione automatica dipendenze

## 📈 Best Practices

### Prompt Engineering
1. **Sii specifico** nel prompt di sistema
2. **Includi esempi** di etichettature corrette
3. **Definisci il contesto** (educativo, ricerca, ecc.)
4. **Testa varianti** di prompt per ottimizzare

### Gestione Qualità
1. **Rivedi sempre** i primi batch di suggerimenti
2. **Monitora confidence scores** per identificare pattern
3. **Aggiorna prompt** basandoti sui feedback
4. **Combina AI + umano** per massima accuratezza

### Ottimizzazione Costi
1. **Usa modelli gratuiti** per test e sviluppo
2. **Modelli premium** solo per produzione
3. **Monitora utilizzo** OpenRouter regolarmente
4. **Ottimizza batch_size** per efficienza

## 🔗 Link Utili

- [Ollama Documentation](https://ollama.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Docs](https://openrouter.ai/docs)

## 📞 Supporto

Per problemi o domande:
1. Controlla i logs dell'applicazione
2. Usa il sistema di test integrato
3. Verifica configurazioni AI
4. Consulta la documentazione provider
