from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import secrets
from werkzeug.utils import secure_filename  # ✅ Correct
from datetime import datetime, date
from sqlalchemy import desc
import os
from datetime import datetime, date, timedelta, time
import json
import re
from sqlalchemy import create_engine

import pymysql
pymysql.install_as_MySQLdb()


app = Flask(__name__)

# Clé secrète pour la gestion des sessions
app.secret_key = secrets.token_hex(16)

# Configuration de la base de données MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:BLHHHtLaXnryjOkEjhTazvmCGTRyxkTi@yamabiko.proxy.rlwy.net:16438/railway'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Désactive la notification de modifications
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Répertoire pour stocker les fichiers
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}  # Extensions de fichiers autorisées

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

db_url = app.config['SQLALCHEMY_DATABASE_URI']
print("db_url =", db_url)
engine=create_engine(db_url)


# Modèle Utilisateur
class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'

    id_uti = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    mot_de_passe = db.Column(db.String(255))
    role = db.Column(db.String(50))
    status = db.Column(db.String(255), default='en_attente')

# Fonction pour ajouter un utilisateur dans la base de données
def add_utilisateur_to_db(nom, prenom, email, password_hash):
    try:
        nouvel_utilisateur = Utilisateur(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=password_hash,
            role='etudiant',  # Le rôle par défaut
            status='en_attente'  # Compte en attente par défaut
        )
        db.session.add(nouvel_utilisateur)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'insertion dans la base de données : {e}", "error")
def is_password_strong(password):
    """Vérifie si le mot de passe est suffisamment fort."""
    if len(password) < 8:  # Changement ici : vérification de la longueur minimale
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une lettre majuscule."
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une lettre minuscule."
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, None


    
@app.route('/')
def avant_page():
    return render_template('avant_page.html')  # Une page simple de bienvenue ou d'introduction

@app.route('/connexion_redirect')
def connexion_redirect():
    return redirect(url_for('connexion_011737'))


