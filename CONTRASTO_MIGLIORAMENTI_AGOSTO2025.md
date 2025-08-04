# Miglioramenti Contrasto CSS - Agosto 2025

## Problema Risolto
I titoli e testi informativi su sfondi blu e chiari avevano problemi di contrasto e risultavano illeggibili.

**Problema specifico identificato:** 
- Pagine Excel con `card-header bg-light` (sfondo chiaro) avevano testo bianco forzato
- URL problematico: `/excel/file/3/question/...` - routes Excel, non annotation
- Template: `templates/excel/view_question.html` linea 384

## Modifiche Implementate

### 1. Miglioramenti Card Header Standard (`static/css/style.css`)
- **Titoli principali**: Forzato colore bianco per h5 e .h5 dentro card-header con sfondo blu
- **Testi secondari**: Migliorato contrasto per .text-muted e small con rgba(255, 255, 255, 0.85)
- **Label dei form**: Colore bianco per migliore leggibilità

### 2. Correzione Card Header con bg-light
- **CORREZIONE CRITICA**: `.card-header.bg-light` ora usa testo scuro su sfondo chiaro
- **Specificità alta**: Regole specifiche per sovrascrivere le regole generali
- **Testo**: `var(--dark-color)` su `var(--light-color)`

### 3. Regole Generali di Contrasto
- **Sfondi colorati**: Migliorato contrasto per .text-muted su bg-primary, bg-secondary, bg-info, bg-dark
- **Elementi small**: Colore migliorato su tutti i sfondi scuri
- **Emergency fix**: Regole aggressive per forzare visibilità

## File Modificati
- `/static/css/style.css` - Aggiunta sezione completa per miglioramenti contrasto
- **Template coinvolto**: `/templates/excel/view_question.html` (non modificato, solo analizzato)

## Test Consigliati
1. ✅ Verificare la pagina `/excel/file/[ID]/question/[QUESTION]` 
2. ✅ Controllare card-header con bg-light (sfondo chiaro)
3. ✅ Controllare card-header standard (sfondo blu)
4. ⏳ Testare la leggibilità su dispositivi mobili

## Note Tecniche
- **Problema root**: Bootstrap `bg-light` class sovrascriveva gli stili di contrasto
- **Soluzione**: Regole CSS specifiche per `.card-header.bg-light`
- **Specificità**: Usato selettori specifici per vincere sui selettori generali

## Colori di Riferimento
- **Card-header standard**: Testo bianco su gradiente blu
- **Card-header bg-light**: Testo `var(--dark-color)` su `var(--light-color)`
- **Trasparenze**: `rgba(255, 255, 255, 0.85)` per testi secondari su sfondi scuri
