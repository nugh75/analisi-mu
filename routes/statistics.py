"""
Routes per le statistiche di annotazione
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc, distinct
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json

from models import CellAnnotation, Label, User, TextCell, ExcelFile, Category, AnnotationAction, db

statistics_bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@statistics_bp.route('/')
@login_required
def overview():
    """Pagina principale delle statistiche"""
    # Statistiche generali
    total_annotations = CellAnnotation.query.count()
    total_users = User.query.count()
    total_cells = TextCell.query.count()
    total_labels = Label.query.count()
    
    # Top 10 annotatori
    top_annotators = db.session.query(
        User.username,
        User.id,
        func.count(CellAnnotation.id).label('annotation_count')
    ).join(CellAnnotation, User.id == CellAnnotation.user_id).group_by(User.id).order_by(desc('annotation_count')).limit(10).all()
    
    # Etichette più usate
    top_labels = db.session.query(
        Label.name,
        func.coalesce(Category.color, Label.color).label('color'),
        func.count(CellAnnotation.id).label('usage_count')
    ).join(CellAnnotation)\
     .outerjoin(Category, Label.category_id == Category.id)\
     .group_by(Label.id).order_by(desc('usage_count')).limit(10).all()
    
    # Statistiche per file
    file_stats = db.session.query(
        ExcelFile.id,
        ExcelFile.filename,
        func.count(distinct(TextCell.id)).label('total_cells'),
        func.count(CellAnnotation.id).label('total_annotations'),
        func.count(distinct(CellAnnotation.user_id)).label('annotator_count')
    ).outerjoin(TextCell, ExcelFile.id == TextCell.excel_file_id)\
     .outerjoin(CellAnnotation, TextCell.id == CellAnnotation.text_cell_id)\
     .group_by(ExcelFile.id)\
     .order_by(desc('total_annotations'))\
     .all()
    
    # Dati per grafici
    # Annotazioni per utente (per grafico)
    user_chart_data = db.session.query(
        User.username,
        func.count(CellAnnotation.id).label('count')
    ).join(CellAnnotation, User.id == CellAnnotation.user_id).group_by(User.id).order_by(desc('count')).limit(15).all()
    
    # Distribuzione etichette (per grafico)
    label_chart_data = db.session.query(
        Label.name,
        func.coalesce(Category.color, Label.color).label('color'),
        func.count(CellAnnotation.id).label('count')
    ).join(CellAnnotation)\
     .outerjoin(Category, Label.category_id == Category.id)\
     .group_by(Label.id).order_by(desc('count')).limit(10).all()
    
    # Timeline attività
    timeline_data = db.session.query(
        func.date(CellAnnotation.created_at).label('date'),
        func.count(CellAnnotation.id).label('count')
    ).group_by(func.date(CellAnnotation.created_at)).order_by('date').all()
    
    return render_template('statistics/overview.html',
                         total_annotations=total_annotations,
                         total_users=total_users,
                         total_cells=total_cells,
                         total_labels=total_labels,
                         top_annotators=top_annotators,
                         top_labels=top_labels,
                         file_stats=file_stats,
                         user_chart_data=user_chart_data,
                         label_chart_data=label_chart_data,
                         timeline_data=timeline_data)

@statistics_bp.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    """Statistiche dettagliate per un singolo utente"""
    user = User.query.get_or_404(user_id)
    
    # Statistiche base dell'utente
    user_annotations = CellAnnotation.query.filter_by(user_id=user_id).all()
    total_annotations = len(user_annotations)
    unique_cells = db.session.query(distinct(CellAnnotation.text_cell_id)).filter_by(user_id=user_id).count()
    unique_labels = db.session.query(distinct(CellAnnotation.label_id)).filter_by(user_id=user_id).count()
    
    # Media annotazioni per giorno
    first_annotation = db.session.query(func.min(CellAnnotation.created_at)).filter_by(user_id=user_id).scalar()
    days_active = 1
    if first_annotation:
        days_active = max(1, (datetime.now() - first_annotation).days + 1)
    avg_per_day = total_annotations / days_active
    
    # Distribuzione etichette
    label_usage = db.session.query(
        Label.name,
        func.coalesce(Category.color, Label.color).label('color'),
        Category.name.label('category_name'),
        func.count(CellAnnotation.id).label('count')
    ).select_from(CellAnnotation).join(Label).outerjoin(Category, Label.category_id == Category.id).filter(
        CellAnnotation.user_id == user_id
    ).group_by(Label.id).order_by(desc('count')).all()
    
    # Aggiungi percentuali
    label_usage_with_pct = []
    for usage in label_usage:
        percentage = (usage.count / total_annotations * 100) if total_annotations > 0 else 0
        label_usage_with_pct.append({
            'name': usage.name,
            'color': usage.color,
            'category_name': usage.category_name,
            'count': usage.count,
            'percentage': percentage
        })
    
    # Attività recente (ultime 20 azioni)
    recent_actions = db.session.query(AnnotationAction).filter_by(
        performed_by=user_id
    ).order_by(desc(AnnotationAction.timestamp)).limit(20).all()
    
    # Aggiungi info etichetta alle azioni
    recent_actions_with_labels = []
    for action in recent_actions:
        label = Label.query.get(action.label_id) if action.label_id else None
        recent_actions_with_labels.append({
            'timestamp': action.timestamp,
            'action': action.action_type,
            'cell_id': action.text_cell_id,
            'label_name': label.name if label else 'N/A',
            'label_color': label.color if label else '#000000'
        })
    
    # Timeline attività
    timeline_data = db.session.query(
        func.date(CellAnnotation.created_at).label('date'),
        func.count(CellAnnotation.id).label('count')
    ).filter(CellAnnotation.user_id == user_id).group_by(
        func.date(CellAnnotation.created_at)
    ).order_by('date').all()
    
    timeline_dates = []
    for item in timeline_data:
        if isinstance(item.date, str):
            # Se date è una stringa, verifica il formato e converti se necessario
            try:
                if '-' in item.date:  # Formato YYYY-MM-DD
                    date_obj = datetime.strptime(item.date, '%Y-%m-%d').date()
                    timeline_dates.append(date_obj.strftime('%Y-%m-%d'))
                else:  # Altri formati di data come stringa
                    timeline_dates.append(item.date)  # Usa la stringa originale
            except ValueError:
                timeline_dates.append(item.date)  # Fallback alla stringa originale
        else:
            # Altrimenti usa direttamente strftime
            timeline_dates.append(item.date.strftime('%Y-%m-%d'))
    timeline_counts = [item.count for item in timeline_data]
    
    # Statistiche per categoria
    category_stats = db.session.query(
        Category.name,
        func.count(CellAnnotation.id).label('total_annotations'),
        func.count(distinct(CellAnnotation.label_id)).label('unique_labels')
    ).select_from(CellAnnotation).join(Label).join(Category).filter(
        CellAnnotation.user_id == user_id
    ).group_by(Category.id).all()
    
    category_stats_with_pct = []
    for cat_stat in category_stats:
        percentage = (cat_stat.total_annotations / total_annotations * 100) if total_annotations > 0 else 0
        
        # Etichetta più usata nella categoria
        most_used = db.session.query(
            Label.name,
            Label.color,
            func.count(CellAnnotation.id).label('count')
        ).select_from(CellAnnotation).join(Label).join(Category).filter(
            CellAnnotation.user_id == user_id,
            Category.name == cat_stat.name
        ).group_by(Label.id).order_by(desc('count')).first()
        
        category_stats_with_pct.append({
            'name': cat_stat.name,
            'total_annotations': cat_stat.total_annotations,
            'unique_labels': cat_stat.unique_labels,
            'percentage': percentage,
            'most_used_label': {
                'name': most_used.name,
                'color': most_used.color,
                'count': most_used.count
            } if most_used else None
        })
    
    # Dati per grafici
    label_names = [item['name'] for item in label_usage_with_pct]
    label_counts = [item['count'] for item in label_usage_with_pct]
    label_colors = [item['color'] for item in label_usage_with_pct]
    
    stats = {
        'total_annotations': total_annotations,
        'unique_cells': unique_cells,
        'unique_labels': unique_labels,
        'avg_per_day': avg_per_day,
        'label_usage': label_usage_with_pct,
        'recent_actions': recent_actions_with_labels,
        'timeline_dates': timeline_dates,
        'timeline_counts': timeline_counts,
        'category_stats': category_stats_with_pct,
        'label_names': label_names,
        'label_counts': label_counts,
        'label_colors': label_colors
    }
    
    return render_template('statistics/user_detail.html', user=user, stats=stats)

@statistics_bp.route('/compare')
@login_required
def compare():
    """Confronto tra annotatori"""
    # Tutti gli utenti con annotazioni
    users = db.session.query(
        User.id,
        User.username,
        func.count(CellAnnotation.id).label('annotation_count')
    ).join(CellAnnotation, User.id == CellAnnotation.user_id).group_by(User.id).order_by(User.username).all()
    
    user1_id = request.args.get('user1_id', type=int)
    user2_id = request.args.get('user2_id', type=int)
    
    user1 = User.query.get(user1_id) if user1_id else None
    user2 = User.query.get(user2_id) if user2_id else None
    
    comparison = None
    if user1 and user2 and user1_id != user2_id:
        comparison = _calculate_comparison(user1, user2)
    
    return render_template('statistics/compare.html',
                         users=users,
                         user1=user1,
                         user2=user2,
                         comparison=comparison)

def _calculate_comparison(user1, user2):
    """Calcola dati di confronto tra due utenti"""
    # Statistiche base per entrambi gli utenti
    user1_stats = _get_user_basic_stats(user1.id)
    user2_stats = _get_user_basic_stats(user2.id)
    
    # Celle annotate da entrambi
    common_cells_query = db.session.query(CellAnnotation.text_cell_id).filter_by(user_id=user1.id).intersect(
        db.session.query(CellAnnotation.text_cell_id).filter_by(user_id=user2.id)
    )
    common_cells = [row[0] for row in common_cells_query.all()]
    
    # Calcola accordo inter-annotatore
    agreement = _calculate_inter_annotator_agreement(user1.id, user2.id, common_cells)
    
    # Conflitti (celle con etichette diverse)
    conflicts = _find_annotation_conflicts(user1.id, user2.id, common_cells)
    
    # Etichette comuni e specifiche
    common_labels, user1_only, user2_only = _compare_label_usage(user1.id, user2.id)
    
    # Dati per grafici
    chart_data = _prepare_chart_data(user1.id, user2.id)
    timeline_data = _prepare_timeline_data(user1.id, user2.id)
    
    # Confronto per quesito - TODO: implementare
    # question_comparison = _compare_by_question(user1.id, user2.id)
    question_comparison = []
    
    return {
        'user1_stats': user1_stats,
        'user2_stats': user2_stats,
        'agreement': agreement,
        'conflicts': conflicts,
        'common_labels': common_labels,
        'user1_only_labels': user1_only,
        'user2_only_labels': user2_only,
        'chart_data': chart_data,
        'timeline_data': timeline_data,
        'question_comparison': question_comparison
    }

def _get_user_basic_stats(user_id):
    """Ottieni statistiche base per un utente"""
    total_annotations = CellAnnotation.query.filter_by(user_id=user_id).count()
    unique_cells = db.session.query(distinct(CellAnnotation.text_cell_id)).filter_by(user_id=user_id).count()
    unique_labels = db.session.query(distinct(CellAnnotation.label_id)).filter_by(user_id=user_id).count()
    
    # Media annotazioni per giorno
    first_annotation = db.session.query(func.min(CellAnnotation.created_at)).filter_by(user_id=user_id).scalar()
    days_active = 1
    if first_annotation:
        days_active = max(1, (datetime.now() - first_annotation).days + 1)
    avg_per_day = total_annotations / days_active
    
    return {
        'total_annotations': total_annotations,
        'unique_cells': unique_cells,
        'unique_labels': unique_labels,
        'avg_per_day': avg_per_day
    }

def _calculate_inter_annotator_agreement(user1_id, user2_id, common_cells):
    """Calcola l'accordo inter-annotatore (Cohen's Kappa)"""
    if not common_cells:
        return {
            'common_cells': 0,
            'exact_matches': 0,
            'agreement_percentage': 0.0,
            'kappa': 0.0
        }
    
    exact_matches = 0
    total_comparisons = 0
    
    for cell_id in common_cells:
        # Etichette dell'utente 1 per questa cella
        user1_labels = set([
            ann.label_id for ann in CellAnnotation.query.filter_by(
                user_id=user1_id, text_cell_id=cell_id
            ).all()
        ])
        
        # Etichette dell'utente 2 per questa cella
        user2_labels = set([
            ann.label_id for ann in CellAnnotation.query.filter_by(
                user_id=user2_id, text_cell_id=cell_id
            ).all()
        ])
        
        # Confronta i set di etichette
        if user1_labels == user2_labels:
            exact_matches += 1
        total_comparisons += 1
    
    agreement_percentage = (exact_matches / total_comparisons * 100) if total_comparisons > 0 else 0
    
    # Calcolo semplificato di Cohen's Kappa (versione base)
    # Per un calcolo più preciso servirebbero più considerazioni statistiche
    pe = 0.5  # Probabilità di accordo casuale (semplificata)
    po = agreement_percentage / 100  # Probabilità di accordo osservato
    kappa = (po - pe) / (1 - pe) if (1 - pe) != 0 else 0
    
    return {
        'common_cells': len(common_cells),
        'exact_matches': exact_matches,
        'agreement_percentage': agreement_percentage,
        'kappa': max(0, kappa)  # Non può essere negativo in questa semplificazione
    }

def _find_annotation_conflicts(user1_id, user2_id, common_cells):
    """Trova conflitti di annotazione tra due utenti"""
    conflicts = []
    
    for cell_id in common_cells:
        # Etichette dell'utente 1
        user1_annotations = db.session.query(CellAnnotation, Label, Category).join(
            Label
        ).join(Category).filter(
            CellAnnotation.user_id == user1_id,
            CellAnnotation.text_cell_id == cell_id
        ).all()
        
        # Etichette dell'utente 2
        user2_annotations = db.session.query(CellAnnotation, Label, Category).join(
            Label
        ).join(Category).filter(
            CellAnnotation.user_id == user2_id,
            CellAnnotation.text_cell_id == cell_id
        ).all()
        
        user1_label_ids = set([ann[0].label_id for ann in user1_annotations])
        user2_label_ids = set([ann[0].label_id for ann in user2_annotations])
        
        # Se ci sono differenze, è un conflitto
        if user1_label_ids != user2_label_ids:
            conflicts.append({
                'cell_id': cell_id,
                'user1_labels': [{'name': ann[1].name, 'color': ann[1].color} for ann in user1_annotations],
                'user2_labels': [{'name': ann[1].name, 'color': ann[1].color} for ann in user2_annotations],
                'category': user1_annotations[0][2].name if user1_annotations else 'N/A'
            })
    
    return conflicts

def _compare_label_usage(user1_id, user2_id):
    """Confronta l'uso delle etichette tra due utenti"""
    # Etichette usate dall'utente 1
    user1_labels = db.session.query(
        Label.id, Label.name, Label.color,
        func.count(CellAnnotation.id).label('count')
    ).join(CellAnnotation).filter(
        CellAnnotation.user_id == user1_id
    ).group_by(Label.id).all()
    
    # Etichette usate dall'utente 2
    user2_labels = db.session.query(
        Label.id, Label.name, Label.color,
        func.count(CellAnnotation.id).label('count')
    ).join(CellAnnotation).filter(
        CellAnnotation.user_id == user2_id
    ).group_by(Label.id).all()
    
    user1_label_ids = set([l.id for l in user1_labels])
    user2_label_ids = set([l.id for l in user2_labels])
    
    # Crea dizionari per accesso rapido
    user1_dict = {l.id: l for l in user1_labels}
    user2_dict = {l.id: l for l in user2_labels}
    
    # Etichette in comune
    common_label_ids = user1_label_ids.intersection(user2_label_ids)
    common_labels = []
    for label_id in common_label_ids:
        label1 = user1_dict[label_id]
        label2 = user2_dict[label_id]
        common_labels.append({
            'id': label_id,
            'name': label1.name,
            'color': label1.color,
            'user1_count': label1.count,
            'user2_count': label2.count
        })
    
    # Etichette specifiche dell'utente 1
    user1_only_ids = user1_label_ids - user2_label_ids
    user1_only = [
        {'name': user1_dict[lid].name, 'color': user1_dict[lid].color, 'count': user1_dict[lid].count}
        for lid in user1_only_ids
    ]
    
    # Etichette specifiche dell'utente 2
    user2_only_ids = user2_label_ids - user1_label_ids
    user2_only = [
        {'name': user2_dict[lid].name, 'color': user2_dict[lid].color, 'count': user2_dict[lid].count}
        for lid in user2_only_ids
    ]
    
    return common_labels, user1_only, user2_only