@app.route('/connexion_011737', methods=['GET', 'POST'])
def connexion_011737():
    message = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Connexion de l'administrateur
        if email == 'admin@gmail.com' and password == '123456789admin?':
            session['utilisateur_id'] = 'admin'
            return redirect(url_for('admin'))

        # Vérification des informations d'identification de l'étudiant
        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur:
            # Vérification de la longueur du mot de passe lors de la connexion
            if len(password) < 8:
                message = "Mot de passe trop court. Veuillez utiliser au moins 8 caractères."
            elif check_password_hash(utilisateur.mot_de_passe, password):
                if utilisateur.status == 'bloqué':
                    message = "Votre compte a été bloqué. Vous ne pouvez pas vous connecter."
                elif utilisateur.status == 'supprimé':
                    message = "Votre compte a été supprimé. Vous ne pouvez pas vous connecter."
                elif utilisateur.status == 'en_attente':
                    message = "Votre compte est en attente d'activation par un administrateur. Vous pourrez vous connecter dès qu'il sera validé."
                elif utilisateur.status == 'actif':
                    session['utilisateur_id'] = utilisateur.id_uti
                    session['prenom_utilisateur'] = utilisateur.prenom 
                    return redirect(url_for('page_acceuil'))
            else:
                message = "Mot de passe incorrect."
        else:
            message = "Aucun utilisateur trouvé avec cet email."

    return render_template('connexion_011737.html', message=message)

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        try:
            # Vérification des champs du formulaire
            if not all(field in request.form for field in ['nom', 'prenom', 'email', 'password', 'confirm-password']):
                flash("Tous les champs sont obligatoires. Veuillez réessayer.", "error")
                return redirect(url_for('inscription'))

            nom = request.form['nom']
            prenom = request.form['prenom']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm-password']

            # Vérification de la longueur du mot de passe
            if len(password) < 8:
                flash("Le mot de passe doit contenir au moins 8 caractères. Veuillez réessayer.", "error")
                return redirect(url_for('inscription'))

            # Vérification de la complexité du mot de passe
            is_strong, message = is_password_strong(password)
            if not is_strong:
                flash(f"{message} Veuillez réessayer.", "error")
                return redirect(url_for('inscription'))

            # Vérification de la correspondance des mots de passe
            if password != confirm_password:
                flash("Les mots de passe ne correspondent pas. Veuillez réessayer.", "error")
                return redirect(url_for('inscription'))

            # Vérification de l'email unique
            if Utilisateur.query.filter_by(email=email).first():
                flash("Cet email est déjà utilisé. Veuillez réessayer avec un autre email.", "error")
                return redirect(url_for('inscription'))

            # Hachage du mot de passe et enregistrement
            password_hash = generate_password_hash(password)
            add_utilisateur_to_db(nom, prenom, email, password_hash)

               # Après succès
            flash("🎉 Inscription réussie! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('connexion_011737', _anchor='message-container'))

        except Exception as e:
            flash("❌ Une erreur s'est produite lors de l'inscription. Veuillez réessayer.", "error")
            # Loggez l'erreur pour le débogage
            print(f"Erreur lors de l'inscription: {str(e)}")
            return redirect(url_for('inscription'))

    return render_template('inscription.html')


@app.route('/page_acceuil')
def page_acceuil():
    prenom_utilisateur = session.get('prenom_utilisateur', 'Invité')
    return render_template('page_acceuil.html', prenom_utilisateur=prenom_utilisateur)


@app.route('/admin/messages')
def admin_messages():
    # Récupère tous les messages triés par date (du plus récent au plus ancien)
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    def __repr__(self):
        return f'<ContactMessage {self.name}>'

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Créer un nouveau message
        new_message = ContactMessage(
            name=name,
            email=email,
            message=message
        )
        
        try:
            db.session.add(new_message)
            db.session.commit()
            flash('Votre message a été envoyé avec succès! Nous vous répondrons dès que possible.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'envoi du message: {str(e)}", 'error')
        
        return redirect(url_for('page_acceuil'))
    








# Route pour la page de renseignement
@app.route('/renseignement')
def renseignement():
    return render_template('renseignement.html')

# Route pour la page d'inscription
@app.route('/page_inscription')
def page_inscription():
    return render_template('page_inscription.html')

# Route pour le guide académique


@app.route('/guide-academique')
def guide_academique():
    return render_template('guideA.html')
@app.route('/aide')
def aide():
    return render_template('acces aide.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')
@app.route('/gestion')
def gestion():
    return render_template('gestion_documents.html')


# Route pour Admin
@app.route('/admin', endpoint='admin')
def admin():
    return render_template('admin.html')






@app.route('/user')
def user():
    utilisateurs = Utilisateur.query.all()  # Récupère tous les utilisateurs de la base de données
    return render_template('Utilisateur.html', users=utilisateurs)  # Affiche la liste dans le template

# Fonction pour bloquer un utilisateur
@app.route('/bloquer/<email>', methods=['GET'])
def bloquer_utilisateur(email):
    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if utilisateur:
        utilisateur.status = 'bloqué'
        db.session.commit()
        flash('L\'utilisateur a été bloqué avec succès!', 'success')
    else:
        flash('Utilisateur non trouvé!', 'danger')
    return redirect(url_for('user'))

# Fonction pour débloquer un utilisateur
@app.route('/debloquer/<email>', methods=['GET'])
def debloquer_utilisateur(email):
    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if utilisateur:
        utilisateur.status = 'actif'
        db.session.commit()
        flash('L\'utilisateur a été débloqué avec succès!', 'success')
    else:
        flash('Utilisateur non trouvé!', 'danger')
    return redirect(url_for('user'))

# Fonction pour supprimer un utilisateur
@app.route('/supprimer/<email>', methods=['GET'])
def supprimer_utilisateur(email):
    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if utilisateur:
        db.session.delete(utilisateur)
        db.session.commit()
        flash('L\'utilisateur a été supprimé avec succès!', 'success')
    else:
        flash('Utilisateur non trouvé!', 'danger')
    return redirect(url_for('user'))



# Modèle pour la table "lieu"
class Lieu(db.Model):
    __tablename__ = 'lieu'

    id_lieu = db.Column(db.Integer, primary_key=True)
    nom_lieu = db.Column(db.String(100), nullable=False)
    type_lieu = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __init__(self, nom_lieu, type_lieu, latitude, longitude, description):
        self.nom_lieu = nom_lieu
        self.type_lieu = type_lieu
        self.latitude = latitude
        self.longitude = longitude
        self.description = description

@app.route('/lieux')
def lieux():
    # Récupérer tous les lieux de la base de données
    lieux = Lieu.query.all()

    # Vérifier si nous avons des lieux et les afficher
    print(lieux)  # Pour le débogage

    return render_template('lieux.html', lieux=lieux)  # Passe la liste des lieux au template

@app.route('/ajouter_lieu', methods=['GET', 'POST'])
def ajouter_lieu():
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            nom_lieu = request.form['nom_lieu']
            type_lieu = request.form['type_lieu']
            latitude = float(request.form['latitude'])  # Assurez-vous que c'est un nombre
            longitude = float(request.form['longitude'])  # Assurez-vous que c'est un nombre
            description = request.form['description']

            # Ajouter le nouveau lieu à la base de données
            nouveau_lieu = Lieu(nom_lieu=nom_lieu, type_lieu=type_lieu, latitude=latitude, longitude=longitude, description=description)
            db.session.add(nouveau_lieu)
            db.session.commit()  # Enregistrez les changements

            # Redirige vers la page des lieux
            return redirect(url_for('lieux')) 

        except Exception as e:
            db.session.rollback()  # Annulez la transaction en cas d'erreur inattendue
            flash(f"Erreur lors de l'ajout du lieu : {e}", "error")

        return redirect(url_for('lieux'))  # Redirige vers la page des lieux

    return render_template('AjouterLieu.html')  # Affiche le formulaire d'ajout du lieu

@app.route('/modifier_lieu/<int:index>', methods=['GET', 'POST'])
def modifier_lieu(index):
    lieu = Lieu.query.get(index)  # Récupérer le lieu par son ID
    if lieu is None:
        flash("Le lieu n'existe pas", "error")
        return redirect(url_for('lieux'))  # Si le lieu n'existe pas, rediriger vers la liste des lieux
    
    if request.method == 'POST':
        try:
            # Mettre à jour les données du lieu avec les valeurs du formulaire
            lieu.nom_lieu = request.form['nom_lieu']
            lieu.type_lieu = request.form['type_lieu']
            lieu.latitude = float(request.form['latitude'])  # Assurez-vous que latitude est un float
            lieu.longitude = float(request.form['longitude'])  # Assurez-vous que longitude est un float
            lieu.description = request.form['description']

            # Sauvegarder les modifications dans la base de données
            db.session.commit()
            flash("Lieu modifié avec succès!", "success")
            return redirect(url_for('lieux'))  # Rediriger vers la liste des lieux après modification

        except Exception as e:
            db.session.rollback()  # Annulez la transaction en cas d'erreur
            flash(f"Erreur lors de la modification : {e}", "error")

    # Si la méthode est GET, rendre le formulaire avec les données existantes du lieu
    return render_template('ModifierLieu.html', lieu=lieu)

@app.route('/supprimer_lieu/<int:index>', methods=['GET', 'POST'])
def supprimer_lieu(index):
    lieu = Lieu.query.get(index)  # Recherche du lieu par son ID
    if lieu:
        if request.method == 'POST':
            db.session.delete(lieu)  # Suppression du lieu
            db.session.commit()  # Validation de la suppression dans la base de données
            flash("Lieu supprimé avec succès!", "success")
            return redirect(url_for('lieux'))  # Redirection vers la page des lieux après la suppression
        else:
            return render_template('SupprimeLieu.html', lieu=lieu)  # Affiche le modal de confirmation
    else:
        flash("Lieu non trouvé!", "danger")
        return redirect(url_for('lieux'))  # Redirige si le lieu n'existe pas




# Modèle Document
class Document(db.Model):
    __tablename__ = 'documents'
    id_document = db.Column(db.Integer, primary_key=True)
    type_document = db.Column(db.String(100), nullable=False)
    titre_document = db.Column(db.String(200), nullable=False)
    lien_fichier = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Document {self.id_document}>"

# Créer le répertoire d'upload s'il n'existe pas
def create_upload_folder():
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

# Créer le répertoire au démarrage de l'application
create_upload_folder()

# Fonction pour vérifier les extensions valides
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route pour afficher les documents
@app.route('/docs')
def docs():
    documents = Document.query.all()
    return render_template('documents.html', documents=documents)

# Route pour ajouter un document
@app.route('/ajouter_document', methods=['GET', 'POST'])
def ajouter_document():
    if request.method == 'POST':
        type_document = request.form['document-type']
        titre_document = request.form['document-title']
        file = request.files['document-file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(file_path)
                nouveau_document = Document(
                    type_document=type_document,
                    titre_document=titre_document,
                    lien_fichier=filename
                )
                db.session.add(nouveau_document)
                db.session.commit()  # Commit pour valider l'ajout dans la base de données
                flash('Document ajouté avec succès!', 'success')
                return redirect('/docs')
            except Exception as e:
                db.session.rollback()  # Rollback si une erreur se produit
                flash(f"Erreur lors de l'ajout du document : {str(e)}", 'error')
                return redirect('/docs')
        else:
            flash('Erreur lors de l\'ajout du document, fichier non valide.', 'error')

    return render_template('AjouterDoc.html')

# Route pour modifier un document
@app.route('/modifier_document/<int:document_id>', methods=['GET', 'POST'])
def modifier_document(document_id):
    document = Document.query.get(document_id)

    if request.method == 'POST':
        document.type_document = request.form['type_document']
        document.titre_document = request.form['titre_document']

        if 'document-file' in request.files:
            file = request.files['document-file']
            if file and allowed_file(file.filename):
                if document.lien_fichier:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], document.lien_fichier))
                    except FileNotFoundError:
                        pass
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                document.lien_fichier = filename

        try:
            db.session.commit()  # Commit pour valider les changements dans la base de données
            flash('Document modifié avec succès!', 'success')
            return redirect(url_for('docs'))
        except Exception as e:
            db.session.rollback()  # Rollback si une erreur se produit
            flash(f"Erreur lors de la modification du document : {str(e)}", 'error')

    return render_template('ModifierDoc.html', document=document)

