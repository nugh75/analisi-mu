"""
Routes per la gestione delle etichette
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from models import Label, CellAnnotation, db
from forms import LabelForm

labels_bp = Blueprint('labels', __name__)

@labels_bp.route('/')
@login_required
def list_labels():
    """Lista di tutte le etichette"""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    
    query = Label.query
    
    if category_filter:
        query = query.filter_by(category=category_filter)
    
    labels = query.order_by(Label.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Liste delle categorie per il filtro
    categories = db.session.query(Label.category)\
                          .filter(Label.category.isnot(None))\
                          .distinct()\
                          .all()
    category_names = [cat[0] for cat in categories if cat[0]]
    
    return render_template('labels/list_labels.html', 
                         labels=labels,
                         categories=category_names,
                         current_category=category_filter)

@labels_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_label():
    """Crea una nuova etichetta"""
    form = LabelForm()
    
    if form.validate_on_submit():
        # Verifica se l'etichetta esiste già
        existing_label = Label.query.filter_by(name=form.name.data).first()
        
        if existing_label:
            flash('Un\'etichetta con questo nome esiste già.', 'error')
        else:
            label = Label(
                name=form.name.data,
                description=form.description.data,
                category=form.category.data,
                color=form.color.data
            )
            
            db.session.add(label)
            db.session.commit()
            
            flash('Etichetta creata con successo!', 'success')
            return redirect(url_for('labels.list_labels'))
    
    return render_template('labels/create_label.html', form=form)

@labels_bp.route('/edit/<int:label_id>', methods=['GET', 'POST'])
@login_required
def edit_label(label_id):
    """Modifica un'etichetta esistente"""
    label = Label.query.get_or_404(label_id)
    form = LabelForm(obj=label)
    
    if form.validate_on_submit():
        # Verifica se un'altra etichetta ha già questo nome
        existing_label = Label.query.filter(
            Label.name == form.name.data,
            Label.id != label_id
        ).first()
        
        if existing_label:
            flash('Un\'altra etichetta con questo nome esiste già.', 'error')
        else:
            label.name = form.name.data
            label.description = form.description.data
            label.category = form.category.data
            label.color = form.color.data
            
            db.session.commit()
            
            flash('Etichetta aggiornata con successo!', 'success')
            return redirect(url_for('labels.list_labels'))
    
    return render_template('labels/edit_label.html', form=form, label=label)

@labels_bp.route('/delete/<int:label_id>', methods=['POST'])
@login_required
def delete_label(label_id):
    """Elimina un'etichetta"""
    label = Label.query.get_or_404(label_id)
    
    # Conta le annotazioni associate
    annotation_count = CellAnnotation.query.filter_by(label_id=label_id).count()
    
    if annotation_count > 0:
        flash(f'Non è possibile eliminare l\'etichetta: è utilizzata in {annotation_count} annotazioni.', 'error')
    else:
        db.session.delete(label)
        db.session.commit()
        flash('Etichetta eliminata con successo.', 'success')
    
    return redirect(url_for('labels.list_labels'))

@labels_bp.route('/api/search')
@login_required
def api_search_labels():
    """API per la ricerca di etichette (per autocompletamento)"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    labels = Label.query.filter(Label.name.contains(query))\
                       .order_by(Label.name)\
                       .limit(10)\
                       .all()
    
    return jsonify([{
        'id': label.id,
        'name': label.name,
        'description': label.description,
        'category': label.category,
        'color': label.color
    } for label in labels])

@labels_bp.route('/merge', methods=['GET', 'POST'])
@login_required
def merge_labels():
    """Unisce due o più etichette in una sola"""
    if request.method == 'POST':
        source_label_ids = request.form.getlist('source_labels')
        target_label_id = request.form.get('target_label')
        
        if not source_label_ids or not target_label_id:
            flash('Seleziona almeno un\'etichetta di origine e una di destinazione.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        # Converte gli ID in interi
        try:
            source_label_ids = [int(id) for id in source_label_ids]
            target_label_id = int(target_label_id)
        except ValueError:
            flash('ID etichette non validi.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        # Verifica che l'etichetta target non sia tra quelle di origine
        if target_label_id in source_label_ids:
            flash('L\'etichetta di destinazione non può essere tra quelle di origine.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        # Ottieni le etichette
        source_labels = Label.query.filter(Label.id.in_(source_label_ids)).all()
        target_label = Label.query.get_or_404(target_label_id)
        
        if len(source_labels) != len(source_label_ids):
            flash('Alcune etichette di origine non sono state trovate.', 'error')
            return redirect(url_for('labels.merge_labels'))
        
        try:
            # Conta le annotazioni che verranno spostate
            total_annotations = 0
            for source_label in source_labels:
                annotation_count = CellAnnotation.query.filter_by(label_id=source_label.id).count()
                total_annotations += annotation_count
            
            # Sposta tutte le annotazioni dalle etichette di origine a quella di destinazione
            for source_label in source_labels:
                CellAnnotation.query.filter_by(label_id=source_label.id)\
                                  .update({'label_id': target_label_id})
            
            # Elimina le etichette di origine
            source_names = [label.name for label in source_labels]
            for source_label in source_labels:
                db.session.delete(source_label)
            
            db.session.commit()
            
            flash(f'Merge completato! {total_annotations} annotazioni spostate da {", ".join(source_names)} a "{target_label.name}".', 'success')
            return redirect(url_for('labels.list_labels'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il merge: {str(e)}', 'error')
            return redirect(url_for('labels.merge_labels'))
    
    # GET: mostra il form di merge
    labels = Label.query.order_by(Label.category, Label.name).all()
    
    # Raggruppa le etichette per categoria
    labels_by_category = {}
    for label in labels:
        category = label.category or 'Senza categoria'
        if category not in labels_by_category:
            labels_by_category[category] = []
        
        # Conta le annotazioni per ogni etichetta
        annotation_count = CellAnnotation.query.filter_by(label_id=label.id).count()
        label_data = {
            'id': label.id,
            'name': label.name,
            'description': label.description,
            'color': label.color,
            'annotation_count': annotation_count
        }
        labels_by_category[category].append(label_data)
    
    return render_template('labels/merge_labels.html', labels_by_category=labels_by_category)

@labels_bp.route('/api/suggest-merge')
@login_required
def api_suggest_merge():
    """API per suggerire etichette simili che potrebbero essere unite"""
    # Trova etichette con nomi simili o nella stessa categoria
    labels = Label.query.order_by(Label.category, Label.name).all()
    
    suggestions = []
    
    # Raggruppa per categoria
    category_groups = {}
    for label in labels:
        category = label.category or 'Senza categoria'
        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(label)
    
    # Trova etichette con nomi simili nella stessa categoria
    for category, cat_labels in category_groups.items():
        if len(cat_labels) > 1:
            # Cerca nomi simili (case-insensitive, ignora spazi)
            normalized_names = {}
            for label in cat_labels:
                normalized = label.name.lower().replace(' ', '').replace('-', '').replace('_', '')
                if normalized not in normalized_names:
                    normalized_names[normalized] = []
                normalized_names[normalized].append(label)
            
            # Trova gruppi con più di un'etichetta
            for normalized, group_labels in normalized_names.items():
                if len(group_labels) > 1:
                    suggestion = {
                        'category': category,
                        'reason': 'Nomi simili',
                        'labels': [{
                            'id': label.id,
                            'name': label.name,
                            'description': label.description,
                            'color': label.color,
                            'annotation_count': CellAnnotation.query.filter_by(label_id=label.id).count()
                        } for label in group_labels]
                    }
                    suggestions.append(suggestion)
    
    return jsonify(suggestions)
