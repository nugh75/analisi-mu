"""
Routes per le statistiche di annotazione
"""

from flask import Blueprint, render_template, request, jsonify
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
        Label.color,
        func.count(CellAnnotation.id).label('usage_count')
    ).join(CellAnnotation).group_by(Label.id).order_by(desc('usage_count')).limit(10).all()
    
    # Dati per grafici
    # Annotazioni per utente (per grafico)
    user_chart_data = db.session.query(
        User.username,
        func.count(CellAnnotation.id).label('count')
    ).join(CellAnnotation, User.id == CellAnnotation.user_id).group_by(User.id).order_by(desc('count')).limit(15).all()
    
    # Distribuzione etichette (per grafico)
    label_chart_data = db.session.query(
        Label.name,
        Label.color,
        func.count(CellAnnotation.id).label('count')
    ).join(CellAnnotation).group_by(Label.id).order_by(desc('count')).limit(10).all()
    
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
        Label.color,
        Category.name.label('category_name'),
        func.count(CellAnnotation.id).label('count')
    ).select_from(CellAnnotation).join(Label).join(Category).filter(
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
    
    return {
        'user1_stats': user1_stats,
        'user2_stats': user2_stats,
        'agreement': agreement,
        'conflicts': conflicts,
        'common_labels': common_labels,
        'user1_only_labels': user1_only,
        'user2_only_labels': user2_only,
        'chart_data': chart_data,
        'timeline_data': timeline_data
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