# Route pour supprimer un document
@app.route('/supprimer_document/<int:document_id>', methods=['GET', 'POST'])
def supprimer_document(document_id):
    if request.method == 'POST':
        document = Document.query.get(document_id)
        if document:
            # Supprimer le fichier du serveur
            if document.lien_fichier:
                try:
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.lien_fichier)
                    os.remove(file_path)  # Supprimer le fichier du système
                except FileNotFoundError:
                    pass  # Si le fichier n'est pas trouvé, ne rien faire
            try:
                db.session.delete(document)  # Supprimer du modèle
                db.session.commit()  # Commit pour valider la suppression
                flash('Document supprimé avec succès!', 'success')
            except Exception as e:
                db.session.rollback()  # Rollback si une erreur se produit
                flash(f"Erreur lors de la suppression du document : {str(e)}", 'error')

        return redirect(url_for('docs'))  # Redirige vers la liste des documents après la suppression

    return render_template('SuppressionDoc.html', document_id=document_id)



from flask import render_template, abort

 

@app.route('/voir_document/<int:document_id>')
def voir_document(document_id):
    # Récupérer le document avec l'ID donné
    document = Document.query.get(document_id)
    
    # Si le document n'existe pas, afficher une erreur 404
    if document is None:
        abort(404)
    
    # Renvoyer le lien du fichier pour l'affichage
    return redirect(document.lien_fichier)

