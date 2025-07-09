"""
Routes per l'integrazione AI
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
import json

from models import db, TextCell, CellAnnotation, ExcelFile, Label
from services.ai_annotator import AIAnnotatorService

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/generate/<int:file_id>', methods=['POST'])
@login_required
def generate_annotations(file_id):
    """Genera annotazioni AI per un file"""
    try:
        # Verifica che il file esista
        excel_file = ExcelFile.query.get_or_404(file_id)
        
        # Parametri opzionali
        batch_size = request.json.get('batch_size', 20) if request.is_json else 20
        
        # Inizializza il servizio AI
        ai_service = AIAnnotatorService()
        
        # Genera le annotazioni
        result = ai_service.generate_annotations(file_id, batch_size)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'total_processed': result.get('total_processed', 0),
            'annotations_count': len(result.get('annotations', []))
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/pending/<int:file_id>')
@login_required
def get_pending_annotations(file_id):
    """Ottiene le annotazioni AI in attesa di revisione per un file"""
    try:
        ai_service = AIAnnotatorService()
        pending_annotations = ai_service.get_pending_annotations(file_id)
        
        return jsonify({
            'success': True,
            'annotations': pending_annotations,
            'count': len(pending_annotations)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/review/<int:annotation_id>', methods=['POST'])
@login_required
def review_annotation(annotation_id):
    """Rivede un'annotazione AI (accetta/rifiuta)"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'accept' o 'reject'
        
        if action not in ['accept', 'reject']:
            return jsonify({'success': False, 'error': 'Azione non valida'}), 400
        
        ai_service = AIAnnotatorService()
        success = ai_service.review_annotation(annotation_id, action, current_user.id)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Annotazione {"accettata" if action == "accept" else "rifiutata"} con successo'
            })
        else:
            return jsonify({'success': False, 'error': 'Errore nella revisione'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/review/batch', methods=['POST'])
@login_required
def batch_review_annotations():
    """Rivede multiple annotazioni AI in batch"""
    try:
        data = request.get_json()
        annotation_ids = data.get('annotation_ids', [])
        action = data.get('action')  # 'accept' o 'reject'
        
        if action not in ['accept', 'reject']:
            return jsonify({'success': False, 'error': 'Azione non valida'}), 400
        
        ai_service = AIAnnotatorService()
        success_count = 0
        
        for annotation_id in annotation_ids:
            if ai_service.review_annotation(annotation_id, action, current_user.id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count}/{len(annotation_ids)} annotazioni processate',
            'processed': success_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/review/file/<int:file_id>')
@login_required
def review_file_annotations(file_id):
    """Pagina per rivedere le annotazioni AI di un file"""
    try:
        # Verifica che il file esista
        excel_file = ExcelFile.query.get_or_404(file_id)
        
        # Ottiene le annotazioni pending
        ai_service = AIAnnotatorService()
        pending_annotations = ai_service.get_pending_annotations(file_id)
        
        # Statistiche
        total_cells = TextCell.query.filter_by(excel_file_id=file_id).count()
        annotated_cells = db.session.query(CellAnnotation.text_cell_id).join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.status == 'active'
        ).distinct().count()
        
        ai_annotations_count = CellAnnotation.query.join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.is_ai_generated == True
        ).count()
        
        return render_template('ai/review_annotations.html',
                             excel_file=excel_file,
                             pending_annotations=pending_annotations,
                             total_cells=total_cells,
                             annotated_cells=annotated_cells,
                             ai_annotations_count=ai_annotations_count)
        
    except Exception as e:
        flash(f'Errore nel caricamento: {str(e)}', 'error')
        return redirect(url_for('excel.list_files'))

@ai_bp.route('/status/<int:file_id>')
@login_required
def get_ai_status(file_id):
    """Ottiene lo stato dell'elaborazione AI per un file"""
    try:
        # Statistiche generali
        total_cells = TextCell.query.filter_by(excel_file_id=file_id).count()
        
        # Annotazioni totali (umane + AI accettate)
        annotated_cells = db.session.query(CellAnnotation.text_cell_id).join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.status == 'active'
        ).distinct().count()
        
        # Annotazioni AI
        ai_pending = CellAnnotation.query.join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.is_ai_generated == True,
            CellAnnotation.status == 'pending_review'
        ).count()
        
        ai_accepted = CellAnnotation.query.join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.is_ai_generated == True,
            CellAnnotation.status == 'active'
        ).count()
        
        ai_rejected = CellAnnotation.query.join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.is_ai_generated == True,
            CellAnnotation.status == 'rejected'
        ).count()
        
        return jsonify({
            'success': True,
            'total_cells': total_cells,
            'annotated_cells': annotated_cells,
            'completion_percentage': round((annotated_cells / total_cells) * 100, 1) if total_cells > 0 else 0,
            'ai_stats': {
                'pending': ai_pending,
                'accepted': ai_accepted,
                'rejected': ai_rejected,
                'total': ai_pending + ai_accepted + ai_rejected
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/config/current')
@login_required
def get_current_config():
    """Ottiene la configurazione AI attiva"""
    try:
        ai_service = AIAnnotatorService()
        config = ai_service.get_active_configuration()
        
        if not config:
            return jsonify({'success': False, 'error': 'Nessuna configurazione AI attiva'})
        
        return jsonify({
            'success': True,
            'config': {
                'id': config.id,
                'provider': config.provider,
                'name': config.name,
                'model': config.ollama_model or config.openrouter_model,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
