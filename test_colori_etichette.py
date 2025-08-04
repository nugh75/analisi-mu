#!/usr/bin/env python3
"""
Test per diagnosticare il problema dei colori delle etichette nelle statistiche utente
"""

import os
import sys
import json
from datetime import datetime
import re

# Aggiungi il path del progetto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    from models import Label, Category, User, CellAnnotation, TextCell, db
    
    # Configura l'ambiente per usare il database corretto
    os.environ['DEV_MODE'] = '0'  # Usa il database di produzione
    
    # Crea l'app usando la factory function
    app = create_app()
    database_available = True
except Exception as e:
    print(f"❌ Errore nell'importazione dei moduli o creazione app: {e}")
    print("🔄 Procedo con test limitati (solo template e CSS)")
    app = None
    database_available = False

class TestColoriEtichette:
    def __init__(self):
        self.app = app
        self.database_available = database_available
        self.issues = []
        self.warnings = []
        self.successes = []
        
    def log_issue(self, message, severity="ERROR"):
        """Registra un problema rilevato"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.issues.append(f"[{timestamp}] {severity}: {message}")
        print(f"❌ {severity}: {message}")
    
    def log_warning(self, message):
        """Registra un avviso"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.warnings.append(f"[{timestamp}] WARNING: {message}")
        print(f"⚠️  WARNING: {message}")
    
    def log_success(self, message):
        """Registra un successo"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.successes.append(f"[{timestamp}] SUCCESS: {message}")
        print(f"✅ SUCCESS: {message}")
    
    def test_database_connection(self):
        """Test 1: Verifica la connessione al database"""
        print("\n🔍 Test 1: Verifica connessione database...")
        
        if not self.database_available:
            self.log_warning("Database non disponibile, test saltato")
            return False
            
        try:
            with self.app.app_context():
                # Test semplice query
                result = db.session.execute(db.text("SELECT 1")).scalar()
                if result == 1:
                    self.log_success("Connessione al database OK")
                    return True
                else:
                    self.log_issue("Connessione al database fallita")
                    return False
        except Exception as e:
            self.log_issue(f"Errore connessione database: {e}")
            return False
    
    def test_etichette_colori_database(self):
        """Test 2: Verifica che le etichette abbiano colori nel database"""
        print("\n🔍 Test 2: Verifica colori etichette nel database...")
        
        if not self.database_available:
            self.log_warning("Database non disponibile, test saltato")
            return False
            
        try:
            with self.app.app_context():
                labels = Label.query.all()
                
                if not labels:
                    self.log_warning("Nessuna etichetta trovata nel database")
                    return False
                
                labels_without_color = []
                labels_with_default_color = []
                labels_with_invalid_color = []
                
                for label in labels:
                    print(f"  📋 Etichetta: {label.name}")
                    print(f"     Colore: {label.color}")
                    print(f"     Categoria ID: {label.category_id}")
                    print(f"     Categoria nome: {label.category if hasattr(label, 'category') else 'N/A'}")
                    
                    if not label.color:
                        labels_without_color.append(label.name)
                    elif label.color == '#007bff':  # Colore di default
                        labels_with_default_color.append(label.name)
                    elif not re.match(r'^#[0-9A-Fa-f]{6}$', label.color):
                        labels_with_invalid_color.append(label.name)
                    
                    print(f"     ✓ Colore valido: {re.match(r'^#[0-9A-Fa-f]{6}$', label.color or '') is not None}")
                    print()
                
                # Report dei problemi
                if labels_without_color:
                    self.log_issue(f"Etichette senza colore: {', '.join(labels_without_color)}")
                
                if labels_with_default_color:
                    self.log_warning(f"Etichette con colore di default (#007bff): {', '.join(labels_with_default_color)}")
                
                if labels_with_invalid_color:
                    self.log_issue(f"Etichette con colore invalido: {', '.join(labels_with_invalid_color)}")
                
                valid_labels = len(labels) - len(labels_without_color) - len(labels_with_invalid_color)
                self.log_success(f"Etichette con colori validi: {valid_labels}/{len(labels)}")
                
                return len(labels_without_color) == 0 and len(labels_with_invalid_color) == 0
                
        except Exception as e:
            self.log_issue(f"Errore durante test etichette: {e}")
            return False
    
    def test_categorie_colori_database(self):
        """Test 3: Verifica che le categorie abbiano colori nel database"""
        print("\n🔍 Test 3: Verifica colori categorie nel database...")
        
        if not self.database_available:
            self.log_warning("Database non disponibile, test saltato")
            return False
            
        try:
            with self.app.app_context():
                categories = Category.query.all()
                
                if not categories:
                    self.log_warning("Nessuna categoria trovata nel database")
                    return False
                
                categories_without_color = []
                categories_with_invalid_color = []
                
                for category in categories:
                    print(f"  📂 Categoria: {category.name}")
                    print(f"     Colore: {category.color}")
                    print(f"     Descrizione: {category.description or 'N/A'}")
                    
                    if not category.color:
                        categories_without_color.append(category.name)
                    elif not re.match(r'^#[0-9A-Fa-f]{6}$', category.color):
                        categories_with_invalid_color.append(category.name)
                    
                    print(f"     ✓ Colore valido: {re.match(r'^#[0-9A-Fa-f]{6}$', category.color or '') is not None}")
                    print()
                
                if categories_without_color:
                    self.log_issue(f"Categorie senza colore: {', '.join(categories_without_color)}")
                
                if categories_with_invalid_color:
                    self.log_issue(f"Categorie con colore invalido: {', '.join(categories_with_invalid_color)}")
                
                valid_categories = len(categories) - len(categories_without_color) - len(categories_with_invalid_color)
                self.log_success(f"Categorie con colori validi: {valid_categories}/{len(categories)}")
                
                return len(categories_without_color) == 0 and len(categories_with_invalid_color) == 0
                
        except Exception as e:
            self.log_issue(f"Errore durante test categorie: {e}")
            return False
    
    def test_user_16_statistics_data(self):
        """Test 4: Simula i dati che vengono passati alla pagina statistics/user/16"""
        print("\n🔍 Test 4: Simula dati per statistiche utente 16...")
        
        if not self.database_available:
            self.log_warning("Database non disponibile, test saltato")
            return False
            
        try:
            with self.app.app_context():
                user_id = 16
                user = User.query.get(user_id)
                
                if not user:
                    self.log_warning(f"Utente con ID {user_id} non trovato")
                    return False
                
                print(f"  👤 Utente: {user.username}")
                
                # Simula la query che viene fatta nel route statistics/user/<int:user_id>
                try:
                    from sqlalchemy import func, desc, distinct
                except ImportError:
                    # Fallback se SQLAlchemy non è disponibile
                    print("  ⚠️  SQLAlchemy non disponibile, test semplificato")
                    annotations = CellAnnotation.query.filter_by(user_id=user_id).all()
                    if annotations:
                        self.log_success(f"Trovate {len(annotations)} annotazioni per utente {user_id}")
                        # Verifica manuale dei colori
                        for ann in annotations[:5]:  # Prime 5
                            if ann.label and ann.label.color:
                                print(f"    🏷️  {ann.label.name}: {ann.label.color}")
                            else:
                                self.log_issue(f"Annotazione senza colore etichetta: {ann.id}")
                    return True
                
                # Distribuzione etichette (query dal route)
                label_usage = db.session.query(
                    Label.name,
                    Label.color,
                    Category.name.label('category_name'),
                    func.count(CellAnnotation.id).label('count')
                ).select_from(CellAnnotation).join(Label).join(Category).filter(
                    CellAnnotation.user_id == user_id
                ).group_by(Label.id).order_by(desc('count')).all()
                
                print(f"  📊 Etichette usate dall'utente {user_id}:")
                
                if not label_usage:
                    self.log_warning(f"Nessuna annotazione trovata per l'utente {user_id}")
                    return False
                
                for usage in label_usage:
                    print(f"    🏷️  {usage.name}")
                    print(f"        Colore: {usage.color}")
                    print(f"        Categoria: {usage.category_name}")
                    print(f"        Utilizzi: {usage.count}")
                    
                    # Verifica problemi
                    if not usage.color:
                        self.log_issue(f"Etichetta '{usage.name}' senza colore per utente {user_id}")
                    elif not re.match(r'^#[0-9A-Fa-f]{6}$', usage.color):
                        self.log_issue(f"Etichetta '{usage.name}' ha colore invalido: {usage.color}")
                    else:
                        self.log_success(f"Etichetta '{usage.name}' ha colore valido: {usage.color}")
                    
                    print()
                
                return True
                
        except Exception as e:
            self.log_issue(f"Errore durante test dati utente 16: {e}")
            return False
    
    def test_template_rendering(self):
        """Test 5: Testa il rendering del template user_detail.html"""
        print("\n🔍 Test 5: Test rendering template...")
        try:
            template_path = '/home/nugh75/Git/analisi-mu/templates/statistics/user_detail.html'
            
            if not os.path.exists(template_path):
                self.log_issue(f"Template non trovato: {template_path}")
                return False
            
            # Leggi il template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Verifica che il template usi correttamente i colori
            print("  🔍 Analisi template user_detail.html...")
            
            # Cerca pattern che dovrebbero utilizzare i colori
            color_patterns = [
                r'style="background-color:\s*{{\s*[\w.]+\.color\s*}}"',
                r'background-color:\s*{{\s*[\w.]+\.color\s*}}',
                r'style="background-color:\s*{{\s*[\w._]+color[\w._]*\s*}}"'
            ]
            
            found_color_usage = False
            for pattern in color_patterns:
                matches = re.findall(pattern, template_content, re.IGNORECASE)
                if matches:
                    found_color_usage = True
                    self.log_success(f"Template usa i colori correttamente: {len(matches)} occorrenze trovate")
                    for match in matches:
                        print(f"    🎨 Pattern trovato: {match}")
            
            if not found_color_usage:
                self.log_issue("Template non sembra utilizzare i colori delle etichette")
                # Cerca dove dovrebbero essere i colori
                badge_patterns = [
                    r'<span class="badge"[^>]*>',
                    r'class="badge[^"]*"'
                ]
                for pattern in badge_patterns:
                    matches = re.findall(pattern, template_content, re.IGNORECASE)
                    if matches:
                        print(f"    🔍 Badge trovati che potrebbero mancare colori: {len(matches)}")
                        for match in matches[:3]:  # Mostra solo i primi 3
                            print(f"        {match}")
            
            return found_color_usage
            
        except Exception as e:
            self.log_issue(f"Errore durante test template: {e}")
            return False
    
    def test_css_styles(self):
        """Test 6: Verifica che i CSS supportino correttamente i colori"""
        print("\n🔍 Test 6: Verifica CSS styles...")
        try:
            css_path = '/home/nugh75/Git/analisi-mu/static/css/style.css'
            
            if not os.path.exists(css_path):
                self.log_warning(f"File CSS principale non trovato: {css_path}")
                return False
            
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Verifica che ci siano stili per label-badge e badge
            css_patterns = [
                r'\.label-badge\s*{',
                r'\.badge\s*{',
                r'background-color:\s*var\(',
                r'\.label-display\s*{'
            ]
            
            print("  🎨 Analisi CSS...")
            for pattern in css_patterns:
                matches = re.findall(pattern, css_content, re.IGNORECASE)
                if matches:
                    self.log_success(f"CSS pattern trovato: {pattern} ({len(matches)} occorrenze)")
                else:
                    self.log_warning(f"CSS pattern mancante: {pattern}")
            
            # Cerca override che potrebbero causare problemi
            problematic_patterns = [
                r'background-color:\s*[^;]*!important',
                r'\.badge[^{]*{\s*background-color:\s*[^}]*}',
            ]
            
            for pattern in problematic_patterns:
                matches = re.findall(pattern, css_content, re.IGNORECASE)
                if matches:
                    self.log_warning(f"Possibile override CSS problematico trovato: {len(matches)} occorrenze")
                    for match in matches[:2]:
                        print(f"    ⚠️  {match}")
            
            return True
            
        except Exception as e:
            self.log_issue(f"Errore durante test CSS: {e}")
            return False
    
    def test_api_response(self):
        """Test 7: Testa le API che forniscono dati sulle etichette"""
        print("\n🔍 Test 7: Test API response...")
        
        if not self.database_available:
            self.log_warning("Database non disponibile, test saltato")
            return False
            
        try:
            with self.app.app_context():
                # Simula le chiamate API che potrebbero essere usate
                from routes.labels import labels_bp
                
                # Test API categories-for-ai
                with self.app.test_client() as client:
                    # Simula login (potrebbe essere necessario adattare)
                    response = client.get('/labels/api/categories-for-ai')
                    
                    print(f"  🌐 Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.get_json()
                            if data and 'categories' in data:
                                print(f"  📊 Categorie nell'API: {len(data['categories'])}")
                                for cat in data['categories'][:3]:  # Prime 3
                                    print(f"    📂 {cat.get('name', 'N/A')}: colore {cat.get('color', 'N/A')}")
                                self.log_success("API categories-for-ai funziona correttamente")
                            else:
                                self.log_warning("API response non contiene dati attesi")
                        except Exception as e:
                            self.log_warning(f"Errore parsing JSON API: {e}")
                    else:
                        self.log_warning(f"API non accessibile (status: {response.status_code})")
            
            return True
            
        except Exception as e:
            self.log_issue(f"Errore durante test API: {e}")
            return False
    
    def generate_report(self):
        """Genera un report finale con tutti i problemi rilevati"""
        print("\n" + "="*60)
        print("📋 REPORT FINALE - DIAGNOSI COLORI ETICHETTE")
        print("="*60)
        
        if self.issues:
            print(f"\n❌ PROBLEMI RILEVATI ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.warnings:
            print(f"\n⚠️  AVVISI ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.successes:
            print(f"\n✅ VERIFICHE SUPERATE ({len(self.successes)}):")
            for success in self.successes:
                print(f"  {success}")
        
        print("\n🔧 RACCOMANDAZIONI:")
        
        if any("senza colore" in issue for issue in self.issues):
            print("  1. Aggiorna le etichette nel database assegnando colori validi")
            print("     SQL: UPDATE label SET color = '#007bff' WHERE color IS NULL;")
        
        if any("template non sembra utilizzare" in issue for issue in self.issues):
            print("  2. Modifica il template user_detail.html per usare i colori:")
            print('     Cambia: <span class="badge">{{ label_stat.name }}</span>')
            print('     Con: <span class="badge" style="background-color: {{ label_stat.color }}">{{ label_stat.name }}</span>')
        
        if any("CSS" in warning for warning in self.warnings):
            print("  3. Verifica che i CSS non abbiano override che impediscono i colori inline")
        
        print(f"\n📊 RIEPILOGO: {len(self.issues)} errori, {len(self.warnings)} avvisi, {len(self.successes)} successi")
        
        # Salva report su file
        report_file = f"diagnosi_colori_etichette_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("DIAGNOSI COLORI ETICHETTE\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("PROBLEMI:\n")
                for issue in self.issues:
                    f.write(f"{issue}\n")
                
                f.write("\nAVVISI:\n")
                for warning in self.warnings:
                    f.write(f"{warning}\n")
                
                f.write("\nSUCCESSI:\n")
                for success in self.successes:
                    f.write(f"{success}\n")
            
            print(f"📄 Report salvato in: {report_file}")
        except Exception as e:
            print(f"❌ Errore salvataggio report: {e}")
    
    def run_all_tests(self):
        """Esegue tutti i test"""
        print("🚀 AVVIO DIAGNOSI COLORI ETICHETTE")
        print("=" * 50)
        
        tests = [
            self.test_database_connection,
            self.test_etichette_colori_database,
            self.test_categorie_colori_database,
            self.test_user_16_statistics_data,
            self.test_template_rendering,
            self.test_css_styles,
            self.test_api_response
        ]
        
        if not self.database_available:
            # Se il database non è disponibile, esegui solo i test che non lo richiedono
            tests = [
                self.test_template_rendering,
                self.test_css_styles
            ]
            print("⚠️  Database non disponibile - eseguo solo test template e CSS")
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                self.log_issue(f"Errore durante {test.__name__}: {e}")
                results.append(False)
        
        self.generate_report()
        
        return all(results)

def main():
    """Funzione principale"""
    tester = TestColoriEtichette()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tutti i test sono passati!")
        return 0
    else:
        print("\n💥 Alcuni test hanno fallito. Controlla il report per i dettagli.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
