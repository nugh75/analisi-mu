// Fallback semplice: forza il colore del testo su sfondi scuri, se necessario.
(function () {
  try {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (!prefersDark) return; // applica solo in dark mode
    const root = document.documentElement;
    const current = getComputedStyle(root).getPropertyValue('--bs-body-color');
    // Se il corpo non è chiaramente leggibile (heuristic), imposta bianco
    if (!current || current.trim() === '' || current.includes('0, 0, 0')) {
      root.style.setProperty('--bs-body-color', '#ffffff');
      root.style.setProperty('--bs-body-color-rgb', '255,255,255');
    }
  } catch (e) {
    // silenzioso
  }
})();
