"""
Routes per il sistema di decisioni sull'etichettatura.
Sistema collaborativo per decidere il raggruppamento delle etichette.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, or_
from werkzeug.utils import secure_filename
import csv
import json
import os
from datetime import datetime

from models import (db, DecisionSession, LabelGroupingProposal, LabelDecisionVote, 
                   LabelDecisionComment, User, Category)

decisions_bp = Blueprint('decisions', __name__, url_prefix='/decisions')


@decisions_bp.route('/')
@login_required
def index():
    """Dashboard principale delle sessioni di decisione"""
    # Filtri
    status_filter = request.args.get('status', 'all')
    
    # Query base
    query = DecisionSession.query
    
    # Applicazione filtri
    if status_filter != 'all':
        query = query.filter(DecisionSession.status == status_filter)
    
    # Ordinamento per data di creazione (più recenti prima)
    sessions = query.order_by(DecisionSession.created_at.desc()).all()
    
    # Statistiche rapide
    stats = {
        'total_sessions': DecisionSession.query.count(),
        'active_sessions': DecisionSession.query.filter_by(status='active').count(),
        'completed_sessions': DecisionSession.query.filter_by(status='completed').count(),
        'my_sessions': DecisionSession.query.filter_by(created_by=current_user.id).count()
    }
    
    return render_template('decisions/index.html', 
                         sessions=sessions, 
                         stats=stats, 
                         current_filter=status_filter)


@decisions_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_session():
    """Crea una nuova sessione di decisione"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        voting_threshold = float(request.form.get('voting_threshold', 0.6))
        allow_public_comments = 'allow_public_comments' in request.form
        
        # Validazione
        if not name:
            flash('Il nome della sessione è obbligatorio', 'error')
            return render_template('decisions/create_session.html')
        
        # Controlla se esiste già una sessione con lo stesso nome
        existing = DecisionSession.query.filter_by(name=name).first()
        if existing:
            flash('Esiste già una sessione con questo nome', 'error')
            return render_template('decisions/create_session.html')
        
        # Crea la sessione
        session = DecisionSession(
            name=name,
            description=description,
            voting_threshold=voting_threshold,
            allow_public_comments=allow_public_comments,
            created_by=current_user.id,
            status='draft'
        )
        
        try:
            db.session.add(session)
            db.session.commit()
            flash(f'Sessione "{name}" creata con successo!', 'success')
            return redirect(url_for('decisions.view_session', session_id=session.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore nella creazione della sessione: {str(e)}', 'error')
    
    return render_template('decisions/create_session.html')


@decisions_bp.route('/<int:session_id>')
@login_required
def view_session(session_id):
    """Visualizza una sessione di decisione specifica"""
    session = DecisionSession.query.get_or_404(session_id)
    
    # Tab selezionato
    active_tab = request.args.get('tab', 'overview')
    
    # Dati per overview
    participants = session.get_participants()
    
    # Proposte recenti
    recent_proposals = LabelGroupingProposal.query\
        .filter_by(session_id=session_id)\
        .order_by(LabelGroupingProposal.created_at.desc())\
        .limit(5).all()
    
    # Commenti recenti
    recent_comments = LabelDecisionComment.query\
        .filter_by(session_id=session_id)\
        .order_by(LabelDecisionComment.created_at.desc())\
        .limit(5).all()
    
    return render_template('decisions/view_session.html',
                         session=session,
                         participants=participants,
                         recent_proposals=recent_proposals,
                         recent_comments=recent_comments,
                         active_tab=active_tab)


@decisions_bp.route('/<int:session_id>/proposals')
@login_required
def list_proposals(session_id):
    """Lista delle proposte in una sessione"""
    session = DecisionSession.query.get_or_404(session_id)
    
    # Filtri
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    
    # Query base
    query = LabelGroupingProposal.query.filter_by(session_id=session_id)
    
    # Applicazione filtri
    if status_filter != 'all':
        query = query.filter(LabelGroupingProposal.status == status_filter)
    
    if category_filter != 'all':
        query = query.filter(LabelGroupingProposal.category == category_filter)
    
    # Ordinamento
    sort_by = request.args.get('sort', 'created_at')
    if sort_by == 'votes':
        # Ordina per numero di voti (query più complessa)
        proposals = query.all()
        proposals.sort(key=lambda p: p.total_votes, reverse=True)
    elif sort_by == 'approval':
        proposals = query.all()
        proposals.sort(key=lambda p: p.approval_percentage, reverse=True)
    else:  # created_at
        proposals = query.order_by(LabelGroupingProposal.created_at.desc()).all()
    
    # Categorie disponibili per filtro
    categories = db.session.query(LabelGroupingProposal.category)\
        .filter_by(session_id=session_id)\
        .distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('decisions/list_proposals.html',
                         session=session,
                         proposals=proposals,
                         categories=categories,
                         current_status_filter=status_filter,
                         current_category_filter=category_filter,
                         current_sort=sort_by)


@decisions_bp.route('/<int:session_id>/proposals/create', methods=['GET', 'POST'])
@login_required
def create_proposal(session_id):
    """Crea una nuova proposta di raggruppamento"""
    session = DecisionSession.query.get_or_404(session_id)
    
    # Ottieni le categorie dal sistema
    categories = [cat.name for cat in Category.query.order_by(Category.name).all()]
    
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        original_labels_str = request.form.get('original_labels', '').strip()
        proposed_label = request.form.get('proposed_label', '').strip()
        proposed_code = request.form.get('proposed_code', '').strip()
        rationale = request.form.get('rationale', '').strip()
        
        # Validazione
        if not all([category, original_labels_str, proposed_label, proposed_code]):
            flash('Tutti i campi obbligatori devono essere compilati', 'error')
            return render_template('decisions/create_proposal.html', session=session)
        
        # Processa le etichette originali (separate da punto e virgola)
        original_labels = [label.strip() for label in original_labels_str.split(';') if label.strip()]
        
        # Controlla se esiste già una proposta con lo stesso codice
        existing = LabelGroupingProposal.query\
            .filter_by(session_id=session_id, proposed_code=proposed_code).first()
        if existing:
            flash(f'Esiste già una proposta con il codice "{proposed_code}"', 'error')
            return render_template('decisions/create_proposal.html', session=session)
        
        # Crea la proposta
        proposal = LabelGroupingProposal(
            session_id=session_id,
            category=category,
            proposed_label=proposed_label,
            proposed_code=proposed_code,
            rationale=rationale,
            created_by=current_user.id
        )
        
        # Imposta le etichette originali
        proposal.original_labels_list = original_labels
        
        try:
            db.session.add(proposal)
            db.session.commit()
            flash(f'Proposta "{proposed_code}" creata con successo!', 'success')
            return redirect(url_for('decisions.view_proposal', 
                                  session_id=session_id, 
                                  proposal_id=proposal.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore nella creazione della proposta: {str(e)}', 'error')
    
    return render_template('decisions/create_proposal.html', session=session, categories=categories)


@decisions_bp.route('/<int:session_id>/proposals/<int:proposal_id>')
@login_required
def view_proposal(session_id, proposal_id):
    """Visualizza i dettagli di una proposta specifica"""
    session = DecisionSession.query.get_or_404(session_id)
    proposal = LabelGroupingProposal.query.get_or_404(proposal_id)
    
    # Verifica che la proposta appartenga alla sessione
    if proposal.session_id != session_id:
        abort(404)
    
    # Voto dell'utente corrente
    user_vote = proposal.get_user_vote(current_user.id)
    
    # Commenti sulla proposta
    comments = LabelDecisionComment.query\
        .filter_by(proposal_id=proposal_id)\
        .filter_by(parent_id=None)\
        .order_by(LabelDecisionComment.created_at.asc()).all()
    
    return render_template('decisions/view_proposal.html',
                         session=session,
                         proposal=proposal,
                         user_vote=user_vote,
                         comments=comments)


@decisions_bp.route('/<int:session_id>/proposals/<int:proposal_id>/vote', methods=['POST'])
@login_required
def vote_proposal(session_id, proposal_id):
    """Vota una proposta"""
    session = DecisionSession.query.get_or_404(session_id)
    proposal = LabelGroupingProposal.query.get_or_404(proposal_id)
    
    if proposal.session_id != session_id:
        abort(404)
    
    vote_type = request.form.get('vote')
    comment = request.form.get('comment', '').strip()
    
    if vote_type not in ['approve', 'reject', 'abstain']:
        flash('Tipo di voto non valido', 'error')
        return redirect(url_for('decisions.view_proposal', 
                              session_id=session_id, 
                              proposal_id=proposal_id))
    
    # Controlla se l'utente ha già votato
    existing_vote = proposal.get_user_vote(current_user.id)
    
    if existing_vote:
        # Aggiorna il voto esistente
        existing_vote.vote = vote_type
        existing_vote.comment = comment
        existing_vote.updated_at = datetime.utcnow()
        action = 'aggiornato'
    else:
        # Crea un nuovo voto
        new_vote = LabelDecisionVote(
            proposal_id=proposal_id,
            user_id=current_user.id,
            vote=vote_type,
            comment=comment
        )
        db.session.add(new_vote)
        action = 'registrato'
    
    try:
        # Aggiorna lo status della proposta basato sui voti
        proposal.update_status_by_votes(session.voting_threshold)
        
        db.session.commit()
        flash(f'Voto {action} con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore nel salvataggio del voto: {str(e)}', 'error')
    
    return redirect(url_for('decisions.view_proposal', 
                          session_id=session_id, 
                          proposal_id=proposal_id))


@decisions_bp.route('/<int:session_id>/proposals/<int:proposal_id>/comment', methods=['POST'])
@login_required
def add_proposal_comment(session_id, proposal_id):
    """Aggiunge un commento a una proposta"""
    session = DecisionSession.query.get_or_404(session_id)
    proposal = LabelGroupingProposal.query.get_or_404(proposal_id)
    
    if proposal.session_id != session_id:
        abort(404)
    
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    if not content:
        flash('Il commento non può essere vuoto', 'error')
        return redirect(url_for('decisions.view_proposal', 
                              session_id=session_id, 
                              proposal_id=proposal_id))
    
    comment = LabelDecisionComment(
        session_id=session_id,
        proposal_id=proposal_id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('Commento aggiunto con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore nell\'aggiunta del commento: {str(e)}', 'error')
    
    return redirect(url_for('decisions.view_proposal', 
                          session_id=session_id, 
                          proposal_id=proposal_id))


@decisions_bp.route('/<int:session_id>/comment', methods=['POST'])
@login_required
def add_session_comment(session_id):
    """Aggiunge un commento generale alla sessione"""
    session = DecisionSession.query.get_or_404(session_id)
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Il commento non può essere vuoto', 'error')
        return redirect(url_for('decisions.view_session', session_id=session_id))
    
    comment = LabelDecisionComment(
        session_id=session_id,
        user_id=current_user.id,
        content=content
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('Commento aggiunto con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore nell\'aggiunta del commento: {str(e)}', 'error')
    
    return redirect(url_for('decisions.view_session', session_id=session_id))


@decisions_bp.route('/<int:session_id>/import-csv', methods=['GET', 'POST'])
@login_required
def import_csv(session_id):
    """Importa proposte da file CSV"""
    session = DecisionSession.query.get_or_404(session_id)
    
    # Solo il creatore o admin possono importare
    if not session.can_edit(current_user):
        flash('Non hai i permessi per modificare questa sessione', 'error')
        return redirect(url_for('decisions.view_session', session_id=session_id))
    
    if request.method == 'POST':
        # Controlla se è stato caricato un file
        if 'csv_file' not in request.files:
            flash('Nessun file selezionato', 'error')
            return render_template('decisions/import_csv.html', session=session)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('Nessun file selezionato', 'error')
            return render_template('decisions/import_csv.html', session=session)
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                # Legge il CSV
                content = file.read().decode('utf-8')
                csv_reader = csv.DictReader(content.splitlines())
                
                imported_count = 0
                skipped_count = 0
                
                for row in csv_reader:
                    category = row.get('categorie', '').strip()
                    original_labels_str = row.get('etichette usate (raggruppate)', '').strip()
                    proposed_label_full = row.get('etichetta raggruppata', '').strip()
                    
                    if not all([category, original_labels_str, proposed_label_full]):
                        skipped_count += 1
                        continue
                    
                    # Estrae codice e label dalla stringa "S1 — Accessibilità e inclusione"
                    if ' — ' in proposed_label_full:
                        proposed_code, proposed_label = proposed_label_full.split(' — ', 1)
                        proposed_code = proposed_code.strip()
                        proposed_label = proposed_label.strip()
                    else:
                        proposed_code = f"AUTO_{imported_count + 1}"
                        proposed_label = proposed_label_full
                    
                    # Controlla se esiste già
                    existing = LabelGroupingProposal.query\
                        .filter_by(session_id=session_id, proposed_code=proposed_code).first()
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Processa le etichette originali
                    original_labels = [label.strip() for label in original_labels_str.split(';') if label.strip()]
                    
                    # Crea la proposta
                    proposal = LabelGroupingProposal(
                        session_id=session_id,
                        category=category,
                        proposed_label=proposed_label,
                        proposed_code=proposed_code,
                        rationale=f"Importato da CSV - Raggruppamento di {len(original_labels)} etichette",
                        created_by=current_user.id
                    )
                    proposal.original_labels_list = original_labels
                    
                    db.session.add(proposal)
                    imported_count += 1
                
                db.session.commit()
                flash(f'Import completato: {imported_count} proposte importate, {skipped_count} saltate', 'success')
                return redirect(url_for('decisions.list_proposals', session_id=session_id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Errore nell\'import del CSV: {str(e)}', 'error')
        else:
            flash('Il file deve essere in formato CSV', 'error')
    
    return render_template('decisions/import_csv.html', session=session)


@decisions_bp.route('/<int:session_id>/export')
@login_required
def export_decisions(session_id):
    """Esporta le decisioni approvate in formato CSV"""
    session = DecisionSession.query.get_or_404(session_id)
    
    # Solo proposte approvate
    approved_proposals = LabelGroupingProposal.query\
        .filter_by(session_id=session_id, status='approved')\
        .order_by(LabelGroupingProposal.category, LabelGroupingProposal.proposed_code).all()
    
    if not approved_proposals:
        flash('Nessuna proposta approvata da esportare', 'warning')
        return redirect(url_for('decisions.view_session', session_id=session_id))
    
    # Genera il CSV
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['categoria', 'etichette_originali', 'etichetta_finale', 'codice', 'voti_approvazione', 'percentuale_approvazione'])
    
    # Dati
    for proposal in approved_proposals:
        original_labels = '; '.join(proposal.original_labels_list)
        writer.writerow([
            proposal.category,
            original_labels,
            proposal.proposed_label,
            proposal.proposed_code,
            proposal.vote_counts['approve'],
            f"{proposal.approval_percentage:.1f}%"
        ])
    
    # Prepara la risposta
    from flask import Response
    
    output.seek(0)
    filename = f"decisioni_approvate_{session.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@decisions_bp.route('/<int:session_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_session(session_id):
    """Modifica una sessione di decisione"""
    session = DecisionSession.query.get_or_404(session_id)
    
    # Solo il creatore o admin possono modificare
    if not session.can_edit(current_user):
        flash('Non hai i permessi per modificare questa sessione', 'error')
        return redirect(url_for('decisions.view_session', session_id=session_id))
    
    if request.method == 'POST':
        session.name = request.form.get('name', '').strip()
        session.description = request.form.get('description', '').strip()
        session.voting_threshold = float(request.form.get('voting_threshold', 0.6))
        session.allow_public_comments = 'allow_public_comments' in request.form
        session.status = request.form.get('status', 'draft')
        session.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('Sessione aggiornata con successo!', 'success')
            return redirect(url_for('decisions.view_session', session_id=session_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore nell\'aggiornamento: {str(e)}', 'error')
    
    return render_template('decisions/edit_session.html', session=session)


# API endpoints per AJAX
@decisions_bp.route('/api/sessions/<int:session_id>/stats')
@login_required
def api_session_stats(session_id):
    """API per ottenere statistiche di una sessione"""
    session = DecisionSession.query.get_or_404(session_id)
    
    return jsonify({
        'proposal_count': session.proposal_count,
        'approved_count': session.approved_proposals_count,
        'pending_count': session.pending_proposals_count,
        'completion_percentage': session.completion_percentage,
        'participants_count': len(session.get_participants())
    })


@decisions_bp.route('/api/proposals/<int:proposal_id>/votes')
@login_required
def api_proposal_votes(proposal_id):
    """API per ottenere i voti di una proposta"""
    proposal = LabelGroupingProposal.query.get_or_404(proposal_id)
    
    votes_data = []
    for vote in proposal.votes:
        votes_data.append({
            'user': vote.user.username,
            'vote': vote.vote,
            'comment': vote.comment,
            'created_at': vote.created_at.isoformat()
        })
    
    return jsonify({
        'votes': votes_data,
        'vote_counts': proposal.vote_counts,
        'total_votes': proposal.total_votes,
        'approval_percentage': proposal.approval_percentage
    })