# Route de déconnexion
@app.route('/deconnexion')
def deconnexion():
    session.pop('utilisateur_id', None)
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for('connexion_011737'))

@app.route('/chatbox', methods=['GET', 'POST'])
def chatbox():
    if request.method == 'POST':
        user_message = request.form['message']
        bot_response = get_bot_response(user_message)
        return jsonify({"response": bot_response})

    return render_template('chatbox.html')

def get_bot_response(user_message):
    responses = {
        "salut": "Salut! Comment puis-je vous aider aujourd'hui?",
        "bonjour": "Salut! Comment puis-je vous aider aujourd'hui?",
        "bonsoir": "Salut! Comment puis-je vous aider aujourd'hui?",
        "bsr": "Salut! Comment puis-je vous aider aujourd'hui?",
        "ça va?": "Je vais bien, merci! Et toi?",
        "cv": "Je vais bien, merci! Et toi?",
        "bye": "Au revoir! À bientôt!",
        "help": "Je suis là pour vous aider. Que puis-je faire pour vous?",
        "aide moi": "Je suis là pour vous aider. Que puis-je faire pour vous?",
        "université": "L'université offre une large gamme de formations. Que voulez-vous savoir à propos de l'université?",
        "universite de djibouti": "L'université offre une large gamme de formations. Que voulez-vous savoir à propos de l'université?",
        "quelles sont les formations disponibles?": "Nous proposons des formations en informatique, droit, médecine, etc. Voulez-vous plus de détails?",
        "inscription": "L'inscription se fait en ligne. Vous devez remplir un formulaire sur notre site web et fournir des documents comme votre pièce d'identité et vos relevés de notes.",
        "comment s'inscrire à l'universite?": "L'inscription se fait en ligne. Vous devez remplir un formulaire sur notre site web et fournir des documents comme votre pièce d'identité et vos relevés de notes.",
        "étapes d'inscription": "Les étapes d'inscription sont les suivantes : 1. Remplir le formulaire en ligne. 2. Télécharger les documents nécessaires. 3. Attendre la confirmation de l'inscription.",
        "donne moi les etapes de l'inscription": "Les étapes d'inscription sont les suivantes : 1. Remplir le formulaire en ligne. 2. Télécharger les documents nécessaires. 3. Attendre la confirmation de l'inscription.",
        "comment s'inscrire?": "Vous pouvez vous inscrire directement sur notre site en remplissant le formulaire d'inscription et en téléchargeant les documents requis.",
        "date limite d'inscription": "La date limite pour l'inscription est le 30 juin de chaque année.",
        "documents nécessaires": "Les documents nécessaires pour l'inscription sont : votre pièce d'identité, vos relevés de notes et votre diplôme (si disponible).",
        "frais d'inscription": "Les frais d'inscription varient en fonction du programme. Veuillez consulter notre site web pour plus de détails.",
        "bourses disponibles": "Oui, nous offrons des bourses basées sur le mérite et les besoins financiers. Voulez-vous plus d'informations?",
        "logement étudiant": "L'université dispose de résidences étudiantes. Les places sont limitées, il est conseillé de faire une demande tôt.",
        "activités étudiantes": "Nous avons de nombreux clubs et associations étudiantes. Il y a toujours quelque chose à faire sur le campus!",
        "bibliothèque": "La bibliothèque de l'université est ouverte de 8h à 22h du lundi au vendredi.",
        "services de santé": "Nous avons un service de santé sur le campus avec des médecins et des infirmières disponibles.",
        "emplois étudiants": "Oui, nous offrons des emplois à temps partiel sur le campus. Consultez le bureau des services aux étudiants pour plus d'informations.",
        "cours en ligne": "Certains de nos cours sont disponibles en ligne. Veuillez consulter notre site web pour la liste complète.",
        "programmes d'échange": "Oui, nous avons des programmes d'échange avec plusieurs universités à l'étranger.",
        "contacts utiles": "Vous pouvez contacter le bureau des admissions pour toute question concernant l'inscription.",
        "ou se trouve l'universite?": "L'université est située à Djibouti-ville. Voici l'adresse exacte : ...",
        "default": "Désolé, je n'ai pas compris. Pouvez-vous reformuler ?"
    }

    for key, response in responses.items():
        if key in user_message.lower():
            return response

    return responses["default"]