def _prepare_chart_data(user1_id, user2_id):
    """Prepara dati per i grafici di confronto"""
    # Ottieni tutte le etichette usate da entrambi
    all_labels = db.session.query(Label.id, Label.name).join(CellAnnotation).filter(
        (CellAnnotation.user_id == user1_id) | (CellAnnotation.user_id == user2_id)
    ).distinct().all()
    
    label_names = [l.name for l in all_labels]
    user1_counts = []
    user2_counts = []
    
    for label in all_labels:
        # Count per utente 1
        count1 = CellAnnotation.query.filter_by(user_id=user1_id, label_id=label.id).count()
        user1_counts.append(count1)
        
        # Count per utente 2
        count2 = CellAnnotation.query.filter_by(user_id=user2_id, label_id=label.id).count()
        user2_counts.append(count2)
    
    return {
        'label_names': label_names,
        'user1_counts': user1_counts,
        'user2_counts': user2_counts
    }

def _prepare_timeline_data(user1_id, user2_id):
    """Prepara dati timeline per confronto"""
    # Date di tutte le annotazioni
    all_dates = db.session.query(
        func.date(CellAnnotation.created_at).label('date')
    ).filter(
        (CellAnnotation.user_id == user1_id) | (CellAnnotation.user_id == user2_id)
    ).distinct().order_by('date').all()
    
    dates = []
    for d in all_dates:
        if isinstance(d.date, str):
            # Se date è una stringa, usa direttamente
            dates.append(d.date)
        else:
            # Altrimenti usa strftime
            dates.append(d.date.strftime('%Y-%m-%d'))
    
    user1_counts = []
    user2_counts = []
    
    for date_obj in all_dates:
        # Estrai la data in formato corretto per il confronto
        if isinstance(date_obj.date, str):
            date_value = date_obj.date
        else:
            date_value = date_obj.date
        
        # Count per utente 1
        count1 = CellAnnotation.query.filter(
            CellAnnotation.user_id == user1_id,
            func.date(CellAnnotation.created_at) == date_value
        ).count()
        user1_counts.append(count1)
        
        # Count per utente 2
        count2 = CellAnnotation.query.filter(
            CellAnnotation.user_id == user2_id,
            func.date(CellAnnotation.created_at) == date_value
        ).count()
        user2_counts.append(count2)
    
    return {
        'dates': dates,
        'user1_counts': user1_counts,
        'user2_counts': user2_counts
    }

