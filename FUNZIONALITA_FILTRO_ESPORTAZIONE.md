# Funzionalità di Filtro e Esportazione Annotazioni

## Panoramica

Sono state implementate nuove funzionalità per la pagina delle annotazioni dei documenti di testo (`/text-documents/annotations/<document_id>`):

1. **Filtro per Categoria** - Possibilità di filtrare le annotazioni per categoria di etichette
2. **Esportazione Multi-formato** - Esportazione delle annotazioni in PDF, Word e LaTeX

## Filtro per Categoria

### Funzionalità
- Nella sezione filtri della pagina annotazioni è stato aggiunto un nuovo campo "Filtra per Categoria"
- Supporta selezione multipla (tenere premuto Ctrl/Cmd per selezionare più categorie)
- Il filtro si applica a livello di server, modificando l'URL con i parametri delle categorie selezionate
- Viene mostrato un badge informativo quando sono attivi dei filtri per categoria

### Utilizzo
1. Aprire la pagina annotazioni di un documento
2. Nella sezione "Filtri", utilizzare il campo "Filtra per Categoria"
3. Selezionare una o più categorie
4. Cliccare "Applica Filtro Categoria"
5. Le annotazioni vengono filtrate e mostrate solo quelle delle categorie selezionate

## Esportazione Annotazioni

### Formati Supportati
- **PDF**: Documento formattato con statistiche, informazioni e lista completa delle annotazioni
- **Word (DOCX)**: Documento Microsoft Word con tabelle e formattazione
- **LaTeX**: File TeX per compilazione con LaTeX, ideale per documenti accademici

### Funzionalità
- Esportazione rispetta i filtri di categoria attivi
- Include informazioni complete del documento
- Statistiche per categoria
- Lista dettagliata delle annotazioni raggruppate per categoria
- Metadati di esportazione (data, utente, filtri applicati)

### Contenuto Esportato
Ogni formato include:
1. **Informazioni Documento**:
   - Nome file originale
   - Tipo documento
   - Data di creazione
   - Numero totale annotazioni
   - Data di esportazione
   - Categorie filtrate (se applicabile)

2. **Statistiche per Categoria**:
   - Conteggio annotazioni per ogni categoria
   - Tabella riassuntiva

3. **Elenco Annotazioni**:
   - Raggruppate per categoria
   - Testo annotato
   - Etichetta applicata
   - Posizione nel documento
   - Utente che ha creato l'annotazione
   - Data di creazione

### Utilizzo
1. Aprire la pagina annotazioni di un documento
2. (Opzionale) Applicare filtri per categoria se si desidera esportare solo alcune categorie
3. Cliccare sul bottone "Esporta" (verde con icona download)
4. Selezionare il formato desiderato dal menu dropdown:
   - **PDF**: Per documenti generali, stampa, condivisione
   - **Word**: Per editing ulteriore, commenti, revisioni
   - **LaTeX**: Per documenti accademici, tesi, articoli scientifici
5. Il file viene scaricato automaticamente

## Implementazione Tecnica

### File Modificati
- `routes/text_documents.py`: Aggiunta route di esportazione e filtro categoria
- `templates/text_documents/document_annotations.html`: UI per filtri e esportazione
- `services/annotation_export.py`: Nuovo servizio per esportazione multi-formato
- `requirements.txt`: Aggiunte dipendenze `reportlab` e `PyTeX`

### Nuove Dipendenze
- `reportlab==4.0.5`: Per generazione PDF

### Route Aggiunta
- `GET /text-documents/export/<document_id>/<format_type>`: Endpoint per esportazione
  - Parametri URL: `categories[]` per filtro categoria
  - Formati supportati: `pdf`, `word`, `latex`

### Sicurezza
- Controllo permessi: solo proprietario documento o admin possono esportare
- Validazione formato di esportazione
- Sanitizzazione input per prevenire injection
- Gestione errori con fallback graceful

## Note di Installazione

Per utilizzare le funzionalità di esportazione, assicurarsi che le dipendenze siano installate:

```bash
pip install reportlab==4.0.5
```

Nel deployment Docker, le dipendenze vengono installate automaticamente dal `requirements.txt`.

## Esempi di Utilizzo

### Caso 1: Esportazione Completa in PDF
1. Aprire le annotazioni di un documento
2. Non applicare filtri (per includere tutte le categorie)
3. Esporta → PDF
4. Risultato: PDF completo con tutte le annotazioni

### Caso 2: Esportazione Filtrata per Ricerca
1. Aprire le annotazioni di un documento
2. Selezionare categorie specifiche (es. "Emozioni", "Temi")
3. Cliccare "Applica Filtro Categoria"
4. Esporta → Word
5. Risultato: Documento Word con solo le annotazioni delle categorie selezionate

### Caso 3: Documento Accademico
1. Filtrare per categorie rilevanti alla ricerca
2. Esporta → LaTeX
3. Compilare il file .tex con LaTeX
4. Risultato: Documento accademico formattato professionalmente

## Troubleshooting

### Problemi Comuni

**Errore "Modulo di esportazione non disponibile"**
- Verificare che `reportlab` sia installato
- Riavviare il server Flask dopo l'installazione

**Export non funziona**
- Verificare permessi sul documento
- Controllare che ci siano annotazioni da esportare
- Verificare connessione internet (per alcuni font PDF)

**File LaTeX non compila**
- Verificare di avere una distribuzione LaTeX installata
- Alcuni caratteri speciali potrebbero richiedere pacchetti aggiuntivi
- Il file generato usa encoding UTF-8
