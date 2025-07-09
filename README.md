# Analisi MU - Applicazione per l'Etichettatura Tematica Collaborativa

Un'applicazione web basata su **Flask** per la gestione collaborativa dell'etichettatura tematica di risposte testuali contenute in file Excel, progettata per supportare processi di analisi tematica scientifica.

## 🎯 Obiettivi

L'applicazione supporta ricercatori nell'analisi qualitativa permettendo di:
- Caricare file Excel contenenti risposte testuali
- Creare un sistema di etichette personalizzato 
- Annotare collaborativamente le celle testuali
- Analizzare l'accordo inter-codificatore
- Esportare i dati per successive analisi

## ✨ Funzionalità Principali

### 📊 Gestione File Excel
- Caricamento di file `.xlsx` e `.xls`
- Estrazione automatica delle celle testuali
- Supporto per file multi-foglio
- Visualizzazione strutturata dei contenuti

### 🏷️ Sistema di Etichettatura
- Creazione di etichette con nome, descrizione, categoria e colore
- Gestione collaborativa del repertorio di etichette
- Assegnazione multipla di etichette per cella
- Storico completo delle annotazioni

### 👥 Collaborazione
- Gestione utenti con autenticazione sicura
- Visualizzazione delle etichette di tutti gli utenti
- Tracking delle modifiche con timestamp e autore
- Dashboard personali per ogni ricercatore

### 📈 Analisi e Statistiche
- Statistiche generali sull'avanzamento
- Analisi dell'uso delle etichette
- Confronto tra etichettatori
- Esportazione dati per analisi esterne

## 🛠️ Tecnologie Utilizzate

- **Backend**: Flask 3.0 (Python)
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Autenticazione**: Flask-Login
- **Form**: Flask-WTF + WTForms
- **Frontend**: Bootstrap 5 + JavaScript
- **File Processing**: Pandas + OpenPyXL

## 🚀 Installazione e Setup

### Requisiti
- Python 3.8+
- pip (package manager Python)

### Setup Rapido

1. **Clona il repository**
   ```bash
   git clone <repository-url>
   cd analisi-mu
   ```

2. **Esegui lo script di setup**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Avvia l'applicazione**
   ```bash
   source venv/bin/activate
   python app.py
   ```

4. **Accedi all'applicazione**
   - Apri il browser su: http://localhost:5000
   - Login con account admin:
     - Username: `admin`
     - Password: `admin123`

### Setup Manuale

1. **Crea ambiente virtuale**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Installa dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura ambiente**
   ```bash
   cp .env.example .env
   # Modifica .env secondo necessità
   ```

4. **Inizializza database**
   ```bash
   python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import db; db.create_all()"
   ```

## 📋 Struttura del Progetto

```
analisi-mu/
├── app.py                 # Applicazione principale Flask
├── models.py              # Modelli del database
├── forms.py               # Form WTForms
├── requirements.txt       # Dipendenze Python
├── setup.sh              # Script di setup automatico
├── .env.example          # Template configurazione
│
├── routes/               # Blueprint delle routes
│   ├── __init__.py
│   ├── auth.py          # Autenticazione
│   ├── main.py          # Routes principali
│   ├── excel.py         # Gestione file Excel
│   ├── labels.py        # Gestione etichette
│   └── annotation.py    # Sistema annotazioni
│
├── templates/           # Template Jinja2
│   ├── base.html        # Template base
│   ├── auth/            # Template autenticazione
│   ├── main/            # Template principali
│   ├── excel/           # Template file Excel
│   ├── labels/          # Template etichette
│   └── annotation/      # Template annotazioni
│
├── static/              # File statici
│   ├── css/
│   │   └── style.css    # Stili personalizzati
│   └── js/
│       └── main.js      # JavaScript principale
│
└── uploads/             # Cartella file caricati
```

## 💻 Utilizzo

