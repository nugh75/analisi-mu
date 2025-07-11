# Come Testare i Miglioramenti AI

## Test Rapido Sistema AI

### 1. Test Configurazione e Template

```bash
# Testa i template migliorati
python test_ai_improvements.py

# Testa endpoint AI (richiede server attivo)
python test_ai_endpoints_quick.py
```

### 2. Test Interfaccia Web

1. **Avvia il server**:
   ```bash
   python app.py
   ```

2. **Vai alla pagina di un quesito**:
   - Naviga su un file Excel caricato
   - Vai alla sezione "Assistente AI per Etichettatura"

3. **Testa le nuove funzionalità**:
   - **Template AI**: Prova a cambiare tra "Standard Quesiti", "Analisi Commenti", "Analisi Competenze"
   - **Prompt Preview**: Osserva come cambia il prompt generato in base al template
   - **Categorie**: Seleziona categorie specifiche e vedi come il prompt si adatta
   - **Stato AI**: Verifica che mostri correttamente "OLLAMA (devstral:24b)"

## Funzionalità da Testare

### ✅ Template Migliorati
- [ ] Cambio template aggiorna automaticamente il prompt
- [ ] Template "Standard Quesiti" mostra istruzioni specifiche per quesiti
- [ ] Template "Analisi Commenti" mostra istruzioni per feedback
- [ ] Template "Analisi Competenze" mostra istruzioni per competenze

### ✅ Prompt Generazione
- [ ] Prompt mostra etichette organizzate per categoria
- [ ] Prompt include informazioni sull'utilizzo delle etichette
- [ ] Prompt numera progressivamente i testi da etichettare
- [ ] Prompt include istruzioni precise per formato JSON

### ✅ Gestione Errori
- [ ] Messaggio chiaro se nessuna etichetta attiva
- [ ] Messaggio informativo se tutte le celle sono già annotate
- [ ] Validazione parametri (file_id, batch_size, etc.)

### ✅ Interfaccia Migliorata
- [ ] Caricamento dinamico dei template disponibili
- [ ] Feedback visivo durante generazione prompt
- [ ] Statistiche mostrate nel prompt preview

## Test di Generazione AI

### Prerequisiti
- Configurazione AI attiva (Ollama o OpenRouter)
- Almeno un file Excel caricato con celle non annotate
- Etichette attive nel sistema

### Procedura Test
1. **Seleziona Template**: Scegli "Standard Quesiti" per quesiti generali
2. **Modalità**: Lascia "Solo nuove" per annotare celle non etichettate
3. **Categorie**: Seleziona 2-3 categorie specifiche (opzionale)
4. **Genera Prompt**: Controlla che il prompt sia ben strutturato
5. **Genera Etichette**: Clicca "Genera Etichette AI"
6. **Rivedi Risultati**: Vai a "Rivedi Suggerimenti" per vedere le annotazioni generate

## Verifica Qualità Prompt

Il prompt generato dovrebbe contenere:

```
ISTRUZIONI SPECIFICHE:
1. Analizza il contenuto di ogni testo (quesito, domanda o risposta)
2. Identifica l'argomento principale, il livello di difficoltà e il tipo di competenza richiesta
...

ETICHETTE DISPONIBILI (sempre aggiornate dal sistema):

=== Prospettiva ===
• Docente (usata 45 volte)
• Studente (usata 23 volte)
...

TESTI DA ETICHETTARE (5 elementi):
[0] Qual è la capitale d'Italia?

[1] Calcola l'area di un triangolo...

FORMATO RISPOSTA OBBLIGATORIO:
[{"index": 0, "label": "NomeEsattoDallaLista", "confidence": 0.95}]
```

## Test Parsing Risposta AI

Per testare il parsing robusto, simula risposte AI nei formati:

1. **JSON Standard**: `[{"index": 0, "label": "Geografia", "confidence": 0.95}]`
2. **JSON in Code Block**: 
   ```
   ```json
   [{"index": 0, "label": "Geografia", "confidence": 0.95}]
   ```
3. **JSON con Testo Extra**: `Ecco la risposta: [{"index": 0, "label": "Geografia", "confidence": 0.95}]`
4. **Oggetto Singolo**: `{"index": 0, "label": "Geografia", "confidence": 0.95}`

## Debugging

### Log da Controllare
- Console browser per errori JavaScript
- Log server Python per errori backend
- Network tab per verificare chiamate API

### Endpoint di Debug
- `GET /ai/config/current` - Verifica configurazione attiva
- `GET /ai/validate-configuration` - Controlla setup completo
- `GET /ai/templates/available` - Lista template disponibili
- `POST /ai/prompt/preview` - Testa generazione prompt

### Problemi Comuni
1. **"Nessuna configurazione AI attiva"**: Configura Ollama o OpenRouter in admin
2. **"Nessuna etichetta attiva"**: Verifica che ci siano etichette non disabilitate
3. **Prompt vuoto**: Controlla che ci siano celle non annotate nel file
4. **Errore template**: Verifica che template_id sia valido (1, 2, o 3)
