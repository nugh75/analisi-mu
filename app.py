#!/usr/bin/env python3
"""
Applicazione Flask per la gestione collaborativa dell'etichettatura tematica
di risposte testuali contenute in file Excel.
"""

from flask import Flask
from flask_login import LoginManager
import os

# Importa l'istanza db dai modelli
from models import db

# Inizializzazione delle altre estensioni
login_manager = LoginManager()

def create_app():
    """Factory function per creare l'applicazione Flask"""
    app = Flask(__name__)
    
    # Configurazione
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///analisi_mu.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Inizializzazione estensioni
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurazione Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
    login_manager.login_message_category = 'info'
    
    # Registrazione blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.excel import excel_bp
    from routes.labels import labels_bp
    from routes.annotation import annotation_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(excel_bp, url_prefix='/excel')
    app.register_blueprint(labels_bp, url_prefix='/labels')
    app.register_blueprint(annotation_bp, url_prefix='/annotation')
    
    # Creazione delle cartelle necessarie
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # User loader per Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Creazione delle tabelle del database
    with app.app_context():
        from models import User, Label, ExcelFile, TextCell, CellAnnotation
        db.create_all()
        
        # Creazione utente admin di default se non esiste
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Creazione etichette di default se non esistono
        if Label.query.count() == 0:
            default_labels = [
                Label(name='Positivo', description='Commento positivo', category='Sentiment', color='#28a745'),
                Label(name='Negativo', description='Commento negativo', category='Sentiment', color='#dc3545'),
                Label(name='Neutro', description='Commento neutro', category='Sentiment', color='#6c757d'),
                Label(name='Suggerimento', description='Contiene suggerimenti', category='Tipo', color='#17a2b8'),
                Label(name='Reclamo', description='Contiene reclami', category='Tipo', color='#fd7e14'),
                Label(name='Complimento', description='Contiene complimenti', category='Tipo', color='#20c997'),
            ]
            
            for label in default_labels:
                db.session.add(label)
            
            db.session.commit()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
