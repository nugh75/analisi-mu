"""
Modelli del database per l'applicazione di etichettatura tematica.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

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
    annotations = db.relationship('CellAnnotation', foreign_keys='CellAnnotation.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
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

class Category(db.Model):
    """Modello per le categorie di etichette"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6c757d')  # Colore HEX
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    labels = db.relationship('Label', foreign_keys='Label.category_id', back_populates='category_obj')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Label(db.Model):
    """Modello per le etichette globali"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.Column(db.String(50))  # Manteniamo per compatibilità, sarà deprecato
    color = db.Column(db.String(7), default='#007bff')  # Colore HEX
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    annotations = db.relationship('CellAnnotation', backref='label', lazy=True, cascade='all, delete-orphan')
    category_obj = db.relationship('Category', foreign_keys=[category_id], back_populates='labels')
    
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
    # annotations verranno creati automaticamente dal backref in CellAnnotation
    
    @property
    def cell_reference(self):
        """Restituisce il riferimento della cella (es. A1, B2)"""
        from openpyxl.utils import get_column_letter
        return f"{get_column_letter(self.column_index + 1)}{self.row_index + 1}"
    
    def __repr__(self):
        return f'<TextCell {self.sheet_name}:{self.cell_reference}>'

class AIConfiguration(db.Model):
    """Configurazione per i provider AI"""
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(20), nullable=False)  # 'ollama' o 'openrouter'
    name = db.Column(db.String(100), nullable=False)  # Nome descrittivo
    
    # Configurazione Ollama
    ollama_url = db.Column(db.String(255))
    ollama_model = db.Column(db.String(100))
    
    # Configurazione OpenRouter
    openrouter_api_key = db.Column(db.String(255))
    openrouter_model = db.Column(db.String(100))
    
    # Configurazione generale
    is_active = db.Column(db.Boolean, default=True)
    max_tokens = db.Column(db.Integer, default=1000)
    temperature = db.Column(db.Float, default=0.7)
    system_prompt = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'name': self.name,
            'ollama_url': self.ollama_url,
            'ollama_model': self.ollama_model,
            'openrouter_model': self.openrouter_model,
            'is_active': self.is_active,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

class OpenRouterModel(db.Model):
    """Modelli disponibili su OpenRouter"""
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    context_length = db.Column(db.Integer)
    pricing_prompt = db.Column(db.Float)  # Prezzo per token di input
    pricing_completion = db.Column(db.Float)  # Prezzo per token di output
    is_free = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OllamaModel(db.Model):
    """Modelli disponibili su Ollama"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    size = db.Column(db.BigInteger)  # Dimensione in bytes
    digest = db.Column(db.String(100))
    modified_at = db.Column(db.DateTime)
    is_pulled = db.Column(db.Boolean, default=False)
    pull_progress = db.Column(db.Float, default=0.0)  # Progresso del download 0-100
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('name', 'tag', name='unique_model_tag'),)

class CellAnnotation(db.Model):
    """Modello per le annotazioni delle celle"""
    id = db.Column(db.Integer, primary_key=True)
    text_cell_id = db.Column(db.Integer, db.ForeignKey('text_cell.id'), nullable=False)
    label_id = db.Column(db.Integer, db.ForeignKey('label.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Campi specifici per AI
    is_ai_generated = db.Column(db.Boolean, default=False)
    ai_confidence = db.Column(db.Float)  # Confidence score 0-1
    ai_model = db.Column(db.String(100))  # Modello AI utilizzato
    ai_provider = db.Column(db.String(20))  # Provider AI (ollama/openrouter)
    status = db.Column(db.String(20), default='active')  # active, pending_review, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Chi ha approvato/rifiutato
    reviewed_at = db.Column(db.DateTime)
    
    # Relazioni
    text_cell = db.relationship('TextCell', backref='annotations')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'text_cell_id': self.text_cell_id,
            'label_id': self.label_id,
            'user_id': self.user_id,
            'is_ai_generated': self.is_ai_generated,
            'ai_confidence': self.ai_confidence,
            'ai_model': self.ai_model,
            'ai_provider': self.ai_provider,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }
    
    def __repr__(self):
        return f'<CellAnnotation {self.id}: Cell {self.text_cell_id} -> Label {self.label_id}>'
