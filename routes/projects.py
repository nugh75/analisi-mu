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

    if hasattr(search_form, 'visibility') and search_form.visibility.data:
        query = query.filter(Project.visibility == search_form.visibility.data)

    # Filtra per ruolo dell'utente nei progetti
    if hasattr(search_form, 'my_role') and search_form.my_role.data:
        role = search_form.my_role.data
        if role == 'owner':
            query = query.filter(Project.owner_id == current_user.id)
        elif role == 'public':
            query = query.filter(Project.visibility == 'public')
        elif role == 'collaborator':
            query = query.filter(
                and_(
                    Project.owner_id != current_user.id,
                    Project.collaborators.like(f'%"user_id": {current_user.id}%')
                )
            )
    
    # Ordina per ultima attività
    query = query.order_by(desc(Project.last_activity), desc(Project.updated_at))
    
    # Paginazione
    projects = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiche rapide
    if current_user.is_admin:
        total_q = Project.query
        active_q = Project.query.filter(Project.status == 'active')
        recent_q = Project.query.filter(Project.last_activity >= datetime.utcnow() - timedelta(days=7))
    else:
        total_q = Project.query.filter(accessible_projects)
        active_q = Project.query.filter(and_(Project.status == 'active', accessible_projects))
        recent_q = Project.query.filter(and_(Project.last_activity >= datetime.utcnow() - timedelta(days=7), accessible_projects))

    stats = {
        'total_projects': total_q.count(),
        'active_projects': active_q.count(),
        'my_projects': Project.query.filter(Project.owner_id == current_user.id).count(),
        'recent_activity': recent_q.count()
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
    
    # Attività recenti (ultimi 5 elementi)
    recent_notes = (
        ProjectNote.query
        .filter_by(project_id=project.id)
        .order_by(desc(ProjectNote.updated_at))
        .limit(5)
        .all()
    )

    # File recenti (Excel + Testo) in forma uniforme
    recent_files_raw = []
    recent_files_raw.extend(project.excel_files[-5:])
    recent_files_raw.extend(project.text_documents[-5:])

    def _uploaded_ts(obj):
        return getattr(obj, 'uploaded_at', None) or getattr(obj, 'created_at', None) or datetime.min

    recent_files_raw.sort(key=_uploaded_ts, reverse=True)
    recent_files = []
    for f in recent_files_raw[:5]:
        if hasattr(f, 'original_filename'):  # ExcelFile
            recent_files.append({
                'id': f.id,
                'name': f.original_filename,
                'type': 'excel',
                'uploaded_at': f.uploaded_at,
                'uploader': f.uploader.username if getattr(f, 'uploader', None) else '—',
                'object': f
            })
        else:  # TextDocument
            recent_files.append({
                'id': f.id,
                'name': getattr(f, 'original_name', f"Documento {f.id}"),
                'type': 'text',
                'uploaded_at': getattr(f, 'created_at', None),
                'uploader': f.uploader.username if getattr(f, 'uploader', None) else '—',
                'object': f
            })
    

    # Collaboratori attivi (sempre visibili)
    collaborators = get_project_collaborators(project)

    # Tutti gli utenti dell'app (per suggerire potenziali collaboratori)
    all_users = User.query.order_by(User.username).all()

    # Id e mappa ruoli (escludi owner)
    collaborator_ids = [c['user'].id for c in collaborators if c.get('role') != 'owner']
    collaborator_roles_map = {c['user'].id: c.get('role') for c in collaborators if c.get('role') != 'owner'}

    return render_template('projects/dashboard.html',
                         project=project,
                         stats=stats,
                         recent_notes=recent_notes,
                         recent_files=recent_files,
                         collaborators=collaborators,
                         all_users=all_users,
                         collaborator_ids=collaborator_ids,
                         collaborator_roles_map=collaborator_roles_map)


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


# Endpoint helper: elenco file non assegnati (per modale di assegnazione)
@projects_bp.route('/<int:project_id>/files/unassigned')
@login_required
def unassigned_files(project_id):
    project = Project.query.get_or_404(project_id)
    if not project.can_edit(current_user):
        return jsonify({'error': 'Unauthorized'}), 403

    # Excel e Documenti non assegnati a nessun progetto
    excel_q = ExcelFile.query.filter(ExcelFile.project_id.is_(None)).order_by(desc(ExcelFile.uploaded_at))
    text_q = TextDocument.query.filter(TextDocument.project_id.is_(None)).order_by(desc(TextDocument.created_at))

    excel = [
        {
            'id': f.id,
            'name': f.original_filename,
            'uploader': f.uploader.username if getattr(f, 'uploader', None) else '—',
            'uploaded_at': f.uploaded_at.isoformat() if f.uploaded_at else None,
            'type': 'excel'
        }
        for f in excel_q.limit(200).all()
    ]
    texts = [
        {
            'id': d.id,
            'name': d.original_name,
            'uploader': d.uploader.username if getattr(d, 'uploader', None) else '—',
            'uploaded_at': d.created_at.isoformat() if d.created_at else None,
            'type': 'text'
        }
        for d in text_q.limit(200).all()
    ]

    return jsonify({'excel': excel, 'texts': texts})


# Assegna una lista di file (excel_ids, text_ids) al progetto
@projects_bp.route('/<int:project_id>/files/assign', methods=['POST'])
@login_required
def assign_files(project_id):
    project = Project.query.get_or_404(project_id)
    if not project.can_edit(current_user):
        flash('Non hai i permessi per modificare i file di questo progetto.', 'error')
        return redirect(url_for('projects.project_files', project_id=project.id))

    # Supporta form-encoded e JSON
    payload = request.get_json(silent=True) or request.form
    excel_ids = payload.get('excel_ids') or []
    text_ids = payload.get('text_ids') or []

    # Se arrivano come stringa CSV da form
    if isinstance(excel_ids, str):
        excel_ids = [int(x) for x in excel_ids.split(',') if x.strip().isdigit()]
    if isinstance(text_ids, str):
        text_ids = [int(x) for x in text_ids.split(',') if x.strip().isdigit()]

    # Se JSON, assicurati siano liste di int
    try:
        excel_ids = [int(x) for x in excel_ids]
        text_ids = [int(x) for x in text_ids]
    except Exception:
        excel_ids = []
        text_ids = []

    assigned = {'excel': 0, 'texts': 0}
    try:
        if excel_ids:
            files = ExcelFile.query.filter(ExcelFile.id.in_(excel_ids)).all()
            for f in files:
                f.project_id = project.id
                assigned['excel'] += 1
        if text_ids:
            docs = TextDocument.query.filter(TextDocument.id.in_(text_ids)).all()
            for d in docs:
                d.project_id = project.id
                assigned['texts'] += 1
        project.last_activity = datetime.utcnow()
        project.update_statistics()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Se la richiesta era AJAX/JSON ritorna JSON
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Errore durante l\'assegnazione: {str(e)}', 'error')
        return redirect(url_for('projects.project_files', project_id=project.id))

    # Risposta
    if request.is_json:
        return jsonify({'success': True, 'assigned': assigned})
    flash(f'Assegnati {assigned["excel"]} file Excel e {assigned["texts"]} documenti al progetto.', 'success')
    return redirect(url_for('projects.project_files', project_id=project.id))


