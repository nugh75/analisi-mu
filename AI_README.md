# 🤖 AI Integration Guide -Anatema

Guida completa per l'integrazione e configurazione delle funzionalità di **Intelligenza Artificiale** in Anatema. Il sistema supporta multiple provider AI per l'annotazione automatica e assistita.

## 🎯 Panoramica

Analisi MU integra modelli di linguaggio avanzati per:
- **Annotazione automatica**: Classificazione automatica delle celle testuali
- **Suggerimenti intelligenti**: Raccomandazioni di etichette basate su AI
- **Analisi del sentiment**: Analisi automatica del sentiment
- **Classificazione tematica**: Categorizzazione automatica dei contenuti
- **Template personalizzati**: Prompt specifici per domini di ricerca

## 🔧 Provider Supportati

### 1. **OpenAI** (Raccomandato)
- **Modelli**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Vantaggi**: Qualità superiore, ampia gamma di modelli
- **Costi**: A consumo, pricing competitivo

### 2. **Anthropic Claude**
- **Modelli**: Claude-3 Opus, Claude-3 Sonnet, Claude-3 Haiku
- **Vantaggi**: Eccellente per analisi di testi lunghi
- **Costi**: A consumo, ottimo rapporto qualità/prezzo

### 3. **Ollama** (Locale)
- **Modelli**: Llama 3.1, Mistral, Gemma, Phi-3
- **Vantaggi**: Completamente locale, nessun costo aggiuntivo
- **Requisiti**: GPU dedicata o CPU potente

## 🚀 Configurazione Rapida

### 1. Configura le API Keys

```bash
# Nel file .env
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
OLLAMA_BASE_URL=http://localhost:11434
```

### 2. Testa la connessione

```bash
# Testa OpenAI
python -c "
import openai
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
response = openai.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Test'}],
    max_tokens=10
)
print('OpenAI: OK')
"

# Testa Anthropic
python -c "
import anthropic
import os
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
response = client.messages.create(
    model='claude-3-haiku-20240307',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'Test'}]
)
print('Anthropic: OK')
"

# Testa Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Test",
  "stream": false
}'
```

## 📋 Configurazione Dettagliata

### OpenAI Setup

