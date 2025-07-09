"""
Modelli del database per l'applicazione di etichettatura tematica.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Questa istanza db sarà importata da app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modello per gli utenti/etichettatori"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='annotatore')  # 'amministratore' o 'annotatore'
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    annotations = db.relationship('CellAnnotation', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Imposta la password hashata"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la password"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        """Compatibilità con il codice esistente"""
        return self.role == 'amministratore'
    
    def can_manage_users(self):
        """Verifica se l'utente può gestire altri utenti"""
        return self.role == 'amministratore'
    
    def can_access_backup(self):
        """Verifica se l'utente può accedere al backup"""
        return self.role == 'amministratore'
    
    def update_last_login(self):
        """Aggiorna il timestamp dell'ultimo login"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Label(db.Model):
    """Modello per le etichette globali"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    color = db.Column(db.String(7), default='#007bff')  # Colore HEX
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    annotations = db.relationship('CellAnnotation', backref='label', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Label {self.name}>'

class ExcelFile(db.Model):
    """Modello per i file Excel caricati"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    uploader = db.relationship('User', backref='uploaded_files')
    text_cells = db.relationship('TextCell', backref='excel_file', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ExcelFile {self.original_filename}>'

class TextCell(db.Model):
    """Modello per le celle testuali estratte dai file Excel"""
    id = db.Column(db.Integer, primary_key=True)
    excel_file_id = db.Column(db.Integer, db.ForeignKey('excel_file.id'), nullable=False)
    sheet_name = db.Column(db.String(100), nullable=False)
    row_index = db.Column(db.Integer, nullable=False)
    column_index = db.Column(db.Integer, nullable=False)
    column_name = db.Column(db.String(100))
    text_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    annotations = db.relationship('CellAnnotation', backref='text_cell', lazy=True, cascade='all, delete-orphan')
    
    @property
    def cell_reference(self):
        """Restituisce il riferimento della cella (es. A1, B2)"""
        from openpyxl.utils import get_column_letter
        return f"{get_column_letter(self.column_index + 1)}{self.row_index + 1}"
    
    def __repr__(self):
        return f'<TextCell {self.sheet_name}:{self.cell_reference}>'

class CellAnnotation(db.Model):
    """Modello per le annotazioni delle celle"""
    id = db.Column(db.Integer, primary_key=True)
    text_cell_id = db.Column(db.Integer, db.ForeignKey('text_cell.id'), nullable=False)
    label_id = db.Column(db.Integer, db.ForeignKey('label.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vincolo di unicità: un utente può assegnare una etichetta a una cella solo una volta
    __table_args__ = (db.UniqueConstraint('text_cell_id', 'label_id', 'user_id', name='unique_annotation'),)
    
    def __repr__(self):
        return f'<CellAnnotation User:{self.user_id} Label:{self.label_id} Cell:{self.text_cell_id}>'
