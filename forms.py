"""
Form per l'applicazione di etichettatura tematica
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SelectField, IntegerField
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
    category_id = SelectField('Categoria', 
                             coerce=int,
                             validators=[Optional()],
                             description='Seleziona una categoria esistente')
    new_category = StringField('Nuova Categoria', validators=[
        Optional(),
        Length(max=50, message='Il nome della categoria non può superare i 50 caratteri')
    ], description='Oppure crea una nuova categoria')
    new_category_description = TextAreaField('Descrizione Nuova Categoria', validators=[
        Optional(),
        Length(max=500, message='La descrizione non può superare i 500 caratteri')
    ], render_kw={"rows": 2})
    color = StringField('Colore', 
                       validators=[Optional()],
                       widget=ColorInput(),
                       default='#007bff',
                       description='Seleziona un colore per identificare l\'etichetta')

    def __init__(self, *args, **kwargs):
        super(LabelForm, self).__init__(*args, **kwargs)
        from models import Category
        # Popola le scelte delle categorie
        categories = Category.query.order_by(Category.name).all()
        self.category_id.choices = [(0, 'Nessuna categoria')] + [(cat.id, cat.name) for cat in categories]

class CategoryForm(FlaskForm):
    """Form per creare/modificare categorie"""
    name = StringField('Nome Categoria', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=1, max=50, message='Il nome deve essere tra 1 e 50 caratteri')
    ])
    description = TextAreaField('Descrizione', validators=[
        Optional(),
        Length(max=500, message='La descrizione non può superare i 500 caratteri')
    ], render_kw={"rows": 3})
    color = StringField('Colore', 
                       validators=[Optional()],
                       widget=ColorInput(),
                       default='#6c757d',
                       description='Seleziona un colore per la categoria')
    is_active = BooleanField('Attiva', default=True)


class TextDocumentForm(FlaskForm):
    """Form per il caricamento di documenti di testo"""
    file = FileField('File di Testo', validators=[
        FileRequired(message='Seleziona un file'),
        FileAllowed(['txt', 'md', 'docx'], 
                   message='Sono supportati solo file di testo (.txt, .md, .docx)')
    ])
    document_type = SelectField('Tipo Documento', 
                               choices=[
                                   ('focus_group', 'Focus Group'),
                                   ('interview', 'Intervista'),
                                   ('other', 'Altro')
                               ],
                               default='other',
                               validators=[DataRequired()])

class CategoryColorsForm(FlaskForm):
    """Form per l'aggiornamento dei colori delle categorie"""
    pass  # I campi verranno aggiunti dinamicamente nella vista


# ============================================================================
# FORM PER I PROGETTI
# ============================================================================

class ProjectForm(FlaskForm):
    """Form per creare/modificare progetti"""
    name = StringField('Nome Progetto', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=3, max=200, message='Il nome deve essere tra 3 e 200 caratteri')
    ])
    description = TextAreaField('Descrizione', validators=[
        Optional(),
        Length(max=1000, message='La descrizione non può superare i 1000 caratteri')
    ], render_kw={"rows": 4})
    
    project_type = SelectField('Tipo Progetto', 
                              choices=[
                                  ('general', 'Generale'),
                                  ('research', 'Ricerca'),
                                  ('annotation', 'Annotazione'),
                                  ('analysis', 'Analisi'),
                                  ('collaborative', 'Collaborativo')
                              ],
                              default='general',
                              validators=[DataRequired()])
    
    objectives = TextAreaField('Obiettivi', validators=[
        Optional(),
        Length(max=2000, message='Gli obiettivi non possono superare i 2000 caratteri')
    ], render_kw={"rows": 3})
    
    methodology = TextAreaField('Metodologia', validators=[
        Optional(),
        Length(max=2000, message='La metodologia non può superare i 2000 caratteri')
    ], render_kw={"rows": 3})
    
    visibility = SelectField('Visibilità', 
                            choices=[
                                ('private', 'Privato'),
                                ('public', 'Pubblico'),
                                ('restricted', 'Ristretto')
                            ],
                            default='private',
                            validators=[DataRequired()])
    
    default_annotation_mode = SelectField('Modalità Annotazione Predefinita', 
                                        choices=[
                                            ('manual', 'Manuale'),
                                            ('ai_assisted', 'Assistita da AI'),
                                            ('automatic', 'Automatica')
                                        ],
                                        default='manual',
                                        validators=[DataRequired()])
    
    enable_ai_assistance = BooleanField('Abilita Assistenza AI', default=True)
    auto_assign_collaborators = BooleanField('Assegnazione Automatica Collaboratori', default=False)
    
    tags = StringField('Tag', validators=[
        Optional(),
        Length(max=500, message='I tag non possono superare i 500 caratteri')
    ], description='Tag separati da virgola (es: ricerca, qualitativo, interviste)')


