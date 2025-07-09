"""
Routes per l'integrazione AI
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
import json

from models import db, TextCell, CellAnnotation, ExcelFile, Label, AIConfiguration
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
    """Rivede un'annotazione AI (accetta/rifiuta) - TEMPORANEAMENTE SENZA CSRF"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'accept' o 'reject'
        
        print(f"🔍 DEBUG: Ricevuta richiesta per annotation {annotation_id}, action: {action}")
        
        if action not in ['accept', 'reject']:
            print(f"❌ DEBUG: Azione non valida: {action}")
            return jsonify({'success': False, 'error': 'Azione non valida'}), 400
        
        ai_service = AIAnnotatorService()
        success = ai_service.review_annotation(annotation_id, action, current_user.id)
        
        print(f"✅ DEBUG: Risultato review_annotation: {success}")
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Annotazione {"accettata" if action == "accept" else "rifiutata"} con successo'
            })
        else:
            return jsonify({'success': False, 'error': 'Errore nella revisione'}), 400
            
    except Exception as e:
        print(f"💥 DEBUG: Errore in review_annotation: {e}")
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

@ai_bp.route('/review/test/<int:file_id>')
@login_required
def test_review_file_annotations(file_id):
    """Pagina di test per rivedere le annotazioni AI di un file"""
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
        
        return render_template('ai/test_review.html',
                             excel_file=excel_file,
                             pending_annotations=pending_annotations,
                             total_cells=total_cells,
                             annotated_cells=annotated_cells,
                             ai_annotations_count=ai_annotations_count)
        
    except Exception as e:
        flash(f'Errore nel caricamento: {str(e)}', 'error')
        return redirect(url_for('excel.list_files'))

@ai_bp.route('/config/current')
def get_current_ai_config():
    """Ottiene la configurazione AI attualmente attiva"""
    try:
        active_config = AIConfiguration.query.filter_by(is_active=True).first()
        
        if not active_config:
            return jsonify({
                'success': False, 
                'message': 'Nessuna configurazione AI attiva'
            })
        
        # Determina il modello in base al provider
        if active_config.provider == 'ollama':
            model_name = active_config.ollama_model
        elif active_config.provider == 'openrouter':
            model_name = active_config.openrouter_model
        else:
            model_name = 'Unknown'
        
        return jsonify({
            'success': True,
            'config': {
                'id': active_config.id,
                'name': active_config.name,
                'provider': active_config.provider,
                'model': model_name
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route('/status/<int:file_id>')
def get_ai_status(file_id):
    """Ottiene lo status delle annotazioni AI per un file"""
    try:
        # Verifica che il file esista
        excel_file = ExcelFile.query.get_or_404(file_id)
        
        # Conta le annotazioni AI per questo file
        ai_annotations = CellAnnotation.query.join(TextCell).filter(
            TextCell.excel_file_id == file_id,
            CellAnnotation.is_ai_generated == True
        ).all()
        
        # Conta quelle in attesa di revisione
        pending_annotations = [ann for ann in ai_annotations if ann.status == 'pending_review']
        
        # Conta quelle approvate/rifiutate
        reviewed_annotations = [ann for ann in ai_annotations if ann.status in ['active', 'rejected']]
        approved_annotations = [ann for ann in reviewed_annotations if ann.status == 'active']
        
        return jsonify({
            'success': True,
            'ai_stats': {
                'total': len(ai_annotations),
                'pending': len(pending_annotations),
                'reviewed': len(reviewed_annotations),
                'approved': len(approved_annotations),
                'rejected': len(reviewed_annotations) - len(approved_annotations)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
