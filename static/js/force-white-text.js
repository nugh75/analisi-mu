/**
 * EMERGENCY FIX - Forza il testo bianco nei card-header
 * Questo script JavaScript forza il colore bianco per tutti gli elementi di testo
 * nei card-header, sovrascrivendo qualsiasi stile CSS o inline
 */

(function() {
    'use strict';
    
    function forceWhiteText() {
        // Seleziona tutti i card-header
        const cardHeaders = document.querySelectorAll('.card-header');
        
        cardHeaders.forEach(header => {
            // Forza il colore del card-header stesso
            header.style.setProperty('color', 'white', 'important');
            
            // Seleziona tutti gli elementi figli (escludendo form controls)
            const allElements = header.querySelectorAll('*:not(input):not(textarea):not(select):not(.form-control):not(.form-select)');
            
            allElements.forEach(element => {
                // Forza il colore bianco con la massima priorità
                element.style.setProperty('color', 'white', 'important');
                element.style.setProperty('-webkit-text-fill-color', 'white', 'important');
                element.style.setProperty('text-shadow', '0 1px 2px rgba(0, 0, 0, 0.5)', 'important');
                
                // Rimuovi eventuali classi di colore Bootstrap
                const colorClasses = ['text-dark', 'text-black', 'text-body', 'text-secondary', 
                                    'text-primary', 'text-info', 'text-success', 'text-warning', 'text-danger'];
                colorClasses.forEach(className => {
                    if (element.classList.contains(className)) {
                        element.classList.remove(className);
                    }
                });
            });
        });
    }
    
    // Esegui immediatamente
    forceWhiteText();
    
    // Esegui quando il DOM è pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', forceWhiteText);
    }
    
    // Esegui periodicamente per catturare contenuto caricato dinamicamente
    setInterval(forceWhiteText, 1000);
    
    // Osserva i cambiamenti nel DOM
    if (window.MutationObserver) {
        const observer = new MutationObserver(function(mutations) {
            let shouldUpdate = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    shouldUpdate = true;
                }
            });
            if (shouldUpdate) {
                setTimeout(forceWhiteText, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style']
        });
    }
    
    console.log('🎨 Force White Text script loaded - Emergency fix for card-header text visibility');
})();
