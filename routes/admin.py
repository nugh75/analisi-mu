"""
Routes per l'amministrazione del sistema
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
import os
import json
import zipfile
from datetime import datetime
import shutil

from models import User, Label, ExcelFile, TextCell, CellAnnotation, db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator per verificare che l'utente sia amministratore"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage_users():
            flash('Accesso negato. Sono richiesti privilegi di amministratore.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """Gestione degli utenti"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Crea un nuovo utente"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'annotatore')
        
        # Validazione
        if not username or not email or not password:
            flash('Tutti i campi sono obbligatori.', 'error')
            return render_template('admin/create_user.html')
        
        # Verifica se l'utente esiste già
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username o email già in uso.', 'error')
            return render_template('admin/create_user.html')
        
        # Crea il nuovo utente
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f'Utente "{username}" creato con successo.', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione dell\'utente: {str(e)}', 'error')
    
    return render_template('admin/create_user.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Modifica un utente"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)
        user.role = request.form.get('role', user.role)
        user.is_active = request.form.get('is_active') == 'on'
        
        # Cambia password solo se fornita
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)
        
        try:
            db.session.commit()
            flash(f'Utente "{user.username}" aggiornato con successo.', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Attiva/disattiva un utente"""
    user = User.query.get_or_404(user_id)
    
    # Non permettere di disattivare se stesso
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Non puoi disattivare il tuo account.'})
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'attivato' if user.is_active else 'disattivato'
        return jsonify({
            'success': True, 
            'message': f'Utente {status} con successo.',
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'})

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Elimina un utente"""
    user = User.query.get_or_404(user_id)
    
    # Non permettere di eliminare se stesso
    if user.id == current_user.id:
        flash('Non puoi eliminare il tuo account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    try:
        # Le annotazioni verranno eliminate automaticamente per le relazioni cascade
        db.session.delete(user)
        db.session.commit()
        flash(f'Utente "{user.username}" eliminato con successo.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Profilo utente per cambiare password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validazione
        if not current_password or not new_password or not confirm_password:
            flash('Tutti i campi sono obbligatori.', 'error')
            return render_template('admin/profile.html')
        
        if not current_user.check_password(current_password):
            flash('Password attuale non corretta.', 'error')
            return render_template('admin/profile.html')
        
        if new_password != confirm_password:
            flash('Le nuove password non coincidono.', 'error')
            return render_template('admin/profile.html')
        
        if len(new_password) < 6:
            flash('La password deve essere di almeno 6 caratteri.', 'error')
            return render_template('admin/profile.html')
        
        # Aggiorna la password
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Password aggiornata con successo.', 'success')
            return redirect(url_for('admin.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('admin/profile.html')

@admin_bp.route('/backup')
@login_required
@admin_required
def backup_page():
    """Pagina di gestione backup"""
    # Statistiche del sistema
    stats = {
        'users_count': User.query.count(),
        'labels_count': Label.query.count(),
        'files_count': ExcelFile.query.count(),
        'cells_count': TextCell.query.count(),
        'annotations_count': CellAnnotation.query.count()
    }
    
    return render_template('admin/backup.html', stats=stats)

@admin_bp.route('/backup/create')
@login_required
@admin_required
def create_backup():
    """Crea un backup completo del sistema"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backup_{timestamp}'
        backup_path = os.path.join('backups', backup_dir)
        
        # Crea la directory di backup
        os.makedirs(backup_path, exist_ok=True)
        os.makedirs('backups', exist_ok=True)
        
        # Backup del database
        db_source = 'instance/analisi_mu.db'
        if os.path.exists(db_source):
            shutil.copy2(db_source, os.path.join(backup_path, 'analisi_mu.db'))
        
        # Backup dei file caricati
        uploads_source = 'uploads'
        if os.path.exists(uploads_source):
            shutil.copytree(uploads_source, os.path.join(backup_path, 'uploads'))
        
        # Backup delle configurazioni (esporta dati in JSON)
        backup_data = {
            'created_at': datetime.now().isoformat(),
            'users': [{
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in User.query.all()],
            'labels': [{
                'id': l.id,
                'name': l.name,
                'description': l.description,
                'category': l.category,
                'color': l.color
            } for l in Label.query.all()],
            'excel_files': [{
                'id': f.id,
                'original_filename': f.original_filename,
                'uploaded_at': f.uploaded_at.isoformat() if f.uploaded_at else None,
                'uploaded_by': f.uploaded_by
            } for f in ExcelFile.query.all()]
        }
        
        with open(os.path.join(backup_path, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Crea un file ZIP
        zip_path = f'backups/backup_{timestamp}.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        # Rimuovi la directory temporanea
        shutil.rmtree(backup_path)
        
        flash(f'Backup creato con successo: backup_{timestamp}.zip', 'success')
        return send_file(zip_path, as_attachment=True, download_name=f'backup_{timestamp}.zip')
        
    except Exception as e:
        flash(f'Errore durante la creazione del backup: {str(e)}', 'error')
        return redirect(url_for('admin.backup_page'))

@admin_bp.route('/system_stats')
@login_required
@admin_required
def system_stats():
    """Statistiche del sistema"""
    stats = {
        'users': {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count(),
            'administrators': User.query.filter_by(role='amministratore').count(),
            'annotators': User.query.filter_by(role='annotatore').count()
        },
        'content': {
            'labels': Label.query.count(),
            'excel_files': ExcelFile.query.count(),
            'text_cells': TextCell.query.count(),
            'annotations': CellAnnotation.query.count()
        },
        'recent_activity': {
            'recent_users': User.query.order_by(User.last_login.desc()).limit(5).all(),
            'recent_files': ExcelFile.query.order_by(ExcelFile.uploaded_at.desc()).limit(5).all()
        }
    }
    
    return render_template('admin/system_stats.html', stats=stats)
