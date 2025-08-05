#!/usr/bin/env python3
"""
Script per creare le tabelle del sistema di decisioni nell'applicazione analisi-mu.
Esegue la migrazione del database aggiungendo le nuove tabelle senza toccare quelle esistenti.
"""

import os
import sys
from flask import Flask
from models import db, DecisionSession, LabelGroupingProposal, LabelDecisionVote, LabelDecisionComment

def create_app():
    """Crea un'istanza minimale dell'app per la migrazione"""
    app = Flask(__name__)
    
    # Configurazione database (usa le stesse impostazioni di app.py)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "analisi_mu.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inizializza il database
    db.init_app(app)
    
    return app

def migrate_database():
    """Esegue la migrazione del database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verifica se le tabelle esistono già
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            decision_tables = [
                'decision_session',
                'label_grouping_proposal', 
                'label_decision_vote',
                'label_decision_comment'
            ]
            
            tables_to_create = []
            for table in decision_tables:
                if table not in existing_tables:
                    tables_to_create.append(table)
            
            if not tables_to_create:
                print("✅ Tutte le tabelle del sistema decisioni sono già presenti nel database")
                return True
            
            print(f"🔄 Creazione di {len(tables_to_create)} nuove tabelle...")
            
            # Crea solo le tabelle dei modelli delle decisioni
            DecisionSession.__table__.create(db.engine, checkfirst=True)
            LabelGroupingProposal.__table__.create(db.engine, checkfirst=True)
            LabelDecisionVote.__table__.create(db.engine, checkfirst=True)
            LabelDecisionComment.__table__.create(db.engine, checkfirst=True)
            
            print("✅ Database migrato con successo!")
            print("\nTabelle create:")
            for table in tables_to_create:
                print(f"  ✓ {table}")
            
            print("\n🎉 Il sistema di decisioni è ora disponibile!")
            print("Puoi accedervi dal menu 'Decisioni' nell'applicazione web.")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {str(e)}")
            return False

def verify_installation():
    """Verifica che l'installazione sia corretta"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            decision_tables = [
                'decision_session',
                'label_grouping_proposal', 
                'label_decision_vote',
                'label_decision_comment'
            ]
            
            print("🔍 Verifica installazione sistema decisioni:")
            all_present = True
            
            for table in decision_tables:
                if table in existing_tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ❌ {table} - MANCANTE")
                    all_present = False
            
            if all_present:
                print("\n✅ Sistema decisioni installato correttamente!")
                
                # Verifica che i modelli funzionino
                session_count = DecisionSession.query.count()
                print(f"📊 Sessioni di decisione nel database: {session_count}")
                
            else:
                print("\n❌ Installazione incompleta. Esegui la migrazione.")
            
            return all_present
            
        except Exception as e:
            print(f"❌ Errore durante la verifica: {str(e)}")
            return False

def create_sample_data():
    """Crea dati di esempio per testare il sistema"""
    app = create_app()
    
    with app.app_context():
        try:
            from models import User
            
            # Trova un utente esistente per la demo
            admin_user = User.query.filter_by(role='amministratore').first()
            if not admin_user:
                admin_user = User.query.first()
            
            if not admin_user:
                print("❌ Nessun utente trovato nel database. Crea prima un utente.")
                return False
            
            # Controlla se esistono già sessioni
            if DecisionSession.query.count() > 0:
                print("ℹ️  Esistono già sessioni di decisione nel database.")
                return True
            
            # Crea una sessione di esempio
            sample_session = DecisionSession(
                name="Demo - Raggruppamento Etichette AI",
                description="Sessione dimostrativa per testare il sistema di decisioni collaborative. Qui si decide come raggruppare le etichette per l'analisi dei dati sull'AI nell'educazione.",
                status="active",
                voting_threshold=0.6,
                allow_public_comments=True,
                created_by=admin_user.id
            )
            
            db.session.add(sample_session)
            db.session.flush()  # Per ottenere l'ID
            
            # Crea alcune proposte di esempio
            sample_proposals = [
                {
                    'category': 'Impatti sugli studenti',
                    'original_labels': ['Accessibilità', 'Inclusione', 'Supporto Tecnico'],
                    'proposed_label': 'Accessibilità e inclusione',
                    'proposed_code': 'S1',
                    'rationale': 'Questi concetti sono strettamente correlati e riguardano tutti l\'accesso equo all\'educazione supportata dall\'AI.'
                },
                {
                    'category': 'Impatti sul docente',
                    'original_labels': ['Velocizzazione attività', 'Facilitazione del lavoro', 'Ricerca di contenuti'],
                    'proposed_label': 'Efficienza e risparmio di tempo',
                    'proposed_code': 'D1',
                    'rationale': 'Tutte queste etichette si riferiscono a come l\'AI aiuta i docenti a essere più efficienti.'
                },
                {
                    'category': 'Rischi/Sentiment',
                    'original_labels': ['Aspetti etici', 'Utilizzo consapevole'],
                    'proposed_label': 'Etica e uso consapevole',
                    'proposed_code': 'R1',
                    'rationale': 'Raggruppa le preoccupazioni etiche e la necessità di un uso responsabile dell\'AI.'
                }
            ]
            
            for proposal_data in sample_proposals:
                proposal = LabelGroupingProposal(
                    session_id=sample_session.id,
                    category=proposal_data['category'],
                    proposed_label=proposal_data['proposed_label'],
                    proposed_code=proposal_data['proposed_code'],
                    rationale=proposal_data['rationale'],
                    created_by=admin_user.id
                )
                proposal.original_labels_list = proposal_data['original_labels']
                db.session.add(proposal)
            
            db.session.commit()
            
            print("✅ Dati di esempio creati con successo!")
            print(f"👤 Utente demo: {admin_user.username}")
            print(f"📋 Sessione: {sample_session.name}")
            print(f"📝 Proposte create: {len(sample_proposals)}")
            print("\n🚀 Vai su /decisions per vedere il sistema in azione!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore nella creazione dei dati di esempio: {str(e)}")
            return False

def main():
    """Funzione principale dello script"""
    if len(sys.argv) < 2:
        print("Usage: python migrate_decisions.py [migrate|verify|sample]")
        print("\nComandi disponibili:")
        print("  migrate  - Crea le tabelle del sistema decisioni")
        print("  verify   - Verifica che l'installazione sia corretta")
        print("  sample   - Crea dati di esempio per testare il sistema")
        return
    
    command = sys.argv[1].lower()
    
    print("🎯 Sistema di Decisioni per l'Etichettatura - Analisi MU")
    print("=" * 60)
    
    if command == 'migrate':
        success = migrate_database()
        if success:
            print("\n🔄 Vuoi anche creare dati di esempio? (y/n): ", end="")
            response = input().lower().strip()
            if response == 'y':
                create_sample_data()
    
    elif command == 'verify':
        verify_installation()
    
    elif command == 'sample':
        create_sample_data()
    
    else:
        print(f"❌ Comando sconosciuto: {command}")
        print("Comandi disponibili: migrate, verify, sample")

if __name__ == '__main__':
    main()
