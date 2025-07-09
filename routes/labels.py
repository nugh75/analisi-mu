"""
Routes per la gestione delle etichette
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from models import Label, CellAnnotation, Category, db
from forms import LabelForm, CategoryForm

labels_bp = Blueprint('labels', __name__)

@labels_bp.route('/')
@login_required
def list_labels():
    """Lista di tutte le etichette"""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', type=int)
    
    query = Label.query
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    labels = query.order_by(Label.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Liste delle categorie reali per il filtro
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('labels/list_labels.html', 
                         labels=labels,
                         categories=categories,
                         current_category=category_filter)

@labels_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_label():
    """Crea una nuova etichetta"""
    form = LabelForm()
    next_url = request.args.get('next') or request.form.get('next')
    
    if form.validate_on_submit():
        # Verifica se l'etichetta esiste già
        existing_label = Label.query.filter_by(name=form.name.data).first()
        
        if existing_label:
            flash('Un\'etichetta con questo nome esiste già!', 'error')
            return render_template('labels/create_label.html', form=form)
        
        # Gestione della categoria
        category_id = None
        if form.new_category.data:
            # Crea una nuova categoria se specificata
            new_category = Category(
                name=form.new_category.data.strip(),
                description=form.new_category_description.data,
                color='#6c757d'
            )
            
            # Verifica se la categoria esiste già
            existing_category = Category.query.filter_by(name=form.new_category.data.strip()).first()
            if existing_category:
                category_id = existing_category.id
            else:
                db.session.add(new_category)
                db.session.flush()  # Per ottenere l'ID
                category_id = new_category.id
        elif form.category_id.data and form.category_id.data != 0:
            category_id = form.category_id.data
        
        # Crea l'etichetta
        label = Label(
            name=form.name.data.strip(),
            description=form.description.data,
            category_id=category_id,
            color=form.color.data
        )
        
        try:
            db.session.add(label)
            db.session.commit()
            flash('Etichetta creata con successo!', 'success')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('labels.list_labels'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
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
            label.category_id = form.category_id.data
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

@labels_bp.route('/categories')
@login_required
def list_categories():
    """Lista delle categorie"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('labels/list_categories.html', categories=categories)

@labels_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """Crea una nuova categoria"""
    form = CategoryForm()
    next_url = request.args.get('next') or request.form.get('next')
    
    if form.validate_on_submit():
        # Verifica se la categoria esiste già
        if existing_category := Category.query.filter_by(name=form.name.data.strip()).first():
            flash('Una categoria con questo nome esiste già!', 'error')
            return render_template('labels/create_category.html', form=form)
        
        category = Category(
            name=form.name.data.strip(),
            description=form.description.data,
            color=form.color.data,
            is_active=form.is_active.data
        )
        
        try:
            db.session.add(category)
            db.session.commit()
            flash('Categoria creata con successo!', 'success')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('labels.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
    return render_template('labels/create_category.html', form=form)

@labels_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Modifica una categoria esistente"""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        # Verifica se un'altra categoria ha già questo nome
        if existing_category := Category.query.filter(
            Category.name == form.name.data.strip(),
            Category.id != category_id
        ).first():
            flash('Un\'altra categoria con questo nome esiste già.', 'error')
        else:
            try:
                category.name = form.name.data.strip()
                category.description = form.description.data
                category.color = form.color.data
                category.is_active = form.is_active.data
                
                db.session.commit()
                flash('Categoria aggiornata con successo!', 'success')
                return redirect(url_for('labels.list_categories'))
            except Exception as e:
                db.session.rollback()
                flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('labels/edit_category.html', form=form, category=category)

@labels_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Elimina una categoria"""
    category = Category.query.get_or_404(category_id)
    
    # Verifica se ci sono etichette che usano questa categoria
    labels_count = Label.query.filter_by(category_id=category_id).count()
    
    if labels_count > 0:
        flash(f'Impossibile eliminare la categoria: è utilizzata da {labels_count} etichette.', 'error')
        return redirect(url_for('labels.list_categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Categoria eliminata con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('labels.list_categories'))

@labels_bp.route('/categories/merge', methods=['GET', 'POST'])
@login_required
def merge_categories():
    """Unisce categorie duplicate o simili"""
    if request.method == 'POST':
        source_category_ids = request.form.getlist('source_categories')
        target_category_id = request.form.get('target_category')
        
        if not source_category_ids or not target_category_id:
            flash('Seleziona le categorie da unire e quella di destinazione.', 'error')
            return redirect(url_for('labels.merge_categories'))
        
        try:
            target_category = Category.query.get_or_404(target_category_id)
            
            # Sposta tutte le etichette dalle categorie sorgente a quella target
            labels_moved = 0
            for source_id in source_category_ids:
                if source_id != target_category_id:
                    source_category = Category.query.get(source_id)
                    if source_category:
                        # Aggiorna le etichette
                        labels_to_move = Label.query.filter_by(category_id=source_id).all()
                        for label in labels_to_move:
                            label.category_id = target_category_id
                            labels_moved += 1
                        
                        # Elimina la categoria sorgente
                        db.session.delete(source_category)
            
            db.session.commit()
            flash(f'Merge completato! {labels_moved} etichette spostate nella categoria "{target_category.name}".', 'success')
            return redirect(url_for('labels.list_categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il merge: {str(e)}', 'error')
    
    # GET: mostra la pagina di merge
    categories = Category.query.order_by(Category.name).all()
    
    # Trova categorie simili (stessa parola chiave)
    similar_groups = {}
    for category in categories:
        # Normalizza il nome per trovare similarità
        normalized = category.name.lower().strip()
        words = normalized.split()
        
        for word in words:
            if len(word) > 3:  # Solo parole significative
                if word not in similar_groups:
                    similar_groups[word] = []
                similar_groups[word].append(category)
    
    # Filtra gruppi con più di una categoria
    potential_merges = {k: v for k, v in similar_groups.items() if len(v) > 1}
    
    return render_template('labels/merge_categories.html',
                         categories=categories,
                         potential_merges=potential_merges)