class ProjectNoteForm(FlaskForm):
    """Form per creare/modificare note del progetto"""
    title = StringField('Titolo', validators=[
        DataRequired(message='Il titolo è obbligatorio'),
        Length(min=3, max=200, message='Il titolo deve essere tra 3 e 200 caratteri')
    ])
    
    content = TextAreaField('Contenuto', validators=[
        DataRequired(message='Il contenuto è obbligatorio'),
        Length(min=10, message='Il contenuto deve essere di almeno 10 caratteri')
    ], render_kw={"rows": 8})
    
    note_type = SelectField('Tipo Nota', 
                           choices=[
                               ('general', 'Generale'),
                               ('meeting', 'Riunione'),
                               ('decision', 'Decisione'),
                               ('observation', 'Osservazione'),
                               ('todo', 'Da Fare'),
                               ('issue', 'Problema'),
                               ('idea', 'Idea')
                           ],
                           default='general',
                           validators=[DataRequired()])
    
    is_pinned = BooleanField('Fissa in cima', default=False)
    is_private = BooleanField('Nota privata', default=False, 
                             description='Solo tu e i moderatori potrete vedere questa nota')
    
    tags = StringField('Tag', validators=[
        Optional(),
        Length(max=300, message='I tag non possono superare i 300 caratteri')
    ], description='Tag separati da virgola')


class CollaboratorInviteForm(FlaskForm):
    """Form per invitare collaboratori al progetto"""
    username_or_email = StringField('Username o Email', validators=[
        DataRequired(message='Username o email obbligatorio'),
        Length(min=3, max=120)
    ])
    
    role = SelectField('Ruolo', 
                      choices=[
                          ('viewer', 'Visualizzatore'),
                          ('annotator', 'Annotatore'),
                          ('editor', 'Editor'),
                          ('moderator', 'Moderatore')
                      ],
                      default='viewer',
                      validators=[DataRequired()])
    
    can_view_private_notes = BooleanField('Può vedere note private', default=False)
    can_export_data = BooleanField('Può esportare dati', default=False)
    can_manage_files = BooleanField('Può gestire file', default=False)
    
    message = TextAreaField('Messaggio (opzionale)', validators=[
        Optional(),
        Length(max=500, message='Il messaggio non può superare i 500 caratteri')
    ], render_kw={"rows": 3})


class ProjectSearchForm(FlaskForm):
    """Form per la ricerca e filtro dei progetti"""
    search_query = StringField('Cerca', validators=[
        Optional(),
        Length(max=200)
    ], render_kw={"placeholder": "Cerca per nome, descrizione o tag..."})
    
    project_type = SelectField('Tipo', 
                              choices=[
                                  ('', 'Tutti i tipi'),
                                  ('general', 'Generale'),
                                  ('research', 'Ricerca'),
                                  ('annotation', 'Annotazione'),
                                  ('analysis', 'Analisi'),
                                  ('collaborative', 'Collaborativo')
                              ],
                              default='')
    
    status = SelectField('Stato', 
                        choices=[
                            ('', 'Tutti gli stati'),
                            ('active', 'Attivo'),
                            ('completed', 'Completato'),
                            ('archived', 'Archiviato'),
                            ('suspended', 'Sospeso')
                        ],
                        default='')
    
    visibility = SelectField('Visibilità', 
                            choices=[
                                ('', 'Tutte'),
                                ('private', 'Privati'),
                                ('public', 'Pubblici'),
                                ('restricted', 'Ristretti')
                            ],
                            default='')


class ProjectFileUploadForm(FlaskForm):
    """Form per caricare file in un progetto"""
    file = FileField('File', validators=[
        FileRequired(message='Seleziona un file'),
        FileAllowed(['xlsx', 'xls', 'txt', 'md', 'docx'], 
                   message='Formati supportati: Excel (.xlsx, .xls), Testo (.txt, .md, .docx)')
    ])
    
    file_type = SelectField('Tipo File', 
                           choices=[
                               ('excel', 'File Excel'),
                               ('text', 'Documento di Testo')
                           ],
                           validators=[DataRequired()])
    
    document_type = SelectField('Tipo Documento', 
                               choices=[
                                   ('focus_group', 'Focus Group'),
                                   ('interview', 'Intervista'),
                                   ('survey', 'Questionario'),
                                   ('other', 'Altro')
                               ],
                               default='other',
                               description='Solo per documenti di testo')
    
    description = TextAreaField('Descrizione (opzionale)', validators=[
        Optional(),
        Length(max=500, message='La descrizione non può superare i 500 caratteri')
    ], render_kw={"rows": 2})