@statistics_bp.route('/api/chart_data/<chart_type>')
@login_required
def chart_data(chart_type):
    """API per dati dei grafici"""
    
    if chart_type == 'annotations_per_user':
        data = db.session.query(
            User.username,
            func.count(CellAnnotation.id).label('count')
        ).join(CellAnnotation, User.id == CellAnnotation.user_id).group_by(User.id).order_by(desc('count')).limit(20).all()
        
        return jsonify({
            'labels': [item.username for item in data],
            'values': [item.count for item in data]
        })
    
    elif chart_type == 'labels_usage':
        data = db.session.query(
            Label.name,
            func.count(CellAnnotation.id).label('count')
        ).join(CellAnnotation).group_by(Label.id).order_by(desc('count')).limit(15).all()
        
        return jsonify({
            'labels': [item.name for item in data],
            'values': [item.count for item in data]
        })
    
    elif chart_type == 'annotations_timeline':
        data = db.session.query(
            func.date(CellAnnotation.created_at).label('date'),
            func.count(CellAnnotation.id).label('count')
        ).group_by(func.date(CellAnnotation.created_at)).order_by('date').all()
        
        return jsonify({
            'dates': [item.date.isoformat() for item in data],
            'values': [item.count for item in data]
        })
    
    return jsonify({'error': 'Chart type not found'}), 404

