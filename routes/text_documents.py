"""
Route per la gestione dei documenti di testo (focus group, interviste)
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from docx import Document
import bleach

from models import db, TextDocument, TextAnnotation, Label
from forms import TextDocumentForm

text_documents_bp = Blueprint('text_documents', __name__, url_prefix='/text-documents')

ALLOWED_EXTENSIONS = {'txt', 'md', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # Ridotto a 5MB per performance migliori
MAX_CONTENT_LENGTH = 500000  # 500KB di testo puro (circa 100-150 pagine)

def allowed_file(filename):
    """Verifica se il file è di un tipo consentito"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_format(filename):
    """Estrae il formato del file"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'

def read_text_file(file_path, file_format):
    """Legge il contenuto di un file di testo"""
    try:
        if file_format == 'docx':
            doc = Document(file_path)
            # Ottimizzazione: usa list comprehension più efficiente
            # e processa solo paragrafi non vuoti
            paragraphs = []
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:  # Solo paragrafi con contenuto
                    paragraphs.append(text)
            content = '\n'.join(paragraphs)
        else:  # txt, md
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Sanitizzazione condizionale: solo se contiene HTML
        if '<' in content and '>' in content:
            content = bleach.clean(content, tags=[], strip=True)
        
        return content
    except Exception as e:
        current_app.logger.error(f"Errore nella lettura del file {file_path}: {str(e)}")
        return None

@text_documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload di un nuovo documento di testo"""
    if request.method == 'POST':
        # Verifica presenza file
        if 'file' not in request.files:
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        document_type = request.form.get('document_type', 'other')
        
        if file.filename == '':
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Verifica dimensione file
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                flash('File troppo grande. Dimensione massima: 10MB', 'error')
                return redirect(request.url)
            
            # Genera nome file sicuro
            original_filename = secure_filename(file.filename)
            file_format = get_file_format(original_filename)
            filename = f"{uuid.uuid4().hex}_{original_filename}"
            
            # Salva il file
            uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, filename)
            
            try:
                file.save(file_path)
                
                # Leggi contenuto
                content = read_text_file(file_path, file_format)
                if content is None:
                    os.remove(file_path)
                    flash('Errore nella lettura del file', 'error')
                    return redirect(request.url)
                
                # Verifica lunghezza contenuto
                if len(content) > MAX_CONTENT_LENGTH:
                    os.remove(file_path)
                    flash(f'Il contenuto del documento è troppo lungo. Massimo {MAX_CONTENT_LENGTH//1000}KB di testo', 'error')
                    return redirect(request.url)
                
                # Crea record nel database
                document = TextDocument(
                    filename=filename,
                    original_name=original_filename,
                    content=content,
                    document_type=document_type,
                    file_format=file_format,
                    user_id=current_user.id
                )
                
                # Calcola statistiche in modo più efficiente
                document.word_count = len(content.split()) if content else 0
                document.character_count = len(content) if content else 0
                
                db.session.add(document)
                db.session.commit()
                
                flash('Documento caricato con successo!', 'success')
                return redirect(url_for('text_documents.view', document_id=document.id))
                
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                current_app.logger.error(f"Errore nel caricamento: {str(e)}")
                flash('Errore nel caricamento del file', 'error')
                return redirect(request.url)
        else:
            flash('Tipo di file non supportato. Formati consentiti: TXT, MD, DOCX', 'error')
    
    return render_template('text_documents/upload.html')

@text_documents_bp.route('/list')
@login_required
def list_documents():
    """Lista dei documenti caricati"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtri
    document_type = request.args.get('type')
    search = request.args.get('search')
    
    query = TextDocument.query
    
    # Applica filtri
    if document_type and document_type != 'all':
        query = query.filter_by(document_type=document_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(TextDocument.original_name.ilike(search_term))
    
    # Se non admin, mostra solo i propri documenti
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    
    documents = query.order_by(TextDocument.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiche
    stats = {
        'total': TextDocument.query.count() if current_user.is_admin else 
                TextDocument.query.filter_by(user_id=current_user.id).count(),
        'focus_groups': TextDocument.query.filter_by(document_type='focus_group').count(),
        'interviews': TextDocument.query.filter_by(document_type='interview').count(),
        'other': TextDocument.query.filter_by(document_type='other').count()
    }
    
    return render_template('text_documents/list.html', 
                         documents=documents, 
                         stats=stats,
                         current_type=document_type,
                         current_search=search)

@text_documents_bp.route('/view/<int:document_id>')
@login_required
def view(document_id):
    """Visualizza un documento per l'etichettamento"""
    document = TextDocument.query.get_or_404(document_id)
    
    # Verifica permessi
    if not current_user.is_admin and document.user_id != current_user.id:
        flash('Non hai i permessi per visualizzare questo documento', 'error')
        return redirect(url_for('text_documents.list_documents'))
    
    # Carica etichette disponibili
    labels = Label.query.filter_by(is_active=True).order_by(Label.name).all()
    
    # Carica annotazioni esistenti
    annotations = TextAnnotation.query.filter_by(document_id=document_id)\
                                    .order_by(TextAnnotation.start_position).all()
    
    # Statistiche documento
    stats = {
        'annotations_count': len(annotations),
        'unique_labels': len(set(ann.label_id for ann in annotations)),
        'annotators': len(set(ann.user_id for ann in annotations)),
        'coverage_percentage': 0
    }
    
    # Calcola copertura (caratteri etichettati vs totali)
    if document.character_count > 0:
        annotated_chars = sum(ann.end_position - ann.start_position for ann in annotations)
        stats['coverage_percentage'] = min(100, (annotated_chars / document.character_count) * 100)
    
    return render_template('text_documents/annotate.html',
                         document=document,
                         labels=labels,
                         annotations=annotations,
                         stats=stats)

