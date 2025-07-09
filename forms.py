"""
Form per l'applicazione di etichettatura tematica
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from wtforms.widgets import ColorInput

class LoginForm(FlaskForm):
    """Form per il login"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')

class RegisterForm(FlaskForm):
    """Form per la registrazione"""
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=80, message='L\'username deve essere tra 4 e 80 caratteri')
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Inserisci un indirizzo email valido'),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='La password deve essere di almeno 6 caratteri')
    ])
    password_confirm = PasswordField('Conferma Password', validators=[
        DataRequired(),
        EqualTo('password', message='Le password non coincidono')
    ])

class UploadForm(FlaskForm):
    """Form per il caricamento di file Excel"""
    file = FileField('File Excel', validators=[
        FileRequired(message='Seleziona un file'),
        FileAllowed(['xlsx', 'xls'], message='Sono supportati solo file Excel (.xlsx, .xls)')
    ])

class LabelForm(FlaskForm):
    """Form per creare/modificare etichette"""
    name = StringField('Nome Etichetta', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=1, max=100, message='Il nome deve essere tra 1 e 100 caratteri')
    ])
    description = TextAreaField('Descrizione', validators=[
        Optional(),
        Length(max=500, message='La descrizione non può superare i 500 caratteri')
    ], render_kw={"rows": 3})
    category = StringField('Categoria', validators=[
        Optional(),
        Length(max=50, message='La categoria non può superare i 50 caratteri')
    ])
    color = StringField('Colore', 
                       validators=[Optional()],
                       widget=ColorInput(),
                       default='#007bff',
                       description='Seleziona un colore per identificare l\'etichetta')

    def __init__(self, *args, **kwargs):
        super(LabelForm, self).__init__(*args, **kwargs)
        # Aggiungi suggerimenti per le categorie più comuni
        self.category.render_kw = {
            'list': 'category-suggestions',
            'placeholder': 'es. emozione, opinione, strategia...'
        }