1. **Crea account** su [OpenAI Platform](https://platform.openai.com/)
2. **Genera API Key** nella sezione API Keys
3. **Imposta billing** per abilitare l'uso
4. **Configura limiti** per controllare i costi

```python
# Configurazione modelli OpenAI
OPENAI_MODELS = {
    'gpt-4': {
        'name': 'GPT-4',
        'max_tokens': 8192,
        'cost_per_1k_tokens': 0.03,
        'recommended_for': 'Analisi complesse, alta qualità'
    },
    'gpt-4-turbo': {
        'name': 'GPT-4 Turbo',
        'max_tokens': 128000,
        'cost_per_1k_tokens': 0.01,
        'recommended_for': 'Testi lunghi, analisi dettagliate'
    },
    'gpt-3.5-turbo': {
        'name': 'GPT-3.5 Turbo',
        'max_tokens': 16384,
        'cost_per_1k_tokens': 0.001,
        'recommended_for': 'Uso generale, economico'
    }
}
```

### Anthropic Setup

1. **Crea account** su [Anthropic Console](https://console.anthropic.com/)
2. **Genera API Key** nella sezione API Keys
3. **Configura billing** per abilitare l'uso

```python
# Configurazione modelli Anthropic
ANTHROPIC_MODELS = {
    'claude-3-opus': {
        'name': 'Claude-3 Opus',
        'max_tokens': 200000,
        'cost_per_1k_tokens': 0.015,
        'recommended_for': 'Analisi complesse, ricerca avanzata'
    },
    'claude-3-sonnet': {
        'name': 'Claude-3 Sonnet',
        'max_tokens': 200000,
        'cost_per_1k_tokens': 0.003,
        'recommended_for': 'Bilanciamento qualità/costo'
    },
    'claude-3-haiku': {
        'name': 'Claude-3 Haiku',
        'max_tokens': 200000,
        'cost_per_1k_tokens': 0.0005,
        'recommended_for': 'Analisi veloci, economiche'
    }
}
```

### Ollama Setup (Locale)

1. **Installa Ollama**
```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Scarica da https://ollama.com/download/windows
```

2. **Avvia il servizio**
```bash
# Avvia Ollama
ollama serve

# Installa modelli
ollama pull llama3.1
ollama pull mistral
ollama pull gemma2
```

3. **Configura modelli**
```python
# Configurazione modelli Ollama
OLLAMA_MODELS = {
    'llama3.1': {
        'name': 'Llama 3.1',
        'size': '4.7GB',
        'recommended_for': 'Uso generale, buona qualità'
    },
    'mistral': {
        'name': 'Mistral 7B',
        'size': '4.1GB',
        'recommended_for': 'Veloce, efficiente'
    },
    'gemma2': {
        'name': 'Gemma 2',
        'size': '5.4GB',
        'recommended_for': 'Analisi tecniche'
    }
}
```

## 🎯 Template e Prompt

### Template predefiniti

Il sistema include template ottimizzati per diversi domini:

#### 1. **Analisi Sentiment**
```python
SENTIMENT_TEMPLATE = """
Analizza il sentiment del seguente testo e classificalo in una delle seguenti categorie:
- Positivo: Atteggiamento favorevole
- Negativo: Atteggiamento contrario
- Neutro: Posizione neutra
- Ambivalente: Contiene aspetti sia positivi che negativi

Testo: {text}

Fornisci solo la classificazione senza spiegazioni aggiuntive.
"""
```

#### 2. **Classificazione Tematica**
```python
THEMATIC_TEMPLATE = """
Classifica il seguente testo secondo le categorie tematiche:
{categories}

Testo: {text}

Seleziona una o più categorie pertinenti e fornisci una breve giustificazione.
"""
```

#### 3. **Analisi Educativa**
```python
EDUCATIONAL_TEMPLATE = """
Analizza il seguente testo dal punto di vista educativo considerando:
- Livello di istruzione
- Ambito disciplinare
- Prospettiva (studente/docente/genitore)
- Problematiche evidenziate

Testo: {text}

Fornisci un'analisi strutturata.
"""
```

### Personalizzazione Template

```python
# Crea template personalizzato
def create_custom_template(domain, categories, instructions):
    template = f"""
    Dominio: {domain}
    
    Categorie disponibili:
    {categories}
    
    Istruzioni specifiche:
    {instructions}
    
    Testo da analizzare: {{text}}
    
    Fornisci classificazione e motivazione.
    """
    return template

# Esempio per ricerca medica
medical_template = create_custom_template(
    domain="Ricerca Medica",
    categories=["Sintomi", "Diagnosi", "Trattamento", "Prevenzione"],
    instructions="Identifica elementi clinici rilevanti"
)
```

## 🔄 Utilizzo nell'Interfaccia

### 1. **Annotazione Automatica**
- Seleziona le celle da annotare
- Scegli il modello AI da utilizzare
- Configura il template appropriato
- Avvia l'annotazione automatica
- Revisiona e conferma i risultati

### 2. **Suggerimenti Intelligenti**
- Durante l'annotazione manuale
- Il sistema suggerisce etichette pertinenti
- Basato su modelli pre-addestrati
- Miglioramento continuo con feedback

### 3. **Analisi Batch**
- Elaborazione di grandi volumi di dati
- Schedulazione di job asincroni
- Monitoraggio del progresso
- Esportazione risultati

## 📊 Monitoraggio e Ottimizzazione

### Metriche di Performance

```python
# Tracking delle metriche
AI_METRICS = {
    'accuracy': 0.85,          # Precisione delle classificazioni
    'processing_time': 2.3,    # Tempo medio per annotazione
    'cost_per_annotation': 0.005,  # Costo per annotazione
    'user_satisfaction': 0.92  # Soddisfazione utente
}
```

### Ottimizzazione dei Costi

```python
# Strategia di ottimizzazione
COST_OPTIMIZATION = {
    'use_cache': True,         # Cache per richieste duplicate
    'batch_processing': True,  # Elaborazione batch
    'model_selection': 'auto', # Selezione automatica modello
    'max_daily_cost': 50.0     # Limite di spesa giornaliera
}
```

## 🛡️ Sicurezza e Privacy

### Protezione dei Dati

1. **Dati sensibili**: Non inviare mai dati personali agli AI esterni
2. **Anonimizzazione**: Rimuovi identificatori prima dell'elaborazione
3. **Controllo accesso**: Limita l'accesso alle funzionalità AI
4. **Audit trail**: Registra tutte le operazioni AI

### Configurazione Sicura

```python
# Configurazione sicurezza AI
AI_SECURITY = {
    'data_anonymization': True,
    'request_logging': True,
    'response_sanitization': True,
    'rate_limiting': True,
    'max_text_length': 5000,
    'blocked_patterns': ['email', 'phone', 'ssn']
}
```

## 🔧 Risoluzione Problemi

### Errori Comuni

#### 1. **API Key non valida**
```bash
# Verifica la key
echo $OPENAI_API_KEY | cut -c1-10
# Deve iniziare con "sk-"

# Testa la connessione
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### 2. **Limite di rate raggiunto**
```python
# Implementa retry con backoff
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

#### 3. **Ollama non risponde**
```bash
# Verifica stato servizio
curl http://localhost:11434/api/tags

# Riavvia Ollama
ollama serve

# Controlla log
journalctl -u ollama -f
```

## 📈 Migliori Pratiche

### 1. **Selezione del Modello**
- **GPT-4**: Analisi complesse, ricerca avanzata
- **GPT-3.5**: Uso generale, buon rapporto qualità/prezzo
- **Claude-3**: Testi lunghi, analisi dettagliate
- **Ollama**: Privacy, controllo completo, nessun costo

### 2. **Ottimizzazione dei Prompt**
```python
# Prompt structure
EFFECTIVE_PROMPT = """
Contesto: {context}
Obiettivo: {objective}
Formato richiesto: {format}
Esempi: {examples}
Testo: {text}
"""
```

### 3. **Gestione della Qualità**
- Valida sempre i risultati AI
- Implementa feedback loop
- Monitora l'accuratezza nel tempo
- Aggiorna i template regolarmente

## 🤝 Contributi

Per contribuire alle funzionalità AI:

1. **Testa nuovi modelli** e condividi i risultati
2. **Crea template** per domini specifici
3. **Ottimizza i prompt** per migliori performance
4. **Documenta** le configurazioni di successo

## 🆘 Supporto

Per problemi con l'AI:

- **Issues**: Usa il tag `ai` su GitHub
- **Logs**: Includi sempre i log delle richieste AI
- **Configurazione**: Condividi la configurazione (senza API keys)
- **Esempi**: Fornisci esempi di testi problematici

---

**AI Integration** - *Intelligenza Artificiale per l'analisi qualitativa avanzata*