### 1. Primo Accesso
- Registra un nuovo account o usa l'admin predefinito
- Familiarizza con l'interfaccia dalla dashboard

### 2. Caricamento File Excel
- Vai a "File Excel" → "Carica File"
- Seleziona un file `.xlsx` o `.xls` 
- L'applicazione estrae automaticamente le celle testuali

### 3. Creazione Etichette
- Vai a "Etichette" → "Crea Etichetta"
- Definisci nome, descrizione, categoria e colore
- Le etichette sono condivise tra tutti gli utenti

### 4. Annotazione
- Vai a "Annotazioni" → "Naviga Celle"
- Seleziona una cella da annotare
- Assegna una o più etichette cliccando su di esse
- Visualizza le annotazioni degli altri utenti

### 5. Analisi
- Usa "Annotazioni" → "Statistiche" per analisi generali
- Esporta i dati per analisi esterne (feature futura)

## 🔧 Configurazione

### Variabili d'Ambiente (.env)

```bash
# Sicurezza
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///analisi_mu.db

# Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

### Database

L'applicazione supporta:
- **SQLite** (predefinito, per sviluppo)
- **PostgreSQL** (consigliato per produzione)

Per PostgreSQL:
```bash
DATABASE_URL=postgresql://username:password@localhost/analisi_mu
```

## 📊 Modello Dati

### Entità Principali

- **User**: Utenti/ricercatori del sistema
- **ExcelFile**: File Excel caricati
- **TextCell**: Celle testuali estratte dai file
- **Label**: Etichette del sistema
- **CellAnnotation**: Annotazioni delle celle

### Relazioni
- Un utente può caricare molti file Excel
- Un file Excel contiene molte celle testuali
- Una cella può avere molte annotazioni (da utenti diversi)
- Un'annotazione collega utente, cella ed etichetta

## 🔐 Sicurezza

- Password hashate con Werkzeug
- Protezione CSRF su tutti i form
- Session management sicuro con Flask-Login
- Validazione input lato server e client
- Upload file con controlli di sicurezza

## 🎨 Interfaccia Utente

- Design responsivo con Bootstrap 5
- Interfaccia intuitiva e user-friendly
- Feedback visivo per tutte le azioni
- Supporto per temi scuri (futuro)
- Accessibilità WCAG compliant

## 🚀 Deploy in Produzione

### Preparazione
1. Imposta `FLASK_ENV=production`
2. Usa un database PostgreSQL
3. Configura un server web (nginx + gunicorn)
4. Imposta HTTPS
5. Backup automatici del database

### Esempio con Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 🔄 Roadmap

### Prossime Funzionalità
- [ ] Esportazione dati in formato CSV/Excel
- [ ] Calcolo accordo inter-codificatore (Cohen's Kappa)
- [ ] Sistema di progetti per organizzare il lavoro
- [ ] API REST per integrazioni esterne
- [ ] Importazione etichette da file esterni
- [ ] Sistema di backup automatico
- [ ] Dashboard analytics avanzate
- [ ] Supporto per file CSV
- [ ] Sistema di notifiche
- [ ] Modalità offline

### Miglioramenti UX
- [ ] Ricerca avanzata nelle celle
- [ ] Filtri multipli per annotazioni
- [ ] Shortcuts da tastiera
- [ ] Tour guidato per nuovi utenti
- [ ] Tema scuro
- [ ] Supporto mobile ottimizzato

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/amazing-feature`)
3. Commit delle modifiche (`git commit -m 'Add amazing feature'`)
4. Push del branch (`git push origin feature/amazing-feature`)
5. Apri una Pull Request

## 📝 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per dettagli.

## 📞 Supporto

Per problemi, domande o suggerimenti:
- Apri una Issue su GitHub
- Contatta il team di sviluppo

## 🙏 Ringraziamenti

Sviluppato per supportare la ricerca qualitativa nell'ambito dell'analisi tematica collaborativa.