# Disassegna un singolo file dal progetto
@projects_bp.route('/<int:project_id>/files/<string:file_type>/<int:file_id>/unassign', methods=['POST'])
@login_required
def unassign_file(project_id, file_type, file_id):
    project = Project.query.get_or_404(project_id)
    if not project.can_edit(current_user):
        flash('Non hai i permessi per modificare i file di questo progetto.', 'error')
        return redirect(url_for('projects.project_files', project_id=project.id))

    try:
        if file_type == 'excel':
            f = ExcelFile.query.get_or_404(file_id)
            if f.project_id != project.id:
                flash('Il file non appartiene a questo progetto.', 'error')
                return redirect(url_for('projects.project_files', project_id=project.id))
            f.project_id = None
        elif file_type == 'text':
            d = TextDocument.query.get_or_404(file_id)
            if d.project_id != project.id:
                flash('Il documento non appartiene a questo progetto.', 'error')
                return redirect(url_for('projects.project_files', project_id=project.id))
            d.project_id = None
        else:
            flash('Tipo di file non valido.', 'error')
            return redirect(url_for('projects.project_files', project_id=project.id))

        project.last_activity = datetime.utcnow()
        project.update_statistics()
        db.session.commit()
        flash('File rimosso dal progetto.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la rimozione: {str(e)}', 'error')

    # Mantieni parametri di filtro/paginazione se presenti
    args = {
        'project_id': project.id,
        'type': request.args.get('type', 'all'),
        'sort': request.args.get('sort', 'date'),
        'page': request.args.get('page', 1)
    }
    return redirect(url_for('projects.project_files', **args))


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