class Planning(db.Model):
    __tablename__ = 'planning'

    id_event = db.Column(db.Integer, primary_key=True)
    id_uti = db.Column(db.Integer, db.ForeignKey('utilisateur.id_uti'), nullable=False)
    titre_event = db.Column(db.String(100), nullable=False)
    date_event = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    
    notified = db.Column(db.Boolean, default=False)  # Nouveau champ
    
    utilisateur = db.relationship('Utilisateur', backref='plannings')
@app.route('/pla')
def pla():
    if 'utilisateur_id' not in session:
        return redirect(url_for('connexion_011737'))
    
    utilisateur_id = session['utilisateur_id']
    
    today = date.today()
    now = datetime.now()
    
    # Événements du jour
    today_events = Planning.query.filter(
        Planning.date_event == today,
        Planning.id_uti == utilisateur_id
    ).order_by(Planning.heure_debut).all()
    
    events_count = Planning.query.filter(
        Planning.id_uti == utilisateur_id,
        Planning.date_event >= today,
        Planning.date_event <= today + timedelta(days=1),
        Planning.notified == False
    ).count()
    # Tous les événements groupés par date
    all_events = Planning.query.filter(
        Planning.id_uti == utilisateur_id
    ).order_by(Planning.date_event, Planning.heure_debut).all()
    
    # Organisation par date avec formatage
    events_by_date = {}
    for event in all_events:
        date_key = event.date_event.strftime('%Y-%m-%d')  # Format comme clé
        if date_key not in events_by_date:
            events_by_date[date_key] = []
         # Configurer la locale française
   
        events_by_date[date_key].append({
            'id': event.id_event,
            'title': event.titre_event,
            'description': event.description,
            'date_display': event.date_event.strftime('%A %d %B %Y'),  # Formaté pour l'affichage
            'start_time': event.heure_debut.strftime('%H:%M'),
            'end_time': event.heure_fin.strftime('%H:%M')
            
        })
    
    return render_template('pla.html',
                         today_events=today_events,
                         events_by_date=events_by_date,
                         today=today.strftime('%Y-%m-%d'),
                         events_count=events_count)

