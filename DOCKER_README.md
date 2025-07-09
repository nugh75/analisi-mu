# Docker Setup per Analisi MU

## Avvio rapido con Docker Compose

### Ambiente di sviluppo

```bash
# Avvia l'applicazione
docker-compose up -d

# Visualizza i log
docker-compose logs -f

# Ferma l'applicazione
docker-compose down
```

### Ambiente di produzione

```bash
# Crea un file .env con le variabili di produzione
cp .env.example .env

# Modifica .env con i valori di produzione
nano .env

# Avvia l'applicazione in produzione
docker-compose -f docker-compose.prod.yml up -d

# Visualizza i log
docker-compose -f docker-compose.prod.yml logs -f

# Ferma l'applicazione
docker-compose -f docker-compose.prod.yml down
```

## Comandi utili

### Build dell'immagine

```bash
# Build dell'immagine Docker
docker build -t analisi-mu .

# Build forzato (senza cache)
docker build --no-cache -t analisi-mu .
```

### Gestione dei container

```bash
# Riavvia solo il servizio web
docker-compose restart web

# Accedi al container
docker-compose exec web bash

# Visualizza lo stato dei servizi
docker-compose ps
```

### Backup e ripristino

```bash
# Backup del database
docker-compose exec web python -c "
import shutil
import datetime
shutil.copy2('/app/instance/analisi_mu.db', 
             f'/app/backups/analisi_mu_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db')
"

# Lista dei backup
docker-compose exec web ls -la /app/backups/
```

## Struttura dei volumi

- `./instance` - Directory contenente il database SQLite
- `./uploads` - Directory per i file Excel caricati
- `./backups` - Directory per i backup del database

## Configurazione

Le variabili d'ambiente possono essere configurate in:
1. File `.env` (non incluso nel repository)
2. Direttamente nel file `docker-compose.yml`
3. Variabili d'ambiente del sistema

### Variabili principali:

- `SECRET_KEY` - Chiave segreta per Flask (CAMBIA IN PRODUZIONE!)
- `DATABASE_URL` - URL del database (SQLite per default)
- `FLASK_ENV` - Ambiente Flask (development/production)
- `FLASK_DEBUG` - Debug mode (0/1)
- `MAX_CONTENT_LENGTH` - Dimensione massima file upload
- `UPLOAD_FOLDER` - Directory per i file caricati

## Troubleshooting

### Problemi comuni:

1. **Porta 5000 già in uso**
   ```bash
   # Modifica la porta nel docker-compose.yml
   ports:
     - "5001:5000"  # Usa la porta 5001 invece di 5000
   ```

2. **Database non accessibile**
   ```bash
   # Verifica i permessi della directory instance
   sudo chown -R $USER:$USER ./instance
   ```

3. **Container non si avvia**
   ```bash
   # Controlla i log per errori
   docker-compose logs web
   ```

4. **Build fallisce**
   ```bash
   # Pulisci cache Docker
   docker system prune -a
   ```

## Monitoraggio

L'applicazione include un health check che verifica:
- Accessibilità del servizio sulla porta 5000
- Stato dell'applicazione Flask

Il health check è configurato per:
- Intervallo: 30 secondi
- Timeout: 10 secondi
- Retry: 3 tentativi
- Periodo di grazia: 40 secondi
