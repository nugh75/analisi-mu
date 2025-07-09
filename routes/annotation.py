"""
Routes per l'annotazione delle celle
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from models import TextCell, Label, CellAnnotation, ExcelFile, User, db

annotation_bp = Blueprint('annotation', __name__)

@annotation_bp.route('/cell/<int:cell_id>')
@login_required
def annotate_cell(cell_id):
    """Pagina di annotazione per una singola cella"""
    cell = TextCell.query.get_or_404(cell_id)
    
    # Ottieni tutte le etichette disponibili
    labels = Label.query.order_by(Label.category, Label.name).all()
    
    # Ottieni le annotazioni esistenti per questa cella
    annotations = db.session.query(CellAnnotation, Label, User)\
        .join(Label)\
        .join(User)\
        .filter(CellAnnotation.text_cell_id == cell_id)\
        .order_by(CellAnnotation.created_at.desc())\
        .all()
    
    # Annotazioni dell'utente corrente
    user_annotations = CellAnnotation.query.filter_by(
        text_cell_id=cell_id,
        user_id=current_user.id
    ).all()
    
    user_label_ids = [ann.label_id for ann in user_annotations]
    
    return render_template('annotation/annotate_cell.html',
                         cell=cell,
                         labels=labels,
                         annotations=annotations,
                         user_label_ids=user_label_ids)

@annotation_bp.route('/api/add_annotation', methods=['POST'])
@login_required
def api_add_annotation():
    """API per aggiungere un'annotazione"""
    data = request.get_json()
    
    cell_id = data.get('cell_id')
    label_id = data.get('label_id')
    
    if not cell_id or not label_id:
        return jsonify({'success': False, 'message': 'Parametri mancanti'}), 400
    
    # Verifica che la cella e l'etichetta esistano
    cell = TextCell.query.get(cell_id)
    label = Label.query.get(label_id)
    
    if not cell or not label:
        return jsonify({'success': False, 'message': 'Cella o etichetta non trovata'}), 404
    
    try:
        # Crea l'annotazione
        annotation = CellAnnotation(
            text_cell_id=cell_id,
            label_id=label_id,
            user_id=current_user.id
        )
        
        db.session.add(annotation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Annotazione aggiunta con successo',
            'annotation_id': annotation.id
        })
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Hai già assegnato questa etichetta a questa cella'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Errore del server: {str(e)}'
        }), 500

@annotation_bp.route('/api/remove_annotation', methods=['POST'])
@login_required
def api_remove_annotation():
    """API per rimuovere un'annotazione"""
    data = request.get_json()
    
    cell_id = data.get('cell_id')
    label_id = data.get('label_id')
    
    if not cell_id or not label_id:
        return jsonify({'success': False, 'message': 'Parametri mancanti'}), 400
    
    # Trova l'annotazione dell'utente corrente
    annotation = CellAnnotation.query.filter_by(
        text_cell_id=cell_id,
        label_id=label_id,
        user_id=current_user.id
    ).first()
    
    if not annotation:
        return jsonify({
            'success': False,
            'message': 'Annotazione non trovata'
        }), 404
    
    try:
        db.session.delete(annotation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Annotazione rimossa con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Errore del server: {str(e)}'
        }), 500

@annotation_bp.route('/browse')
@login_required
def browse_annotations():
    """Naviga tra le celle per l'annotazione"""
    page = request.args.get('page', 1, type=int)
    file_id = request.args.get('file_id', type=int)
    sheet_name = request.args.get('sheet', '')
    annotated_only = request.args.get('annotated_only', type=bool)
    
    query = TextCell.query
    
    if file_id:
        query = query.filter_by(excel_file_id=file_id)
    
    if sheet_name:
        query = query.filter_by(sheet_name=sheet_name)
    
    if annotated_only:
        # Solo celle che hanno almeno un'annotazione
        query = query.join(CellAnnotation)
    
    cells = query.order_by(TextCell.excel_file_id, TextCell.sheet_name, 
                          TextCell.row_index, TextCell.column_index)\
                 .paginate(page=page, per_page=10, error_out=False)
    
    # Per i filtri
    files = ExcelFile.query.order_by(ExcelFile.original_filename).all()
    
    if file_id:
        sheets = db.session.query(TextCell.sheet_name)\
                          .filter_by(excel_file_id=file_id)\
                          .distinct().all()
        sheet_names = [sheet[0] for sheet in sheets]
    else:
        sheet_names = []
    
    return render_template('annotation/browse_annotations.html',
                         cells=cells,
                         files=files,
                         sheet_names=sheet_names,
                         current_file_id=file_id,
                         current_sheet=sheet_name,
                         annotated_only=annotated_only)

@annotation_bp.route('/statistics')
@login_required
def statistics():
    """Statistiche sulle annotazioni"""
    # Statistiche generali
    total_cells = TextCell.query.count()
    annotated_cells = db.session.query(TextCell.id)\
        .join(CellAnnotation)\
        .distinct().count()
    
    # Annotazioni per utente
    user_stats = db.session.query(User.username, db.func.count(CellAnnotation.id))\
        .join(CellAnnotation)\
        .group_by(User.id)\
        .order_by(db.desc(db.func.count(CellAnnotation.id)))\
        .all()
    
    # Etichette più utilizzate
    label_stats = db.session.query(Label.name, Label.color, db.func.count(CellAnnotation.id))\
        .join(CellAnnotation)\
        .group_by(Label.id)\
        .order_by(db.desc(db.func.count(CellAnnotation.id)))\
        .limit(20)\
        .all()
    
    # Progress per file
    file_progress = db.session.query(
        ExcelFile.original_filename,
        db.func.count(TextCell.id).label('total_cells'),
        db.func.count(CellAnnotation.id).label('annotated_cells')
    ).outerjoin(TextCell)\
     .outerjoin(CellAnnotation)\
     .group_by(ExcelFile.id)\
     .all()
    
    return render_template('annotation/statistics.html',
                         total_cells=total_cells,
                         annotated_cells=annotated_cells,
                         user_stats=user_stats,
                         label_stats=label_stats,
                         file_progress=file_progress)