@app.route('/add_event', methods=['POST'])
def add_event():
    if 'utilisateur_id' not in session:
        return redirect(url_for('connexion_011737'))

    try:
        # Récupère les données selon le content-type
        if request.content_type == 'application/json':
            data = request.get_json()
            titre = data['title']
            heure_debut = data['start_time']
            heure_fin = data['end_time']
        else:
            titre = request.form['titre']
            heure_debut = request.form['heure_debut']
            heure_fin = request.form['heure_fin']

        nouvel_event = Planning(
            titre_event=titre,
            description=request.form.get('description', ''),
            date_event=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            heure_debut=datetime.strptime(heure_debut, '%H:%M').time(),
            heure_fin=datetime.strptime(heure_fin, '%H:%M').time(),
            notified=False,
            id_uti=session['utilisateur_id']
        )
        
        db.session.add(nouvel_event)
        db.session.commit()
        flash("Événement ajouté avec succès!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur: {str(e)}", "error")
    
    return redirect(url_for('pla'))

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'utilisateur_id' not in session:
        return jsonify({'success': False, 'error': 'Non autorisé'}), 401
    
    event = Planning.query.filter_by(
        id_event=event_id,  # Utilisez le bon nom de colonne (id_event)
        id_uti=session['utilisateur_id']  # Vérification de propriété
    ).first()
    
    if not event:
        return jsonify({'success': False, 'error': 'Événement non trouvé'}), 404
    
    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    if 'utilisateur_id' not in session:
        return jsonify({'success': False, 'error': 'Non autorisé'}), 401
    
    try:
        data = request.get_json()
        event = Planning.query.get_or_404(event_id)
        
        # Réinitialiser notified si la date change pour aujourd'hui/futur
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if new_date >= date.today() and event.date_event < date.today():
            event.notified = False
        
        # Mise à jour des autres champs
        event.titre_event = data['title']
        event.description = data.get('description', '')
        event.date_event = new_date
        event.heure_debut = datetime.strptime(data['start_time'], '%H:%M').time()
        event.heure_fin = datetime.strptime(data['end_time'], '%H:%M').time()
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_event/<int:event_id>')
def get_event(event_id):
    # Vérification robuste de la session
    if 'utilisateur_id' not in session:
        return jsonify({'error': 'Unauthorized', 'login_required': True}), 401
    
    # Récupération de l'événement
    event = Planning.query.filter_by(
        id_event=event_id,
        id_uti=session['utilisateur_id']  # Vérification du propriétaire
    ).first_or_404(description="Événement non trouvé")
    
    # Formatage de la réponse
    return jsonify({
        'id': event.id_event,
        'title': event.titre_event,
        'description': event.description or '',
        'date': event.date_event.strftime('%Y-%m-%d'),
        'start_time': event.heure_debut.strftime('%H:%M'),
        'end_time': event.heure_fin.strftime('%H:%M')
    })

@app.context_processor
def inject_events_count():
    if 'utilisateur_id' not in session:
        return {'events_count': 0}
    
    today = date.today()
    count = Planning.query.filter(
        Planning.id_uti == session['utilisateur_id'],
        Planning.notified == False,
        Planning.date_event >= today
    ).count()
    
    return {'events_count': count}
from flask import send_from_directory

@app.route('/telecharger/<int:document_id>')
def telecharger(document_id):
    # 1. Trouver le document dans la base
    doc = Document.query.get_or_404(document_id)
    
    # 2. Chemin complet du fichier
    chemin_fichier = os.path.join(app.config['UPLOAD_FOLDER'], doc.lien_fichier)
    
    # 3. Vérifier que le fichier existe
    if not os.path.exists(chemin_fichier):
        return "Fichier introuvable", 404
    
    # 4. Envoyer le fichier
    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=doc.lien_fichier,
        as_attachment=True,
        download_name=doc.titre_document + os.path.splitext(doc.lien_fichier)[1]  # Garde l'extension (.pdf, .docx)
    )



@app.route('/carte')
def carte():
    return render_template('carte.html')




if __name__ == "__main__":
    with app.app_context():  # Créer un contexte d'application
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True)
