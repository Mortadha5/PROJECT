// Système de basculement de thème
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // Appliquer le thème sauvegardé
        this.applyTheme(this.currentTheme);
        
        // Créer le bouton de basculement
        this.createToggleButton();
        
        // Écouter les changements de préférence système
        this.watchSystemTheme();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
        
        // Mettre à jour l'icône du bouton
        this.updateToggleIcon();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        
        // Animation de transition douce
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    createToggleButton() {
        const toggleButton = document.createElement('button');
        toggleButton.className = 'theme-toggle';
        toggleButton.innerHTML = `
            <i class="theme-icon fas fa-sun"></i>
        `;
        
        toggleButton.addEventListener('click', () => this.toggleTheme());
        document.body.appendChild(toggleButton);
        
        this.toggleButton = toggleButton;
        this.updateToggleIcon();
    }

    updateToggleIcon() {
        if (!this.toggleButton) return;
        
        const icon = this.toggleButton.querySelector('.theme-icon');
        
        if (this.currentTheme === 'dark') {
            icon.className = 'theme-icon fas fa-moon';
        } else {
            icon.className = 'theme-icon fas fa-sun';
        }
    }

    watchSystemTheme() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            // Si aucune préférence n'est sauvegardée, utiliser la préférence système
            if (!localStorage.getItem('theme')) {
                this.applyTheme(mediaQuery.matches ? 'dark' : 'light');
            }
            
            // Écouter les changements de préférence système
            mediaQuery.addEventListener('change', (e) => {
                if (!localStorage.getItem('theme-manual')) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
}

// Initialiser le gestionnaire de thème
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Fonction globale pour basculer le thème (utilisable depuis n'importe où)
function toggleTheme() {
    if (window.themeManager) {
        window.themeManager.toggleTheme();
    }
}