@projects_bp.route('/<int:project_id>/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(project_id, note_id):
    """Modifica una nota esistente del progetto"""
    project = Project.query.get_or_404(project_id)
    note = ProjectNote.query.filter_by(id=note_id, project_id=project.id).first_or_404()

    if not project.can_edit(current_user):
        flash('Non hai i permessi per modificare note in questo progetto.', 'error')
        return redirect(url_for('projects.project_notes', project_id=project.id))

    # Se nota privata, solo autore o manager
    if note.is_private and (note.author_id != current_user.id) and (not project.can_manage(current_user)):
        flash('Non puoi modificare una nota privata di un altro utente.', 'error')
        return redirect(url_for('projects.project_notes', project_id=project.id))

    form = ProjectNoteForm(obj=note)
    # Precompila i tag
    if note.tags_list:
        form.tags.data = ', '.join(note.tags_list)

    if form.validate_on_submit():
        # Aggiorna
        note.title = form.title.data
        note.content = form.content.data
        note.note_type = form.note_type.data
        note.is_pinned = form.is_pinned.data
        note.is_private = form.is_private.data
        # Tag
        if form.tags.data:
            note.tags_list = [t.strip() for t in form.tags.data.split(',') if t.strip()]
        else:
            note.tags_list = []
        try:
            db.session.commit()
            flash('Nota aggiornata con successo!', 'success')
            return redirect(url_for('projects.project_notes', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante l'aggiornamento: {str(e)}", 'error')

    return render_template('projects/note_form.html', form=form, project=project, action='edit')


@projects_bp.route('/<int:project_id>/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(project_id, note_id):
    """Elimina una nota del progetto"""
    project = Project.query.get_or_404(project_id)
    note = ProjectNote.query.filter_by(id=note_id, project_id=project.id).first_or_404()

    # Solo autore o manager del progetto
    if not (note.author_id == current_user.id or project.can_manage(current_user)):
        flash('Non hai i permessi per eliminare questa nota.', 'error')
        return redirect(url_for('projects.project_notes', project_id=project.id))

    try:
        db.session.delete(note)
        db.session.commit()
        flash('Nota eliminata.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Errore durante l'eliminazione: {str(e)}", 'error')

    return redirect(url_for('projects.project_notes', project_id=project.id))


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

    # Tutti gli utenti dell'app
    all_users = User.query.order_by(User.username).all()

    collaborator_ids = [c['user'].id for c in collaborators if c.get('role') != 'owner']
    collaborator_roles_map = {c['user'].id: c.get('role') for c in collaborators if c.get('role') != 'owner'}

    return render_template('projects/collaborators.html',
                         project=project,
                         collaborators=collaborators,
                         all_users=all_users,
                         collaborator_ids=collaborator_ids,
                         collaborator_roles_map=collaborator_roles_map)


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
    
    # Tutti gli utenti per gestione collaboratori (eccetto owner visualizzato separatamente)
    all_users = User.query.order_by(User.username).all()
    current_collaborator_ids = {c.get('user_id') for c in project.collaborators_list if isinstance(c, dict)}
    collaborators = get_project_collaborators(project, detailed=True)
    collaborator_ids = [c['user'].id for c in collaborators if c.get('role') != 'owner']
    collaborator_roles_map = {c['user'].id: c.get('role') for c in collaborators if c.get('role') != 'owner'}

    return render_template('projects/settings.html', 
                         form=form, 
                         project=project,
                         all_users=all_users,
                         current_collaborator_ids=current_collaborator_ids,
                         collaborators=collaborators,
                         collaborator_ids=collaborator_ids,
                         collaborator_roles_map=collaborator_roles_map)


@projects_bp.route('/<int:project_id>/collaborators/update', methods=['POST'])
@login_required
def update_collaborators(project_id):
    """Aggiorna la lista dei collaboratori (selezione multiutente dalla dashboard o impostazioni)."""
    project = Project.query.get_or_404(project_id)
    if not project.can_manage(current_user):
        flash('Non hai i permessi per modificare i collaboratori.', 'error')
        return redirect(url_for('projects.view_project', project_id=project.id))

    # Ottengo lista di user_id selezionati (checkbox name="collaborators[]")
    selected_ids = request.form.getlist('collaborators[]')
    try:
        selected_ids = [int(uid) for uid in selected_ids if uid.isdigit()]
    except ValueError:
        selected_ids = []

    # Costruisci nuova lista collaboratori (mantieni ruoli esistenti, consenti aggiornamento ruolo da form)
    existing = {c.get('user_id'): c for c in project.collaborators_list if isinstance(c, dict)}
    new_list = []
    now_iso = datetime.utcnow().isoformat()
    for uid in selected_ids:
        # salta l'owner se accidentalmente selezionato
        if uid == project.owner_id:
            continue
        prev = existing.get(uid)
        # ruolo dal form: role_<id>
        role_key = f'role_{uid}'
        role_val = request.form.get(role_key, (prev.get('role') if prev else 'viewer'))
        if prev:
            new_list.append({
                'user_id': uid,
                'role': role_val,
                'added_at': prev.get('added_at', now_iso)
            })
        else:
            new_list.append({
                'user_id': uid,
                'role': role_val,
                'added_at': now_iso
            })

    project.collaborators_list = new_list
    project.last_activity = datetime.utcnow()
    try:
        db.session.commit()
        flash('Collaboratori aggiornati.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore aggiornando i collaboratori: {str(e)}', 'error')

    # Redirect alla pagina di provenienza (dashboard o settings) se passato il ref
    redirect_target = request.form.get('redirect', 'dashboard')
    if redirect_target == 'settings':
        return redirect(url_for('projects.project_settings', project_id=project.id))
    return redirect(url_for('projects.view_project', project_id=project.id))


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
