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
