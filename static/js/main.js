// JavaScript principale per Analisi MU

document.addEventListener('DOMContentLoaded', function() {
    // Inizializzazione tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inizializzazione popovers Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts dopo 5 secondi
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        }
    });

    // Conferma eliminazione
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirmDelete || 'Sei sicuro di voler eliminare questo elemento?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-resize textarea
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        // Trigger iniziale
        textarea.dispatchEvent(new Event('input'));
    });

    // Search functionality
    const searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const targetSelector = this.dataset.searchTarget;
            const targets = document.querySelectorAll(targetSelector);
            
            targets.forEach(target => {
                const text = target.textContent.toLowerCase();
                const shouldShow = text.includes(searchTerm);
                target.style.display = shouldShow ? '' : 'none';
            });
        });
    });

    // File upload drag and drop
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    fileUploadAreas.forEach(area => {
        const fileInput = area.querySelector('input[type="file"]');
        
        if (fileInput) {
            area.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('dragover');
            });

            area.addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.classList.remove('dragover');
            });

            area.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    // Trigger change event
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            area.addEventListener('click', function() {
                fileInput.click();
            });

            fileInput.addEventListener('change', function() {
                if (this.files.length > 0) {
                    const fileName = this.files[0].name;
                    const fileNameDisplay = area.querySelector('.file-name-display');
                    if (fileNameDisplay) {
                        fileNameDisplay.textContent = fileName;
                    }
                }
            });
        }
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('[data-copy-text]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.dataset.copyText;
            navigator.clipboard.writeText(textToCopy).then(() => {
                showToast('Testo copiato negli appunti!', 'success');
            }).catch(() => {
                showToast('Errore durante la copia', 'error');
            });
        });
    });

    // Toggle visibility
    const toggleButtons = document.querySelectorAll('[data-toggle-target]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetSelector = this.dataset.toggleTarget;
            const target = document.querySelector(targetSelector);
            if (target) {
                target.style.display = target.style.display === 'none' ? '' : 'none';
                
                // Update button text/icon if needed
                const showText = this.dataset.showText;
                const hideText = this.dataset.hideText;
                if (showText && hideText) {
                    const isHidden = target.style.display === 'none';
                    this.textContent = isHidden ? showText : hideText;
                }
            }
        });
    });

    // Progress bar animation
    const progressBars = document.querySelectorAll('.progress-bar[data-animate]');
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.transition = 'width 1s ease-in-out';
            bar.style.width = targetWidth;
        }, 100);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            form.classList.add('was-validated');
        });
    });

    // Real-time character counter
    const textInputsWithCounter = document.querySelectorAll('[data-max-length]');
    textInputsWithCounter.forEach(input => {
        const maxLength = parseInt(input.dataset.maxLength);
        const counter = document.createElement('small');
        counter.className = 'form-text text-muted character-counter';
        input.parentNode.appendChild(counter);
        
        function updateCounter() {
            const remaining = maxLength - input.value.length;
            counter.textContent = `${input.value.length}/${maxLength} caratteri`;
            
            if (remaining < 10) {
                counter.className = 'form-text text-warning character-counter';
            } else if (remaining < 0) {
                counter.className = 'form-text text-danger character-counter';
            } else {
                counter.className = 'form-text text-muted character-counter';
            }
        }
        
        input.addEventListener('input', updateCounter);
        updateCounter(); // Initial call
    });

    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-save functionality (for future implementation)
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        let saveTimeout;
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    // Auto-save logic here
                    console.log('Auto-saving form data...');
                }, 2000);
            });
        });
    });
});

// Utility functions

/**
 * Mostra un toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    
    bsToast.show();
    
    // Remove element after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Ottiene o crea il container per i toast
 */
function getOrCreateToastContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Mostra un loading spinner
 */
function showLoading(target = document.body) {
    target.classList.add('loading');
}

/**
 * Nasconde il loading spinner
 */
function hideLoading(target = document.body) {
    target.classList.remove('loading');
}

/**
 * Debounce function per limitare la frequenza di chiamate
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Formatta una data in formato locale
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    return new Intl.DateTimeFormat('it-IT', finalOptions).format(new Date(date));
}

/**
 * Ottiene il token CSRF
 */
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name=csrf-token]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    
    const hiddenInput = document.querySelector('input[name="csrf_token"]');
    if (hiddenInput) {
        return hiddenInput.value;
    }
    
    return null;
}

/**
 * Wrapper per fetch con handling degli errori
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Esporta le funzioni globalmente
window.AnalisiMU = {
    showToast,
    showLoading,
    hideLoading,
    debounce,
    formatDate,
    getCSRFToken,
    apiRequest
};
