"""
Route per la gestione dei progetti multi-file
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, func
from sqlalchemy.orm import joinedload

from models import (
    db, Project, ProjectNote, ProjectCollaborator, User, ExcelFile, TextDocument, 
    CellAnnotation, TextAnnotation, Label, Category
)
from forms import (
    ProjectForm, ProjectNoteForm, CollaboratorInviteForm, 
    ProjectSearchForm, ProjectFileUploadForm
)

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('/')
@login_required
def list_projects():
    """Lista tutti i progetti accessibili all'utente con filtri"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    search_form = ProjectSearchForm(request.args)
    
    # Query base - progetti accessibili dall'utente
    query = Project.query
    
    # Filtra per accessibilità
    if not current_user.is_admin:
        accessible_projects = or_(
            Project.owner_id == current_user.id,  # Progetti di proprietà
            Project.visibility == 'public',        # Progetti pubblici
            Project.collaborators.like(f'%"user_id": {current_user.id}%')  # Progetti dove è collaboratore
        )
        query = query.filter(accessible_projects)
    
    # Applica filtri di ricerca
    if search_form.search_query.data:
        search_term = f"%{search_form.search_query.data}%"
        query = query.filter(or_(
            Project.name.like(search_term),
            Project.description.like(search_term),
            Project.tags.like(search_term)
        ))
    
    if search_form.project_type.data:
        query = query.filter(Project.project_type == search_form.project_type.data)
    
    if search_form.status.data:
        query = query.filter(Project.status == search_form.status.data)
    
    # Ordina per ultima attività
    query = query.order_by(desc(Project.last_activity), desc(Project.updated_at))
    
    # Paginazione
    projects = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiche rapide
    stats = {
        'total_projects': Project.query.filter(accessible_projects if not current_user.is_admin else True).count(),
        'active_projects': Project.query.filter(
            and_(Project.status == 'active', accessible_projects if not current_user.is_admin else True)
        ).count(),
        'my_projects': Project.query.filter(Project.owner_id == current_user.id).count(),
        'recent_activity': Project.query.filter(
            and_(
                Project.last_activity >= datetime.utcnow() - timedelta(days=7),
                accessible_projects if not current_user.is_admin else True
            )
        ).count()
    }
    
    return render_template('projects/list.html', 
                         projects=projects, 
                         search_form=search_form,
                         stats=stats)


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Crea un nuovo progetto"""
    form = ProjectForm()
    
    if form.validate_on_submit():
        # Processa i tag
        tags_list = []
        if form.tags.data:
            tags_list = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        
        # Crea il progetto
        project = Project(
            name=form.name.data,
            description=form.description.data,
            project_type=form.project_type.data,
            objectives=form.objectives.data,
            methodology=form.methodology.data,
            visibility=form.visibility.data,
            default_annotation_mode=form.default_annotation_mode.data,
            enable_ai_assistance=form.enable_ai_assistance.data,
            auto_assign_collaborators=form.auto_assign_collaborators.data,
            owner_id=current_user.id,
            last_activity=datetime.utcnow()
        )
        
        project.tags_list = tags_list
        
        try:
            db.session.add(project)
            db.session.commit()
            
            flash(f'Progetto "{project.name}" creato con successo!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione del progetto: {str(e)}', 'error')
    
    return render_template('projects/create.html', form=form)


@projects_bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """Dashboard principale del progetto"""
    project = Project.query.get_or_404(project_id)
    
    # Verifica autorizzazioni
    if not project.can_access(current_user):
        flash('Non hai i permessi per accedere a questo progetto.', 'error')
        return redirect(url_for('projects.list_projects'))
    
    # Aggiorna statistiche del progetto
    project.update_statistics()
    db.session.commit()
    
    # Ottieni statistiche dettagliate
    stats = get_project_statistics(project)
    
    # Attività recenti (ultimi 10 elementi)
    recent_notes = ProjectNote.query.filter_by(project_id=project.id)\
                                  .order_by(desc(ProjectNote.updated_at))\
                                  .limit(5).all()
    
    # File recenti
    recent_files = []
    recent_files.extend(project.excel_files[-3:])  # Ultimi 3 file Excel
    recent_files.extend(project.text_documents[-3:])  # Ultimi 3 documenti testo
    recent_files.sort(key=lambda x: x.uploaded_at if hasattr(x, 'uploaded_at') else x.created_at, reverse=True)
    recent_files = recent_files[:5]  # Massimo 5 file totali
    
    # Collaboratori attivi
    collaborators = get_project_collaborators(project)
    
    return render_template('projects/dashboard.html',
                         project=project,
                         stats=stats,
                         recent_notes=recent_notes,
                         recent_files=recent_files,
                         collaborators=collaborators)


@projects_bp.route('/<int:project_id>/files')
@login_required
def project_files(project_id):
    """Vista unificata dei file del progetto"""
    project = Project.query.get_or_404(project_id)
    
    if not project.can_access(current_user):
        flash('Non hai i permessi per accedere a questo progetto.', 'error')
        return redirect(url_for('projects.list_projects'))
    
    # Parametri di filtro
    file_type = request.args.get('type', 'all')  # all, excel, text
    sort_by = request.args.get('sort', 'date')   # date, name, size, annotations
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Combina file Excel e documenti di testo
    files = []
    
    if file_type in ['all', 'excel']:
        for excel_file in project.excel_files:
            files.append({
                'id': excel_file.id,
                'name': excel_file.original_filename,
                'type': 'excel',
                'size': 'N/A',  # TODO: implementare dimensione file
                'uploaded_at': excel_file.uploaded_at,
                'uploader': excel_file.uploader.username,
                'annotations_count': sum(len(cell.annotations) for cell in excel_file.text_cells),
                'cells_count': len(excel_file.text_cells),
                'object': excel_file
            })
    
    if file_type in ['all', 'text']:
        for text_doc in project.text_documents:
            files.append({
                'id': text_doc.id,
                'name': text_doc.original_name,
                'type': 'text',
                'size': f"{text_doc.character_count} caratteri",
                'uploaded_at': text_doc.created_at,
                'uploader': text_doc.uploader.username,
                'annotations_count': len(text_doc.annotations),
                'cells_count': 1,  # Un documento = una "cella"
                'object': text_doc
            })
    
    # Ordinamento
    if sort_by == 'name':
        files.sort(key=lambda x: x['name'].lower())
    elif sort_by == 'annotations':
        files.sort(key=lambda x: x['annotations_count'], reverse=True)
    else:  # default: date
        files.sort(key=lambda x: x['uploaded_at'], reverse=True)
    
    # Paginazione manuale
    total_files = len(files)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_files = files[start_idx:end_idx]
    
    # Crea oggetto di paginazione mock
    class MockPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    pagination = MockPagination(paginated_files, page, per_page, total_files)
    
    return render_template('projects/files.html',
                         project=project,
                         files=pagination,
                         file_type=file_type,
                         sort_by=sort_by)


@projects_bp.route('/<int:project_id>/notes')
@login_required
def project_notes(project_id):
    """Gestione note del progetto"""
    project = Project.query.get_or_404(project_id)
    
    if not project.can_access(current_user):
        flash('Non hai i permessi per accedere a questo progetto.', 'error')
        return redirect(url_for('projects.list_projects'))
    
    page = request.args.get('page', 1, type=int)
    note_type = request.args.get('type', 'all')
    
    # Query base
    query = ProjectNote.query.filter_by(project_id=project.id)
    
    # Filtra per tipo se specificato
    if note_type != 'all':
        query = query.filter(ProjectNote.note_type == note_type)
    
    # Filtra note private se non sei l'autore
    if not project.can_manage(current_user):
        query = query.filter(or_(
            ProjectNote.is_private == False,
            ProjectNote.author_id == current_user.id
        ))
    
    # Ordinamento: note pinned prima, poi per data
    query = query.order_by(desc(ProjectNote.is_pinned), desc(ProjectNote.updated_at))
    
    notes = query.paginate(page=page, per_page=10, error_out=False)
    
    # Statistiche note
    note_stats = {
        'total': ProjectNote.query.filter_by(project_id=project.id).count(),
        'by_type': db.session.query(
            ProjectNote.note_type, 
            func.count(ProjectNote.id)
        ).filter_by(project_id=project.id).group_by(ProjectNote.note_type).all()
    }
    
    return render_template('projects/notes.html',
                         project=project,
                         notes=notes,
                         note_type=note_type,
                         note_stats=note_stats)


@projects_bp.route('/<int:project_id>/notes/create', methods=['GET', 'POST'])
@login_required
def create_note(project_id):
    """Crea una nuova nota per il progetto"""
    project = Project.query.get_or_404(project_id)
    
    if not project.can_edit(current_user):
        flash('Non hai i permessi per aggiungere note a questo progetto.', 'error')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    form = ProjectNoteForm()
    
    if form.validate_on_submit():
        # Processa i tag
        tags_list = []
        if form.tags.data:
            tags_list = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        
        note = ProjectNote(
            project_id=project.id,
            title=form.title.data,
            content=form.content.data,
            note_type=form.note_type.data,
            is_pinned=form.is_pinned.data,
            is_private=form.is_private.data,
            author_id=current_user.id
        )
        
        note.tags_list = tags_list
        
        try:
            db.session.add(note)
            db.session.commit()
            
            flash(f'Nota "{note.title}" creata con successo!', 'success')
            return redirect(url_for('projects.project_notes', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione della nota: {str(e)}', 'error')
    
    return render_template('projects/note_form.html', 
                         form=form, 
                         project=project, 
                         action='create')


@projects_bp.route('/<int:project_id>/collaborators')
@login_required
def manage_collaborators(project_id):
    """Gestione collaboratori del progetto"""
    project = Project.query.get_or_404(project_id)
    
    if not project.can_manage(current_user):
        flash('Non hai i permessi per gestire i collaboratori di questo progetto.', 'error')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    # Ottieni collaboratori dettagliati
    collaborators = get_project_collaborators(project, detailed=True)
    
    return render_template('projects/collaborators.html',
                         project=project,
                         collaborators=collaborators)


@projects_bp.route('/<int:project_id>/settings', methods=['GET', 'POST'])
@login_required
def project_settings(project_id):
    """Impostazioni del progetto"""
    project = Project.query.get_or_404(project_id)
    
    if not project.can_manage(current_user):
        flash('Non hai i permessi per modificare le impostazioni di questo progetto.', 'error')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    form = ProjectForm(obj=project)
    
    # Precompila i tag
    if project.tags_list:
        form.tags.data = ', '.join(project.tags_list)
    
    if form.validate_on_submit():
        # Aggiorna il progetto
        project.name = form.name.data
        project.description = form.description.data
        project.project_type = form.project_type.data
        project.objectives = form.objectives.data
        project.methodology = form.methodology.data
        project.visibility = form.visibility.data
        project.default_annotation_mode = form.default_annotation_mode.data
        project.enable_ai_assistance = form.enable_ai_assistance.data
        project.auto_assign_collaborators = form.auto_assign_collaborators.data
        
        # Aggiorna i tag
        if form.tags.data:
            project.tags_list = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        else:
            project.tags_list = []
        
        try:
            db.session.commit()
            flash('Impostazioni del progetto aggiornate con successo!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('projects/settings.html', 
                         form=form, 
                         project=project)


# ============================================================================
# FUNZIONI HELPER
# ============================================================================

def get_project_statistics(project):
    """Calcola statistiche dettagliate per un progetto"""
    stats = {
        'files': {
            'excel': len(project.excel_files),
            'text': len(project.text_documents),
            'total': len(project.excel_files) + len(project.text_documents)
        },
        'annotations': {
            'total': 0,
            'by_user': {},
            'by_label': {},
            'ai_generated': 0
        },
        'completion': {
            'percentage': project.completion_percentage,
            'annotated_items': 0,
            'total_items': 0
        },
        'activity': {
            'last_activity': project.last_activity,
            'total_collaborators': len(project.collaborators_list) + 1  # +1 per il proprietario
        }
    }
    
    # Conta annotazioni Excel
    for excel_file in project.excel_files:
        for cell in excel_file.text_cells:
            stats['completion']['total_items'] += 1
            if cell.annotations:
                stats['completion']['annotated_items'] += 1
                
            for annotation in cell.annotations:
                stats['annotations']['total'] += 1
                
                # Per utente
                username = annotation.user.username
                stats['annotations']['by_user'][username] = stats['annotations']['by_user'].get(username, 0) + 1
                
                # Per etichetta
                label_name = annotation.label.name
                stats['annotations']['by_label'][label_name] = stats['annotations']['by_label'].get(label_name, 0) + 1
                
                # AI generated
                if annotation.is_ai_generated:
                    stats['annotations']['ai_generated'] += 1
    
    # Conta annotazioni testo
    for text_doc in project.text_documents:
        stats['completion']['total_items'] += 1
        if text_doc.annotations:
            stats['completion']['annotated_items'] += 1
            
        for annotation in text_doc.annotations:
            stats['annotations']['total'] += 1
            
            # Per utente
            username = annotation.user.username
            stats['annotations']['by_user'][username] = stats['annotations']['by_user'].get(username, 0) + 1
            
            # Per etichetta
            label_name = annotation.label.name
            stats['annotations']['by_label'][label_name] = stats['annotations']['by_label'].get(label_name, 0) + 1
            
            # AI generated
            if annotation.is_ai_generated:
                stats['annotations']['ai_generated'] += 1
    
    return stats


def get_project_collaborators(project, detailed=False):
    """Ottiene la lista dei collaboratori del progetto"""
    collaborators = []
    
    # Aggiungi il proprietario
    collaborators.append({
        'user': project.owner,
        'role': 'owner',
        'role_display': 'Proprietario',
        'role_class': 'danger',
        'joined_at': project.created_at,
        'annotations_count': 0,  # TODO: calcolare
        'last_activity': None   # TODO: calcolare
    })
    
    # Aggiungi collaboratori dalla lista JSON
    for collab_data in project.collaborators_list:
        if isinstance(collab_data, dict):
            user = User.query.get(collab_data.get('user_id'))
            if user:
                role = collab_data.get('role', 'viewer')
                collaborators.append({
                    'user': user,
                    'role': role,
                    'role_display': {
                        'moderator': 'Moderatore',
                        'editor': 'Editor',
                        'annotator': 'Annotatore',
                        'viewer': 'Visualizzatore'
                    }.get(role, 'Sconosciuto'),
                    'role_class': {
                        'moderator': 'warning',
                        'editor': 'primary',
                        'annotator': 'success',
                        'viewer': 'secondary'
                    }.get(role, 'secondary'),
                    'joined_at': datetime.fromisoformat(collab_data.get('added_at', project.created_at.isoformat())),
                    'annotations_count': 0,  # TODO: calcolare
                    'last_activity': None   # TODO: calcolare
                })
    
    return collaborators