@statistics_bp.route('/api/question_chart_data/<int:file_id>/<question>/<chart_type>')
@login_required
def question_chart_data(file_id, question, chart_type):
    """API per dati dei grafici specifici del quesito"""
    
    # Verifica che il file esista
    file_obj = ExcelFile.query.get_or_404(file_id)
    
    # Ottieni filtri dalla query string
    category_filter = request.args.get('category')
    label_name_filter = request.args.get('label_name', '').strip()
    min_usage = request.args.get('min_usage', type=int)
    max_usage = request.args.get('max_usage', type=int)
    
    if chart_type == 'labels_histogram':
        # Istogramma delle etichette per il quesito con filtri
        query = db.session.query(
            Label.name,
            func.coalesce(Category.color, Label.color).label('color'),
            Category.name.label('category_name'),
            func.count(CellAnnotation.id).label('usage_count')
        ).join(CellAnnotation)\
         .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
         .outerjoin(Category, Label.category_id == Category.id)\
         .filter(TextCell.excel_file_id == file_id)\
         .filter(TextCell.column_name == question)\
         .group_by(Label.id)
        
        # Applica filtri se specificati
        if category_filter:
            query = query.filter(Category.name == category_filter)
        
        if label_name_filter:
            query = query.filter(Label.name.ilike(f'%{label_name_filter}%'))
        
        if min_usage is not None:
            query = query.having(func.count(CellAnnotation.id) >= min_usage)
        
        if max_usage is not None:
            query = query.having(func.count(CellAnnotation.id) <= max_usage)
        
        data = query.order_by(desc('usage_count')).all()
        
        return jsonify({
            'labels': [item.name for item in data],
            'values': [item.usage_count for item in data],
            'colors': [item.color or '#007bff' for item in data],
            'categories': [item.category_name or 'Senza categoria' for item in data]
        })
    
    elif chart_type == 'annotators_histogram':
        # Istogramma degli annotatori per il quesito con filtri
        base_query = db.session.query(CellAnnotation.user_id)\
            .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
            .join(Label, Label.id == CellAnnotation.label_id)\
            .outerjoin(Category, Label.category_id == Category.id)\
            .filter(TextCell.excel_file_id == file_id)\
            .filter(TextCell.column_name == question)
        
        # Applica filtri se specificati
        if category_filter:
            base_query = base_query.filter(Category.name == category_filter)
        
        if label_name_filter:
            base_query = base_query.filter(Label.name.ilike(f'%{label_name_filter}%'))
        
        # Query per annotazioni totali
        annotations_query = base_query.add_columns(func.count(CellAnnotation.id).label('annotation_count'))\
            .group_by(CellAnnotation.user_id)
        
        # Query per celle uniche
        cells_query = base_query.add_columns(func.count(distinct(CellAnnotation.text_cell_id)).label('cell_count'))\
            .group_by(CellAnnotation.user_id)
        
        # Unisci i risultati con le informazioni utente
        user_annotations = {}
        user_cells = {}
        
        for user_id, count in annotations_query.all():
            user_annotations[user_id] = count
            
        for user_id, count in cells_query.all():
            user_cells[user_id] = count
        
        # Ottieni nomi utenti
        users = db.session.query(User.id, User.username)\
            .filter(User.id.in_(list(user_annotations.keys())))\
            .order_by(User.username)\
            .all()
        
        labels = []
        annotations = []
        cells = []
        
        for user_id, username in users:
            labels.append(username)
            annotations.append(user_annotations.get(user_id, 0))
            cells.append(user_cells.get(user_id, 0))
        
        return jsonify({
            'labels': labels,
            'annotations': annotations,
            'cells': cells
        })
    
    elif chart_type == 'categories_distribution':
        # Distribuzione per categoria con filtri
        query = db.session.query(
            Category.name.label('category_name'),
            func.count(CellAnnotation.id).label('total_annotations'),
            func.count(distinct(CellAnnotation.label_id)).label('unique_labels')
        ).join(Label, Label.category_id == Category.id)\
         .join(CellAnnotation)\
         .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
         .filter(TextCell.excel_file_id == file_id)\
         .filter(TextCell.column_name == question)
        
        # Applica filtri se specificati
        if category_filter:
            query = query.filter(Category.name == category_filter)
        
        if label_name_filter:
            query = query.filter(Label.name.ilike(f'%{label_name_filter}%'))
        
        data = query.group_by(Category.id)\
                   .order_by(desc('total_annotations'))\
                   .all()
        
        # Aggiungi etichette senza categoria se non filtrato per categoria specifica
        if not category_filter:
            no_category_query = db.session.query(
                func.count(CellAnnotation.id).label('total_annotations'),
                func.count(distinct(CellAnnotation.label_id)).label('unique_labels')
            ).join(Label)\
             .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
             .filter(TextCell.excel_file_id == file_id)\
             .filter(TextCell.column_name == question)\
             .filter(Label.category_id.is_(None))
            
            if label_name_filter:
                no_category_query = no_category_query.filter(Label.name.ilike(f'%{label_name_filter}%'))
            
            no_category_data = no_category_query.first()
            
            categories = [item.category_name for item in data]
            annotations = [item.total_annotations for item in data]
            labels_count = [item.unique_labels for item in data]
            
            if no_category_data and no_category_data.total_annotations > 0:
                categories.append('Senza categoria')
                annotations.append(no_category_data.total_annotations)
                labels_count.append(no_category_data.unique_labels)
        else:
            categories = [item.category_name for item in data]
            annotations = [item.total_annotations for item in data]
            labels_count = [item.unique_labels for item in data]
        
        return jsonify({
            'categories': categories,
            'annotations': annotations,
            'labels_count': labels_count
        })
    
    elif chart_type == 'coverage_analysis':
        # Analisi copertura annotazioni con filtri
        total_cells = TextCell.query.filter_by(
            excel_file_id=file_id, 
            column_name=question
        ).count()
        
        # Query base per celle annotate con filtri
        annotated_cells_query = db.session.query(TextCell.id)\
            .filter(TextCell.excel_file_id == file_id)\
            .filter(TextCell.column_name == question)\
            .join(CellAnnotation)\
            .join(Label, Label.id == CellAnnotation.label_id)\
            .outerjoin(Category, Label.category_id == Category.id)
        
        # Applica filtri se specificati
        if category_filter:
            annotated_cells_query = annotated_cells_query.filter(Category.name == category_filter)
        
        if label_name_filter:
            annotated_cells_query = annotated_cells_query.filter(Label.name.ilike(f'%{label_name_filter}%'))
        
        annotated_cells = annotated_cells_query.distinct().count()
        
        # Distribuzione per numero di annotazioni per cella (con filtri)
        coverage_query = db.session.query(
            func.count(CellAnnotation.text_cell_id).label('annotations_per_cell'),
            func.count(distinct(CellAnnotation.text_cell_id)).label('cell_count')
        ).select_from(CellAnnotation)\
         .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
         .join(Label, Label.id == CellAnnotation.label_id)\
         .outerjoin(Category, Label.category_id == Category.id)\
         .filter(TextCell.excel_file_id == file_id)\
         .filter(TextCell.column_name == question)
        
        # Applica filtri se specificati
        if category_filter:
            coverage_query = coverage_query.filter(Category.name == category_filter)
        
        if label_name_filter:
            coverage_query = coverage_query.filter(Label.name.ilike(f'%{label_name_filter}%'))
        
        coverage_data = coverage_query.group_by(CellAnnotation.text_cell_id)\
                                     .subquery()
        
        distribution = db.session.query(
            coverage_data.c.annotations_per_cell.label('annotations_count'),
            func.count().label('cells_with_this_count')
        ).group_by(coverage_data.c.annotations_per_cell)\
         .order_by(coverage_data.c.annotations_per_cell)\
         .all()
        
        return jsonify({
            'total_cells': total_cells,
            'annotated_cells': annotated_cells,
            'unannotated_cells': total_cells - annotated_cells,
            'coverage_percentage': (annotated_cells / total_cells * 100) if total_cells > 0 else 0,
            'distribution_labels': [f'{item.annotations_count} annotazioni' for item in distribution],
            'distribution_values': [item.cells_with_this_count for item in distribution],
            'filtered': bool(category_filter or label_name_filter)
        })
    
    return jsonify({'error': 'Chart type not found'}), 404