@text_documents_bp.route('/api/annotate', methods=['POST'])
@login_required
def api_annotate():
    """API per creare una nuova annotazione"""
    try:
        data = request.get_json()
        
        document_id = data.get('document_id')
        text_selection = data.get('text_selection')
        start_position = data.get('start_position')
        end_position = data.get('end_position')
        label_id = data.get('label_id')
        context_before = data.get('context_before', '')
        context_after = data.get('context_after', '')
        
        # Validazioni
        if not all([document_id, text_selection, start_position is not None, 
                   end_position is not None, label_id]):
            return jsonify({'success': False, 'message': 'Dati mancanti'}), 400
        
        # Verifica documento
        document = TextDocument.query.get(document_id)
        if not document:
            return jsonify({'success': False, 'message': 'Documento non trovato'}), 404
        
        # Verifica permessi
        if not current_user.is_admin and document.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permessi insufficienti'}), 403
        
        # Verifica etichetta
        label = Label.query.get(label_id)
        if not label or not label.is_active:
            return jsonify({'success': False, 'message': 'Etichetta non valida'}), 400
        
        # Verifica sovrapposizioni
        overlapping = TextAnnotation.query.filter(
            TextAnnotation.document_id == document_id,
            TextAnnotation.start_position < end_position,
            TextAnnotation.end_position > start_position
        ).first()
        
        if overlapping:
            return jsonify({
                'success': False, 
                'message': 'Sovrapposizione con annotazione esistente'
            }), 400
        
        # Crea annotazione
        annotation = TextAnnotation(
            document_id=document_id,
            text_selection=text_selection,
            start_position=start_position,
            end_position=end_position,
            label_id=label_id,
            user_id=current_user.id,
            context_before=context_before,
            context_after=context_after
        )
        
        db.session.add(annotation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Annotazione creata con successo',
            'annotation': {
                'id': annotation.id,
                'label_name': label.name,
                'label_color': label.color,
                'text_preview': annotation.text_preview,
                'created_at': annotation.created_at.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore nella creazione annotazione: {str(e)}")
        return jsonify({'success': False, 'message': 'Errore interno del server'}), 500

@text_documents_bp.route('/api/annotations/<int:annotation_id>', methods=['DELETE'])
@login_required
def api_delete_annotation(annotation_id):
    """API per eliminare un'annotazione"""
    try:
        annotation = TextAnnotation.query.get_or_404(annotation_id)
        
        # Verifica permessi
        if not current_user.is_admin and annotation.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permessi insufficienti'}), 403
        
        db.session.delete(annotation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Annotazione eliminata con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore nell'eliminazione annotazione: {str(e)}")
        return jsonify({'success': False, 'message': 'Errore interno del server'}), 500

@text_documents_bp.route('/annotations')
@login_required
def manage_annotations():
    """Gestione delle annotazioni create"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filtri
    document_id = request.args.get('document_id', type=int)
    label_id = request.args.get('label_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = TextAnnotation.query.join(TextDocument).join(Label)
    
    # Se non admin, mostra solo le proprie annotazioni o quelle sui propri documenti
    if not current_user.is_admin:
        query = query.filter(
            (TextAnnotation.user_id == current_user.id) |
            (TextDocument.user_id == current_user.id)
        )
    
    # Applica filtri
    if document_id:
        query = query.filter(TextAnnotation.document_id == document_id)
    if label_id:
        query = query.filter(TextAnnotation.label_id == label_id)
    if user_id and current_user.is_admin:
        query = query.filter(TextAnnotation.user_id == user_id)
    
    annotations = query.order_by(TextAnnotation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Dati per i filtri
    documents = TextDocument.query.order_by(TextDocument.original_name).all()
    labels = Label.query.filter_by(is_active=True).order_by(Label.name).all()
    
    return render_template('text_documents/annotations.html',
                         annotations=annotations,
                         documents=documents,
                         labels=labels,
                         current_document=document_id,
                         current_label=label_id,
                         current_user_filter=user_id)

@text_documents_bp.route('/delete/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    """Elimina un documento e tutte le sue annotazioni"""
    document = TextDocument.query.get_or_404(document_id)
    
    # Verifica permessi
    if not current_user.is_admin and document.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permessi insufficienti'}), 403
    
    try:
        # Elimina file fisico
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(uploads_dir, document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Elimina record (le annotazioni vengono eliminate automaticamente per cascade)
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Documento eliminato con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore nell'eliminazione documento: {str(e)}")
        return jsonify({'success': False, 'message': 'Errore interno del server'}), 500
