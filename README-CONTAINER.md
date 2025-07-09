# 🐳 Guida Rapida - Avvio Container Analisi MU

## 🚀 Avvio Immediato

### Opzione 1: Docker Compose (Consigliato)

```bash
# 1. Avvia il container
docker-compose up -d

# 2. Verifica che sia in esecuzione
docker-compose ps

# 3. Visualizza i log
docker-compose logs -f web
```

### Opzione 2: Makefile (Ancora più semplice)

```bash
# Avvia tutto con un comando
make up

# Oppure per vedere i log in tempo reale
make dev
```

### Opzione 3: Docker manuale

```bash
# 1. Build dell'immagine
docker build -t analisi-mu .

# 2. Avvia il container
docker run -d \
  --name analisi-mu \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/backups:/app/backups \
  analisi-mu
```

## 📋 Verifica che tutto funzioni

1. **Accedi all'applicazione**: http://localhost:5000
2. **Login di test**: 
   - Username: `admin`
   - Password: `admin123`

## 🛠️ Comandi Utili

### Gestione Container

```bash
# Ferma il container
docker-compose down

# Riavvia il container
docker-compose restart

# Visualizza lo stato
docker-compose ps

# Accedi al container
docker-compose exec web bash
```

### Con Makefile

```bash
make help      # Mostra tutti i comandi disponibili
make up        # Avvia i servizi
make down      # Ferma i servizi
make logs      # Visualizza i log
make restart   # Riavvia i servizi
make shell     # Accedi al container
make backup    # Crea backup del database
make ps        # Mostra lo stato
```

## 🔧 Risoluzione Problemi

### Porta 5000 già in uso

```bash
# Cambia la porta nel docker-compose.yml
ports:
  - "5001:5000"  # Usa la porta 5001

# Oppure ferma il processo che usa la porta 5000
sudo lsof -i :5000
sudo kill -9 [PID]
```

### Container non si avvia

```bash
# 1. Controlla i log per errori
docker-compose logs web

# 2. Verifica lo stato del container
docker-compose ps

# 3. Ricostruisci l'immagine
docker-compose build --no-cache

# 4. Riavvia tutto
docker-compose down && docker-compose up -d
```

### Problemi di permessi

```bash
# Imposta i permessi corretti
sudo chown -R $USER:$USER ./instance ./uploads ./backups
chmod 755 ./instance ./uploads ./backups
```

## 📂 Struttura File Persistenti

I seguenti file/directory sono persistenti:

```
./instance/     # Database SQLite
./uploads/      # File Excel caricati
./backups/      # Backup del database
```

## 🔒 Configurazione Produzione

Per l'ambiente di produzione:

```bash
# 1. Copia il file di configurazione
cp .env.production .env

# 2. Modifica le variabili
nano .env

# 3. Avvia in produzione
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoraggio

```bash
# Visualizza risorse usate
docker stats

# Health check
curl http://localhost:5000/

# Log in tempo reale
docker-compose logs -f --tail=100
```

## 🔄 Backup e Ripristino

### Backup automatico

```bash
# Con Makefile
make backup

# Manualmente
docker-compose exec web python -c "
import shutil, datetime
shutil.copy2('/app/instance/analisi_mu.db', 
             f'/app/backups/analisi_mu_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db')
"
```

### Ripristino

```bash
# 1. Ferma il container
docker-compose down

# 2. Ripristina il database
cp ./backups/analisi_mu_backup_YYYYMMDD_HHMMSS.db ./instance/analisi_mu.db

# 3. Riavvia il container
docker-compose up -d
```

## ⚡ Comandi Rapidi

```bash
# Setup completo prima volta
make init

# Sviluppo rapido
make dev

# Produzione
make prod

# Pulizia sistema
make clean

# Stato completo
make status
```

## 📱 Accesso all'Applicazione

Una volta avviato il container, accedi a:

- **URL**: http://localhost:5000
- **Admin**: admin / admin123
- **Dashboard**: http://localhost:5000/dashboard

## 🆘 Supporto

In caso di problemi:

1. Controlla i log: `make logs`
2. Verifica lo stato: `make ps`
3. Riavvia: `make restart`
4. Ricostruisci: `make build-no-cache && make up`

---

**Nota**: Assicurati di avere Docker e Docker Compose installati sul tuo sistema prima di procedere.