@statistics_bp.route('/api/user_stats')
@login_required
def api_user_stats():
    """API per statistiche dell'utente corrente"""
    user_id = current_user.id
    
    total_annotations = CellAnnotation.query.filter_by(user_id=user_id).count()
    unique_cells = db.session.query(distinct(CellAnnotation.text_cell_id)).filter_by(user_id=user_id).count()
    unique_labels = db.session.query(distinct(CellAnnotation.label_id)).filter_by(user_id=user_id).count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_annotations': total_annotations,
            'unique_cells': unique_cells,
            'unique_labels': unique_labels
        }
    })

@statistics_bp.route('/api/global_stats')
@login_required
def api_global_stats():
    """API per statistiche globali del sistema"""
    total_annotations = CellAnnotation.query.count()
    total_users = User.query.count()
    total_cells = TextCell.query.count()
    total_labels = Label.query.count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_annotations': total_annotations,
            'total_users': total_users,
            'total_cells': total_cells,
            'total_labels': total_labels
        }
    })

@statistics_bp.route('/file/<int:file_id>')
@login_required
def file_detail(file_id):
    """Statistiche dettagliate per un file specifico"""
    file_obj = ExcelFile.query.get_or_404(file_id)
    
    # Statistiche generali del file
    total_cells = TextCell.query.filter_by(excel_file_id=file_id).count()
    annotated_cells = db.session.query(TextCell.id)\
        .filter(TextCell.excel_file_id == file_id)\
        .join(CellAnnotation)\
        .distinct().count()
    
    # Annotazioni per utente in questo file
    user_stats = db.session.query(
        User.username,
        User.id,
        func.count(CellAnnotation.id).label('annotation_count')
    ).join(CellAnnotation, User.id == CellAnnotation.user_id)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .filter(TextCell.excel_file_id == file_id)\
     .group_by(User.id)\
     .order_by(desc('annotation_count'))\
     .all()
    
    # Etichette più utilizzate in questo file
    label_stats = db.session.query(
        Label.name,
        func.coalesce(Category.color, Label.color).label('color'),  # Usa il colore della categoria se esiste, altrimenti quello dell'etichetta
        Category.name.label('category_name'),
        func.count(CellAnnotation.id).label('usage_count')
    ).join(CellAnnotation)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .outerjoin(Category, Label.category_id == Category.id)\
     .filter(TextCell.excel_file_id == file_id)\
     .group_by(Label.id)\
     .order_by(desc('usage_count'))\
     .all()
    
    # Statistiche per quesito
    question_stats = db.session.query(
        TextCell.column_name,
        func.count(distinct(TextCell.id)).label('total_cells'),
        func.count(CellAnnotation.id).label('total_annotations'),
        func.count(distinct(CellAnnotation.user_id)).label('annotator_count')
    ).outerjoin(CellAnnotation, TextCell.id == CellAnnotation.text_cell_id)\
     .filter(TextCell.excel_file_id == file_id)\
     .group_by(TextCell.column_name)\
     .order_by(TextCell.column_name)\
     .all()
    
    return render_template('statistics/file_detail.html',
                         file=file_obj,
                         total_cells=total_cells,
                         annotated_cells=annotated_cells,
                         user_stats=user_stats,
                         label_stats=label_stats,
                         question_stats=question_stats)

