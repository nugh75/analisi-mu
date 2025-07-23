/**
 * Sistema di annotazione di testo per documenti
 */
class TextAnnotationSystem {
    constructor(options) {
        this.documentId = options.documentId;
        this.container = document.getElementById(options.containerId);
        this.annotations = options.annotations || [];
        this.labels = options.labels || [];
        
        this.selectedText = null;
        this.selectedRange = null;
        this.lineNumbersVisible = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.renderAnnotations();
        this.setupModals();
    }
    
    setupEventListeners() {
        // Selezione testo
        this.container.addEventListener('mouseup', (e) => {
            setTimeout(() => this.handleTextSelection(e), 10);
        });
        
        // Click su annotazioni esistenti
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('annotation-highlight')) {
                this.showAnnotationDetails(e.target.dataset.annotationId);
            }
        });
        
        // Previeni selezione su annotazioni esistenti durante la creazione
        this.container.addEventListener('selectstart', (e) => {
            if (e.target.classList.contains('annotation-highlight')) {
                e.preventDefault();
            }
        });
    }
    
    setupModals() {
        this.annotationModal = new bootstrap.Modal(document.getElementById('annotationModal'));
        this.detailsModal = new bootstrap.Modal(document.getElementById('annotationDetailsModal'));
        
        // Salva annotazione
        document.getElementById('saveAnnotation').addEventListener('click', () => {
            this.saveAnnotation();
        });
    }
    
    handleTextSelection(e) {
        const selection = window.getSelection();
        
        if (selection.rangeCount === 0 || selection.isCollapsed) {
            return;
        }
        
        const range = selection.getRangeAt(0);
        
        // Verifica che la selezione sia all'interno del container
        if (!this.container.contains(range.commonAncestorContainer)) {
            return;
        }
        
        // Verifica che non ci siano annotazioni esistenti nella selezione
        if (this.hasExistingAnnotations(range)) {
            this.showToast('Non è possibile annotare testo già etichettato', 'warning');
            selection.removeAllRanges();
            return;
        }
        
        const selectedText = selection.toString().trim();
        
        if (selectedText.length < 3) {
            this.showToast('Seleziona almeno 3 caratteri per creare un\'annotazione', 'warning');
            selection.removeAllRanges();
            return;
        }
        
        if (selectedText.length > 1000) {
            this.showToast('La selezione è troppo lunga (massimo 1000 caratteri)', 'warning');
            selection.removeAllRanges();
            return;
        }
        
        // Calcola posizioni
        const startPos = this.getTextPosition(range.startContainer, range.startOffset);
        const endPos = this.getTextPosition(range.endContainer, range.endOffset);
        
        this.selectedText = selectedText;
        this.selectedRange = {
            start: startPos,
            end: endPos,
            range: range.cloneRange()
        };
        
        this.showAnnotationModal();
    }
    
    hasExistingAnnotations(range) {
        const walker = document.createTreeWalker(
            range.commonAncestorContainer,
            NodeFilter.SHOW_ELEMENT,
            {
                acceptNode: (node) => {
                    return node.classList && node.classList.contains('annotation-highlight') 
                        ? NodeFilter.FILTER_ACCEPT 
                        : NodeFilter.FILTER_SKIP;
                }
            }
        );
        
        while (walker.nextNode()) {
            if (range.intersectsNode(walker.currentNode)) {
                return true;
            }
        }
        
        return false;
    }
    
    getTextPosition(node, offset) {
        const walker = document.createTreeWalker(
            this.container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let position = 0;
        let currentNode;
        
        while (currentNode = walker.nextNode()) {
            if (currentNode === node) {
                return position + offset;
            }
            position += currentNode.textContent.length;
        }
        
        return position;
    }
    
    showAnnotationModal() {
        document.getElementById('selectedText').textContent = this.selectedText;
        document.getElementById('positionInfo').textContent = 
            `${this.selectedRange.start} - ${this.selectedRange.end} (${this.selectedText.length} caratteri)`;
        
        // Reset label selection
        document.getElementById('labelSelect').value = '';
        
        this.annotationModal.show();
    }
    
    saveAnnotation() {
        const labelSelect = document.getElementById('labelSelect');
        const labelId = labelSelect.value;
        
        if (!labelId) {
            this.showToast('Seleziona un\'etichetta', 'error');
            return;
        }
        
        const label = this.labels.find(l => l.id == labelId);
        if (!label) {
            this.showToast('Etichetta non valida', 'error');
            return;
        }
        
        // Calcola contesto
        const context = this.getContext(this.selectedRange.start, this.selectedRange.end);
        
        const annotationData = {
            document_id: this.documentId,
            text_selection: this.selectedText,
            start_position: this.selectedRange.start,
            end_position: this.selectedRange.end,
            label_id: labelId,
            context_before: context.before,
            context_after: context.after
        };
        
        fetch('/text-documents/api/annotate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify(annotationData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message, 'success');
                this.annotationModal.hide();
                
                // Aggiorna l'interfaccia
                this.addAnnotationToList(data.annotation);
                this.highlightAnnotation(this.selectedRange.range, label, data.annotation.id);
                this.clearSelection();
                
                // Aggiorna contatori
                this.updateStats();
                
            } else {
                this.showToast('Errore: ' + data.message, 'error');
            }
        })
        .catch(error => {
            this.showToast('Errore di connessione: ' + error.message, 'error');
        });
    }
    
    getContext(start, end) {
        const fullText = this.container.textContent;
        const contextLength = 100;
        
        const beforeStart = Math.max(0, start - contextLength);
        const afterEnd = Math.min(fullText.length, end + contextLength);
        
        return {
            before: fullText.substring(beforeStart, start),
            after: fullText.substring(end, afterEnd)
        };
    }
    
    highlightAnnotation(range, label, annotationId) {
        const span = document.createElement('span');
        span.className = 'annotation-highlight';
        span.style.backgroundColor = this.hexToRgba(label.color || '#007bff', 0.3);
        span.style.borderBottom = `2px solid ${label.color || '#007bff'}`;
        span.style.cursor = 'pointer';
        span.dataset.annotationId = annotationId;
        span.title = `${label.name}: ${range.toString().substring(0, 50)}...`;
        
        try {
            range.surroundContents(span);
        } catch (e) {
            // Fallback per selezioni complesse
            const contents = range.extractContents();
            span.appendChild(contents);
            range.insertNode(span);
        }
    }
    
    renderAnnotations() {
        // Ordina annotazioni per posizione
        const sortedAnnotations = [...this.annotations].sort((a, b) => a.start_position - b.start_position);
        
        let offset = 0;
        const textContent = this.container.textContent;
        this.container.innerHTML = '';
        
        for (let i = 0; i < sortedAnnotations.length; i++) {
            const annotation = sortedAnnotations[i];
            const label = this.labels.find(l => l.id === annotation.label_id);
            
            // Testo prima dell'annotazione
            if (annotation.start_position > offset) {
                const beforeText = textContent.substring(offset, annotation.start_position);
                this.container.appendChild(document.createTextNode(beforeText));
            }
            
            // Annotazione
            const span = document.createElement('span');
            span.className = 'annotation-highlight';
            span.style.backgroundColor = this.hexToRgba(label?.color || '#007bff', 0.3);
            span.style.borderBottom = `2px solid ${label?.color || '#007bff'}`;
            span.style.cursor = 'pointer';
            span.dataset.annotationId = annotation.id;
            span.title = `${label?.name || 'Unknown'}: ${annotation.text_selection.substring(0, 50)}...`;
            span.textContent = annotation.text_selection;
            
            this.container.appendChild(span);
            offset = annotation.end_position;
        }
        
        // Testo rimanente
        if (offset < textContent.length) {
            const remainingText = textContent.substring(offset);
            this.container.appendChild(document.createTextNode(remainingText));
        }
    }
    
    addAnnotationToList(annotation) {
        const annotationsList = document.querySelector('.card-body[style*="max-height: 400px"]');
        
        // Se la lista era vuota, rimuovi il messaggio placeholder
        const placeholder = annotationsList.querySelector('.text-center.text-muted');
        if (placeholder) {
            placeholder.remove();
        }
        
        const annotationItem = document.createElement('div');
        annotationItem.className = 'annotation-item p-2 border-bottom';
        annotationItem.dataset.annotationId = annotation.id;
        
        const label = this.labels.find(l => l.id == annotation.label_id);
        
        annotationItem.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="label-color-indicator me-2 mt-1" 
                     style="width: 8px; height: 8px; background-color: ${label?.color || '#007bff'}; border-radius: 50%;"></div>
                <div class="flex-grow-1">
                    <div class="fw-bold small">${annotation.label_name}</div>
                    <div class="text-truncate small text-muted" style="max-width: 200px;">
                        "${annotation.text_preview}"
                    </div>
                    <div class="small text-muted">
                        ${window.currentUserName || 'Tu'} - ${annotation.created_at}
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger delete-annotation" 
                        data-annotation-id="${annotation.id}" title="Elimina">
                    <i class="bi bi-trash" style="font-size: 0.7rem;"></i>
                </button>
            </div>
        `;
        
        annotationsList.insertBefore(annotationItem, annotationsList.firstChild);
        
        // Aggiungi listener per eliminazione
        annotationItem.querySelector('.delete-annotation').addEventListener('click', (e) => {
            if (confirm('Sei sicuro di voler eliminare questa annotazione?')) {
                this.deleteAnnotation(annotation.id);
            }
        });
    }
    
    deleteAnnotation(annotationId) {
        fetch(`/text-documents/api/annotations/${annotationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message, 'success');
                
                // Rimuovi dall'interfaccia
                const annotationElement = document.querySelector(`[data-annotation-id="${annotationId}"]`);
                if (annotationElement) {
                    if (annotationElement.classList.contains('annotation-highlight')) {
                        // Sostituisci con testo normale
                        const textNode = document.createTextNode(annotationElement.textContent);
                        annotationElement.parentNode.replaceChild(textNode, annotationElement);
                    } else {
                        // Rimuovi dalla lista
                        annotationElement.remove();
                    }
                }
                
                // Aggiorna contatori
                this.updateStats();
                
                // Rimuovi dall'array locale
                this.annotations = this.annotations.filter(a => a.id != annotationId);
                
            } else {
                this.showToast('Errore: ' + data.message, 'error');
            }
        })
        .catch(error => {
            this.showToast('Errore di connessione: ' + error.message, 'error');
        });
    }
    
    showAnnotationDetails(annotationId) {
        const annotation = this.annotations.find(a => a.id == annotationId);
        if (!annotation) return;
        
        const label = this.labels.find(l => l.id === annotation.label_id);
        
        const content = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Etichetta</h6>
                    <div class="d-flex align-items-center mb-3">
                        <div class="label-color-indicator me-2" 
                             style="width: 16px; height: 16px; background-color: ${label?.color || '#007bff'}; border-radius: 3px;"></div>
                        <span class="fw-bold">${label?.name || 'Unknown'}</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Informazioni</h6>
                    <p class="small mb-1"><strong>Utente:</strong> ${annotation.user?.username || 'Unknown'}</p>
                    <p class="small mb-1"><strong>Data:</strong> ${annotation.created_at}</p>
                    <p class="small mb-3"><strong>Posizione:</strong> ${annotation.start_position} - ${annotation.end_position}</p>
                </div>
            </div>
            
            <h6>Testo Selezionato</h6>
            <div class="bg-light p-3 rounded border mb-3" style="max-height: 200px; overflow-y: auto;">
                "${annotation.text_selection}"
            </div>
            
            ${annotation.context_before || annotation.context_after ? `
                <h6>Contesto</h6>
                <div class="bg-light p-3 rounded border small">
                    ${annotation.context_before ? `<span class="text-muted">${annotation.context_before}</span>` : ''}
                    <span class="fw-bold text-primary">${annotation.text_selection}</span>
                    ${annotation.context_after ? `<span class="text-muted">${annotation.context_after}</span>` : ''}
                </div>
            ` : ''}
        `;
        
        document.getElementById('annotationDetailsContent').innerHTML = content;
        this.detailsModal.show();
    }
    
    toggleLineNumbers() {
        this.lineNumbersVisible = !this.lineNumbersVisible;
        
        if (this.lineNumbersVisible) {
            this.addLineNumbers();
        } else {
            this.removeLineNumbers();
        }
    }
    
    addLineNumbers() {
        const lines = this.container.textContent.split('\\n');
        this.container.innerHTML = '';
        
        lines.forEach((line, index) => {
            const lineDiv = document.createElement('div');
            lineDiv.className = 'text-line';
            lineDiv.style.display = 'flex';
            
            const lineNumber = document.createElement('span');
            lineNumber.className = 'line-number';
            lineNumber.style.minWidth = '40px';
            lineNumber.style.color = '#6c757d';
            lineNumber.style.fontSize = '0.85em';
            lineNumber.style.marginRight = '10px';
            lineNumber.style.textAlign = 'right';
            lineNumber.textContent = index + 1;
            
            const lineContent = document.createElement('span');
            lineContent.className = 'line-content';
            lineContent.style.flex = '1';
            lineContent.textContent = line;
            
            lineDiv.appendChild(lineNumber);
            lineDiv.appendChild(lineContent);
            this.container.appendChild(lineDiv);
        });
    }
    
    removeLineNumbers() {
        // Ricostruisci il contenuto senza numeri di riga
        this.renderAnnotations();
    }
    
    clearSelection() {
        window.getSelection().removeAllRanges();
        this.selectedText = null;
        this.selectedRange = null;
    }
    
    updateStats() {
        // Aggiorna i contatori nell'interfaccia
        const annotationsCount = document.querySelectorAll('.annotation-highlight').length;
        const statsElement = document.querySelector('.col-md-3:nth-child(3) strong');
        if (statsElement && statsElement.textContent === 'Annotazioni:') {
            statsElement.nextSibling.textContent = ` ${annotationsCount}`;
        }
    }
    
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    showToast(message, type = 'info') {
        // Implementazione toast semplice
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const toast = document.createElement('div');
        toast.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Rimuovi automaticamente dopo 5 secondi
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
}
