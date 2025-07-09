"""
Routes per l'annotazione delle celle
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
import plotly.graph_objs as go
import plotly.utils
import json
import os
from collections import defaultdict

from models import TextCell, Label, CellAnnotation, ExcelFile, User, db

annotation_bp = Blueprint('annotation', __name__)

@annotation_bp.route('/cell/<int:cell_id>', methods=['GET', 'POST'])
@login_required
def annotate_cell(cell_id):
    """Pagina di annotazione per una singola cella"""
    cell = TextCell.query.get_or_404(cell_id)
    
    # Ottieni tutte le etichette disponibili
    # Ordiniamo prima per categoria (trattando None come stringa vuota) poi per nome
    labels = Label.query.all()
    labels.sort(key=lambda x: (x.category or '', x.name))
    
    # Ottieni tutte le categorie disponibili
    from models import Category
    categories = Category.query.order_by(Category.name).all()
    
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
    
    next_url = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        # Esempio: gestione di una form classica (aggiungi qui la logica di salvataggio se serve)
        # ...
        flash('Annotazione salvata!', 'success')
        return redirect(next_url or url_for('annotation.browse_annotations'))

    return render_template('annotation/annotate_cell.html',
                         cell=cell,
                         labels=labels,
                         categories=categories,
                         annotations=annotations,
                         user_label_ids=user_label_ids,
                         next_url=next_url)

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
    annotated_only = request.args.get('annotated_only', '')
    view_mode = request.args.get('view_mode', 'classic')
    selected_question = request.args.get('question', '')
    ajax = request.args.get('ajax', '')
    
    # Se è una richiesta AJAX, restituisci solo i dati dei filtri
    if ajax == '1' and file_id:
        sheets = db.session.query(TextCell.sheet_name)\
                          .filter_by(excel_file_id=file_id)\
                          .distinct().all()
        sheet_names = [sheet[0] for sheet in sheets]
        
        questions = db.session.query(TextCell.column_name)\
                             .filter_by(excel_file_id=file_id)\
                             .distinct()\
                             .order_by(TextCell.column_name)\
                             .all()
        question_names = [q[0] for q in questions if q[0]]
        
        return jsonify({
            'sheets': sheet_names,
            'questions': question_names
        })
    
    query = TextCell.query
    
    if file_id:
        query = query.filter_by(excel_file_id=file_id)
    
    if sheet_name:
        query = query.filter_by(sheet_name=sheet_name)
        
    if selected_question:
        query = query.filter_by(column_name=selected_question)
    
    if annotated_only == '1':
        # Solo celle che hanno almeno un'annotazione
        query = query.join(CellAnnotation).distinct()
    elif annotated_only == '0':
        # Solo celle non annotate
        query = query.outerjoin(CellAnnotation).filter(CellAnnotation.id.is_(None))
    
    cells = query.order_by(TextCell.excel_file_id, TextCell.sheet_name, 
                          TextCell.row_index, TextCell.column_index)\
                 .paginate(page=page, per_page=20, error_out=False)
    
    # Per i filtri
    files = ExcelFile.query.order_by(ExcelFile.original_filename).all()
    
    # Ottieni tutti i fogli disponibili
    if file_id:
        # Se è selezionato un file, mostra solo i fogli di quel file
        sheets = db.session.query(TextCell.sheet_name)\
                          .filter_by(excel_file_id=file_id)\
                          .distinct().all()
        sheet_names = [sheet[0] for sheet in sheets]
        
        # Ottieni tutte le domande/colonne per il file selezionato
        questions = db.session.query(TextCell.column_name)\
                             .filter_by(excel_file_id=file_id)\
                             .distinct()\
                             .order_by(TextCell.column_name)\
                             .all()
        question_names = [q[0] for q in questions if q[0]]
    else:
        # Se non è selezionato nessun file, mostra tutti i fogli di tutti i file
        sheets = db.session.query(TextCell.sheet_name)\
                          .distinct().all()
        sheet_names = [sheet[0] for sheet in sheets]
        
        # Ottieni tutte le domande/colonne di tutti i file
        questions = db.session.query(TextCell.column_name)\
                             .distinct()\
                             .order_by(TextCell.column_name)\
                             .all()
        question_names = [q[0] for q in questions if q[0]]
    
    # Per la Vista per Domanda, calcola le statistiche per domanda
    questions_stats = []
    if view_mode == 'per_domanda':
        # Ottieni statistiche per ogni domanda come in questions_overview
        base_query = db.session.query(
            TextCell.column_name,
            db.func.count(TextCell.id).label('total_responses'),
            db.func.count(CellAnnotation.id).label('annotated_responses')
        ).outerjoin(CellAnnotation)
        
        # Applica filtro per file se selezionato
        if file_id:
            base_query = base_query.filter(TextCell.excel_file_id == file_id)
        
        # Applica filtro per domanda specifica se selezionata
        if selected_question:
            base_query = base_query.filter(TextCell.column_name == selected_question)
        
        # Applica filtro per foglio se selezionato
        if sheet_name:
            base_query = base_query.filter(TextCell.sheet_name == sheet_name)
        
        questions_stats = base_query.group_by(TextCell.column_name)\
                                   .order_by(TextCell.column_name)\
                                   .all()
    
    return render_template('annotation/browse_annotations.html',
                         cells=cells,
                         files=files,
                         sheet_names=sheet_names,
                         question_names=question_names,
                         current_file_id=file_id,
                         current_sheet=sheet_name,
                         selected_question=selected_question,
                         annotated_only=annotated_only,
                         view_mode=view_mode,
                         questions_stats=questions_stats)

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
    ).select_from(ExcelFile)\
     .outerjoin(TextCell, ExcelFile.id == TextCell.excel_file_id)\
     .outerjoin(CellAnnotation, TextCell.id == CellAnnotation.text_cell_id)\
     .group_by(ExcelFile.id)\
     .all()
    
    # Nuove statistiche dettagliate per file
    file_label_stats = get_file_label_statistics()
    overview_charts = create_overview_charts(file_label_stats)
    
    return render_template('annotation/statistics.html',
                         total_cells=total_cells,
                         annotated_cells=annotated_cells,
                         user_stats=user_stats,
                         label_stats=label_stats,
                         file_progress=file_progress,
                         file_label_stats=file_label_stats,
                         overview_charts=overview_charts)

@annotation_bp.route('/file_statistics/<int:file_id>')
@login_required
def file_statistics(file_id):
    """Statistiche dettagliate per un file specifico"""
    file_obj = ExcelFile.query.get_or_404(file_id)
    
    # Ottieni statistiche solo per questo file
    file_stats = get_file_label_statistics()
    current_file_stats = None
    
    for stat in file_stats:
        if stat['file'].id == file_id:
            current_file_stats = stat
            break
    
    if not current_file_stats:
        flash('Nessuna statistica trovata per questo file.', 'warning')
        return redirect(url_for('annotation.statistics'))
    
    return render_template('annotation/file_statistics.html',
                         file_stats=current_file_stats)

def get_file_label_statistics():
    """Genera statistiche dettagliate delle etichette per ogni file"""
    file_stats = []
    
    # Ottieni tutti i file con le loro statistiche
    files = ExcelFile.query.all()
    
    for file in files:
        # Statistiche base del file
        total_cells = TextCell.query.filter_by(excel_file_id=file.id).count()
        annotated_cells = db.session.query(TextCell.id)\
            .filter_by(excel_file_id=file.id)\
            .join(CellAnnotation, TextCell.id == CellAnnotation.text_cell_id)\
            .distinct().count()
        
        # Statistiche per etichetta in questo file
        label_stats = db.session.query(
            Label.name,
            Label.color,
            Label.category,
            db.func.count(CellAnnotation.id).label('count')
        ).select_from(Label)\
         .join(CellAnnotation, Label.id == CellAnnotation.label_id)\
         .join(TextCell, CellAnnotation.text_cell_id == TextCell.id)\
         .filter(TextCell.excel_file_id == file.id)\
         .group_by(Label.id)\
         .order_by(db.desc('count'))\
         .all()
        
        # Statistiche per categoria in questo file
        category_stats = db.session.query(
            Label.category,
            db.func.count(CellAnnotation.id).label('count')
        ).select_from(Label)\
         .join(CellAnnotation, Label.id == CellAnnotation.label_id)\
         .join(TextCell, CellAnnotation.text_cell_id == TextCell.id)\
         .filter(TextCell.excel_file_id == file.id)\
         .group_by(Label.category)\
         .order_by(db.desc('count'))\
         .all()
        
        # Contributori al file
        contributors = db.session.query(
            User.username,
            db.func.count(CellAnnotation.id).label('count')
        ).select_from(User)\
         .join(CellAnnotation, User.id == CellAnnotation.user_id)\
         .join(TextCell, CellAnnotation.text_cell_id == TextCell.id)\
         .filter(TextCell.excel_file_id == file.id)\
         .group_by(User.id)\
         .order_by(db.desc('count'))\
         .all()
        
        # Crea grafici per questo file
        charts = create_file_charts(file.id, label_stats, category_stats, contributors)
        
        file_stats.append({
            'file': file,
            'total_cells': total_cells,
            'annotated_cells': annotated_cells,
            'completion_rate': round((annotated_cells / total_cells * 100) if total_cells > 0 else 0, 1),
            'label_stats': label_stats,
            'category_stats': category_stats,
            'contributors': contributors,
            'charts': charts
        })
    
    return file_stats

def create_file_charts(file_id, label_stats, category_stats, contributors):
    """Crea grafici Plotly per un file specifico"""
    charts = {}
    
    # Grafico a torta delle etichette
    if label_stats:
        labels = [stat.name for stat in label_stats]
        values = [stat.count for stat in label_stats]
        colors = [stat.color for stat in label_stats]
        
        fig_labels = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig_labels.update_layout(
            title=f"Distribuzione Etichette",
            showlegend=True,
            height=400,
            font=dict(size=12)
        )
        
        charts['labels_pie'] = json.dumps(fig_labels, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Grafico a barre delle categorie
    if category_stats:
        categories = [stat.category for stat in category_stats]
        counts = [stat.count for stat in category_stats]
        
        fig_categories = go.Figure(data=[go.Bar(
            x=categories,
            y=counts,
            marker_color='rgb(55, 83, 109)'
        )])
        
        fig_categories.update_layout(
            title="Annotazioni per Categoria",
            xaxis_title="Categoria",
            yaxis_title="Numero di Annotazioni",
            height=400
        )
        
        charts['categories_bar'] = json.dumps(fig_categories, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Grafico dei contributori
    if contributors:
        users = [contrib.username for contrib in contributors[:10]]  # Top 10
        counts = [contrib.count for contrib in contributors[:10]]
        
        fig_contributors = go.Figure(data=[go.Bar(
            x=counts,
            y=users,
            orientation='h',
            marker_color='rgb(26, 118, 255)'
        )])
        
        fig_contributors.update_layout(
            title="Top Contributori",
            xaxis_title="Numero di Annotazioni",
            yaxis_title="Utente",
            height=max(400, len(users) * 30)
        )
        
        charts['contributors_bar'] = json.dumps(fig_contributors, cls=plotly.utils.PlotlyJSONEncoder)
    
    return charts

def create_overview_charts(file_stats):
    """Crea grafici di panoramica generale"""
    charts = {}
    
    # Grafico del tasso di completamento per file
    file_names = [stat['file'].original_filename[:30] + "..." if len(stat['file'].original_filename) > 30 
                  else stat['file'].original_filename for stat in file_stats]
    completion_rates = [stat['completion_rate'] for stat in file_stats]
    
    fig_completion = go.Figure(data=[go.Bar(
        x=file_names,
        y=completion_rates,
        marker_color=['rgb(26, 118, 255)' if rate >= 50 else 'rgb(255, 65, 54)' for rate in completion_rates]
    )])
    
    fig_completion.update_layout(
        title="Tasso di Completamento per File",
        xaxis_title="File",
        yaxis_title="Percentuale Completamento (%)",
        height=400,
        xaxis_tickangle=-45
    )
    
    charts['completion_overview'] = json.dumps(fig_completion, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Distribuzione generale delle etichette (tutti i file)
    all_labels = defaultdict(int)
    label_colors = {}
    
    for stat in file_stats:
        for label_stat in stat['label_stats']:
            all_labels[label_stat.name] += label_stat.count
            label_colors[label_stat.name] = label_stat.color
    
    if all_labels:
        labels = list(all_labels.keys())
        values = list(all_labels.values())
        colors = [label_colors.get(label, '#cccccc') for label in labels]
        
        fig_all_labels = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.3
        )])
        
        fig_all_labels.update_layout(
            title="Distribuzione Generale delle Etichette",
            height=500
        )
        
        charts['all_labels_pie'] = json.dumps(fig_all_labels, cls=plotly.utils.PlotlyJSONEncoder)
    
    return charts
