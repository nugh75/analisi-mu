# Piano d'Azione: Risoluzione Problemi AI

## 🎯 Obiettivi
1. Risolvere il problema di generazione etichette (timeout Ollama)
2. Aggiungere gestione template nella configurazione AI
3. Migliorare feedback utente durante la generazione

## 📊 Problemi Identificati

### Problema 1: Timeout Ollama
**Sintomo**: `HTTPConnectionPool(host='192.168.129.14', port=11435): Read timed out. (read timeout=60)`
**Possibili Cause**:
- Ollama non risponde o è sovraccarico
- Prompt troppo lungo o complesso
- Batch size troppo grande (attualmente 20 celle)
- Modello troppo lento (devstral:24b)

### Problema 2: Template non gestiti in configurazione
**Sintomo**: L'interfaccia admin non ha sezione template
**Conseguenze**: 
- Non si possono modificare i template via UI
- Non si può vedere quale template è attivo
- Impossibile creare template personalizzati

## 🔧 Soluzioni Proposte

### A. Risoluzione Timeout (Priorità ALTA)
1. **Verifica stato Ollama**
   - Controllare se Ollama è in esecuzione
   - Testare connessione diretta
   - Verificare risorse sistema

2. **Ottimizzazione parametri**
   - Ridurre batch size da 20 a 5-10 celle
   - Aumentare timeout da 60s a 120s
   - Semplificare prompt se necessario

3. **Fallback e retry**
   - Implementare retry automatico
   - Fallback a batch più piccoli
   - Messaggi di errore più chiari

### B. Gestione Template (Priorità MEDIA)
1. **Estendere configurazione AI**
   - Aggiungere sezione "Template Management" 
   - CRUD per template personalizzati
   - Preview template in tempo reale

2. **Database schema**
   - Tabella `ai_prompt_templates`
   - Relazione con `AIConfiguration`
   - Versioning template

3. **UI miglioramenti**
   - Editor template con syntax highlighting
   - Test template su campioni
   - Import/export template

## 🎯 Implementazione

### Step 1: Diagnostica Immediate (15 min)
- [ ] Verificare stato Ollama
- [ ] Testare connessione AI
- [ ] Controllare logs dettagliati

### Step 2: Fix Rapidi (30 min)
- [ ] Ridurre batch size
- [ ] Aumentare timeout
- [ ] Migliorare error handling

### Step 3: Template Management (2 ore)
- [ ] Creare modello database template
- [ ] Estendere admin interface
- [ ] Implementare CRUD template

### Step 4: Testing (30 min)
- [ ] Test generazione con parametri ottimizzati
- [ ] Test template personalizzati
- [ ] Validazione completa workflow

## 🚀 Risultati Attesi
- ✅ Generazione etichette funzionante
- ✅ Template configurabili via UI
- ✅ Feedback utente migliorato
- ✅ Sistema più robusto e configurabile