@statistics_bp.route('/question/<int:file_id>/<question>')
@login_required
def question_detail(file_id, question):
    """Statistiche dettagliate per un quesito specifico"""
    file_obj = ExcelFile.query.get_or_404(file_id)
    
    # Verifica che il quesito esista
    question_exists = TextCell.query.filter_by(
        excel_file_id=file_id, 
        column_name=question
    ).first()
    
    if not question_exists:
        flash('Quesito non trovato.', 'error')
        return redirect(url_for('statistics.file_detail', file_id=file_id))
    
    # Parametri per il filtraggio delle etichette
    category_filter = request.args.get('category')
    label_name_filter = request.args.get('label_name', '').strip()
    min_usage = request.args.get('min_usage', type=int)
    max_usage = request.args.get('max_usage', type=int)
    sort_by = request.args.get('sort_by', default='name')
    sort_order = request.args.get('sort_order', default='asc')
    
    # Celle del quesito
    cells = TextCell.query.filter_by(
        excel_file_id=file_id, 
        column_name=question
    ).all()
    
    # Statistiche annotatori per questo quesito
    annotator_stats = db.session.query(
        User.username,
        User.id,
        func.count(CellAnnotation.id).label('annotation_count'),
        func.count(distinct(CellAnnotation.text_cell_id)).label('cell_count')
    ).join(CellAnnotation, User.id == CellAnnotation.user_id)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .group_by(User.id)\
     .order_by(desc('annotation_count'))\
     .all()
    
    # Tutte le etichette utilizzate per questo quesito (con filtri)
    label_stats_query = db.session.query(
        Label.id,
        Label.name,
        Label.color,
        Category.name.label('category_name'),
        func.count(CellAnnotation.id).label('usage_count')
    ).join(CellAnnotation)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .outerjoin(Category, Label.category_id == Category.id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .group_by(Label.id)
    
    # Applica filtri se specificati
    if category_filter:
        label_stats_query = label_stats_query.filter(Category.name == category_filter)
    
    if label_name_filter:
        label_stats_query = label_stats_query.filter(Label.name.ilike(f'%{label_name_filter}%'))
    
    if min_usage is not None:
        label_stats_query = label_stats_query.having(func.count(CellAnnotation.id) >= min_usage)
    
    if max_usage is not None:
        label_stats_query = label_stats_query.having(func.count(CellAnnotation.id) <= max_usage)
    
    # Applica ordinamento
    if sort_by == 'category':
        if sort_order == 'desc':
            label_stats_query = label_stats_query.order_by(desc(Category.name))
        else:
            label_stats_query = label_stats_query.order_by(Category.name)
    elif sort_by == 'usage':
        if sort_order == 'desc':
            label_stats_query = label_stats_query.order_by(desc('usage_count'))
        else:
            label_stats_query = label_stats_query.order_by('usage_count')
    else:  # sort_by == 'name' (default)
        if sort_order == 'desc':
            label_stats_query = label_stats_query.order_by(desc(Label.name))
        else:
            label_stats_query = label_stats_query.order_by(Label.name)
    
    label_stats = label_stats_query.all()
    
    # Ottieni tutte le categorie disponibili per il dropdown dei filtri
    available_categories = db.session.query(Category.name)\
        .join(Label, Label.category_id == Category.id)\
        .join(CellAnnotation, CellAnnotation.label_id == Label.id)\
        .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
        .filter(TextCell.excel_file_id == file_id)\
        .filter(TextCell.column_name == question)\
        .distinct()\
        .order_by(Category.name)\
        .all()
    
    # Statistiche per i filtri (min/max utilizzi)
    # Prima otteniamo tutti i conteggi degli utilizzi
    usage_counts_subquery = db.session.query(
        func.count(CellAnnotation.id).label('usage_count')
    ).select_from(Label)\
     .join(CellAnnotation)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .group_by(Label.id)\
     .subquery()
    
    # Poi calcoliamo min e max da questi conteggi
    usage_stats = db.session.query(
        func.min(usage_counts_subquery.c.usage_count).label('min_usage'),
        func.max(usage_counts_subquery.c.usage_count).label('max_usage')
    ).first()
    
    # Valori di default per min/max se non ci sono dati
    min_usage_available = usage_stats.min_usage if usage_stats and usage_stats.min_usage else 1
    max_usage_available = usage_stats.max_usage if usage_stats and usage_stats.max_usage else 1
    
    # Raggruppamento etichetta + commento con ID
    cell_annotations = db.session.query(
        TextCell.id.label('cell_id'),
        TextCell.text_content.label('content'),
        CellAnnotation.id.label('annotation_id'),
        CellAnnotation.status,
        CellAnnotation.is_ai_generated,
        CellAnnotation.ai_confidence,
        Label.name.label('label_name'),
        Label.color.label('label_color'),
        Category.name.label('category_name'),
        User.username.label('annotator')
    ).join(CellAnnotation, TextCell.id == CellAnnotation.text_cell_id)\
     .join(Label, Label.id == CellAnnotation.label_id)\
     .join(User, User.id == CellAnnotation.user_id)\
     .outerjoin(Category, Label.category_id == Category.id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .order_by(TextCell.id, Label.name)\
     .all()
    
    # Raggruppa per cella
    cells_with_annotations = defaultdict(list)
    for ann in cell_annotations:
        cells_with_annotations[ann.cell_id].append(ann)
    
    # Report delle etichette con i commenti completi
    label_comments_report = db.session.query(
        Label.id,
        Label.name,
        Label.color,
        Category.name.label('category_name'),
        TextCell.id.label('cell_id'),
        TextCell.row_index.label('row_number'),
        TextCell.text_content.label('content'),
        CellAnnotation.id.label('annotation_id'),
        User.username.label('annotator'),
        CellAnnotation.is_ai_generated,
        CellAnnotation.ai_confidence,
        CellAnnotation.status
    ).join(CellAnnotation, Label.id == CellAnnotation.label_id)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .join(User, User.id == CellAnnotation.user_id)\
     .outerjoin(Category, Label.category_id == Category.id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .order_by(Label.name, TextCell.row_index)\
     .all()
    
    # Raggruppa per etichetta
    labels_with_comments = defaultdict(list)
    for item in label_comments_report:
        labels_with_comments[item.name].append(item)
    
    return render_template('statistics/question_detail.html',
                         file=file_obj,
                         question=question,
                         cells=cells,
                         annotator_stats=annotator_stats,
                         label_stats=label_stats,
                         cells_with_annotations=dict(cells_with_annotations),
                         labels_with_comments=dict(labels_with_comments),
                         # Dati per i filtri
                         available_categories=[cat.name for cat in available_categories],
                         min_usage_available=min_usage_available,
                         max_usage_available=max_usage_available,
                         # Valori correnti dei filtri
                         current_filters={
                             'category': category_filter,
                             'label_name': label_name_filter,
                             'min_usage': min_usage,
                             'max_usage': max_usage,
                             'sort_by': sort_by,
                             'sort_order': sort_order
                         })

@statistics_bp.route('/question/<int:file_id>/<question>/compare')
@login_required
def question_compare(file_id, question):
    """Confronto annotatori per un quesito specifico"""
    file_obj = ExcelFile.query.get_or_404(file_id)
    
    # Ottieni tutti gli annotatori che hanno lavorato su questo quesito
    annotators = db.session.query(User)\
        .join(CellAnnotation, User.id == CellAnnotation.user_id)\
        .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
        .filter(TextCell.excel_file_id == file_id)\
        .filter(TextCell.column_name == question)\
        .distinct()\
        .all()
    
    user1_id = request.args.get('user1_id', type=int)
    user2_id = request.args.get('user2_id', type=int)
    
    comparison_data = None
    user1 = None
    user2 = None
    
    if user1_id and user2_id and user1_id != user2_id:
        user1 = User.query.get(user1_id)
        user2 = User.query.get(user2_id)
        
        if user1 and user2:
            comparison_data = calculate_question_comparison(file_id, question, user1_id, user2_id)
    
    return render_template('statistics/question_compare.html',
                         file=file_obj,
                         question=question,
                         annotators=annotators,
                         user1=user1,
                         user2=user2,
                         comparison=comparison_data)

def calculate_question_comparison(file_id, question, user1_id, user2_id):
    """Calcola il confronto tra due annotatori per un quesito specifico"""
    # Annotazioni utente 1
    user1_annotations = db.session.query(
        CellAnnotation.text_cell_id,
        CellAnnotation.label_id,
        CellAnnotation.status,
        CellAnnotation.is_ai_generated,
        Label.name.label('label_name'),
        Label.color.label('label_color')
    ).join(Label, Label.id == CellAnnotation.label_id)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .filter(CellAnnotation.user_id == user1_id)\
     .all()
    
    # Annotazioni utente 2
    user2_annotations = db.session.query(
        CellAnnotation.text_cell_id,
        CellAnnotation.label_id,
        CellAnnotation.status,
        CellAnnotation.is_ai_generated,
        Label.name.label('label_name'),
        Label.color.label('label_color')
    ).join(Label, Label.id == CellAnnotation.label_id)\
     .join(TextCell, TextCell.id == CellAnnotation.text_cell_id)\
     .filter(TextCell.excel_file_id == file_id)\
     .filter(TextCell.column_name == question)\
     .filter(CellAnnotation.user_id == user2_id)\
     .all()
    
    # Raggruppa per cella
    user1_by_cell = defaultdict(list)
    user2_by_cell = defaultdict(list)
    
    for ann in user1_annotations:
        user1_by_cell[ann.text_cell_id].append(ann)
    
    for ann in user2_annotations:
        user2_by_cell[ann.text_cell_id].append(ann)
    
    # Calcola statistiche
    user1_cells = set(user1_by_cell.keys())
    user2_cells = set(user2_by_cell.keys())
    common_cells = user1_cells & user2_cells
    
    agreements = 0
    conflicts = []
    
    for cell_id in common_cells:
        user1_labels = set(ann.label_id for ann in user1_by_cell[cell_id])
        user2_labels = set(ann.label_id for ann in user2_by_cell[cell_id])
        
        if user1_labels == user2_labels:
            agreements += 1
        else:
            conflicts.append({
                'cell_id': cell_id,
                'user1_annotations': user1_by_cell[cell_id],
                'user2_annotations': user2_by_cell[cell_id]
            })
    
    agreement_percentage = (agreements / len(common_cells) * 100) if common_cells else 0
    
    return {
        'user1_total': len(user1_cells),
        'user2_total': len(user2_cells),
        'common_cells': len(common_cells),
        'agreements': agreements,
        'conflicts': conflicts,
        'agreement_percentage': agreement_percentage,
        'user1_annotations': user1_annotations,
        'user2_annotations': user2_annotations
    }
