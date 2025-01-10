from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseForbidden
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .models import Rdv, Ordonnance, Certificat
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from .forms import SignUpForm, PostForm, LoginForm
from datetime import datetime, time
from django.conf import settings
from bidi.algorithm import get_display
import textwrap
import os
import arabic_reshaper
import codecs

# Créez vos vues ici.

# Vue pour la page d'accueil
def home(request):
    """
    Affiche la page d'accueil du site.
    """
    return render(request, 'home.html')

from .models import FichePatient

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Sauvegarde de l'utilisateur
            user = form.save()

            # Création de la fiche patient
            FichePatient.objects.create(
                id_patient=user,
                nom=user.last_name,
                prenom=user.first_name,
                age=form.cleaned_data['age'],
                sexe=form.cleaned_data['gender'],
                tel=form.cleaned_data['phone'],
                motif_consultation=''
            )

            # Authentification et connexion
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')  # Redirigez vers la page d'accueil ou une autre page
        else:
            # Afficher toutes les erreurs du formulaire
            for field, errors in form.errors.items():
                messages.error(request, f"{field}: {', '.join(errors)}")
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})


# Vue pour la connexion des utilisateurs
def login_view(request):
    """
    Gère la connexion des utilisateurs en vérifiant leur nom d'utilisateur et mot de passe.
    Si la connexion réussit, l'utilisateur est redirigé en fonction de son rôle (staff ou non).
    Si l'authentification échoue, un message d'erreur est affiché.
    """
    form = LoginForm(request.POST or None)  # Instanciation du formulaire
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)  # Authentification
            
            if user is not None:
                login(request, user)  # Connexion de l'utilisateur
                
                # Redirection en fonction du rôle de l'utilisateur
                if user.is_staff:  # Si l'utilisateur est un membre du staff
                    return redirect('/admin/')  # Redirige vers l'administration Django
                else:
                    return redirect('/panel/')  # Redirige vers la page d'accueil ou une autre page
                
            else:
                # Ajouter un message d'erreur si l'authentification échoue
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    
    # Rendu du formulaire de connexion
    return render(request, 'login.html', {'form': form})

# Vue pour la déconnexion des utilisateurs
def logout_view(request):
    """
    Déconnecte l'utilisateur et redirige vers la page d'accueil.
    """
    logout(request)
    return redirect('home')

# Fonction de calcul du numéro du prochain rendez-vous pour une date donnée
def CountNumeroRdvForDay(rdv_date):
    """
    Calcule le numéro du prochain rendez-vous pour une date spécifique.
    Cette fonction récupère tous les rendez-vous de la date donnée, trie par numéro de rendez-vous,
    puis retourne le numéro suivant disponible. Si aucun rendez-vous n'existe pour la date, elle retourne 1.
    """
    rdvs_on_date = Rdv.objects.filter(date=rdv_date).order_by('num_rdv')
    last_rdv = rdvs_on_date.aggregate(Max('num_rdv'))['num_rdv__max']

    # Retourne le prochain numéro de rendez-vous (ou 1 si aucun rendez-vous n'existe)
    return (last_rdv or 0) + 1



@login_required
def rdv_new(request):
    """
    Gère la création d'un nouveau rendez-vous pour un utilisateur connecté.
    Le formulaire est validé, puis un rendez-vous est associé à l'utilisateur. 
    Si l'heure actuelle est après 17h00 pour la date du jour, une erreur est ajoutée.
    Le numéro du rendez-vous est déterminé dynamiquement en fonction des rendez-vous existants pour cette date.
    """
    form = PostForm(request.POST or None)

    if form.is_valid():
        # Sauvegarde du formulaire sans validation immédiate
        rdv = form.save(commit=False)
        rdv.id_patient = request.user  # Associe l'utilisateur connecté comme patient
        rdv_date = form.cleaned_data['date']  # Récupère la date du rendez-vous depuis le formulaire

        # Vérifie si l'heure actuelle dépasse 17h00 pour la date du jour
        if rdv_date == datetime.now().date() and datetime.now().time() >= time(17, 0):
            form.add_error(None, "Le cabinet est fermé après 17h00. Veuillez choisir une autre date.")
        else:
            try:
                # Assigne le numéro du rendez-vous basé sur la date et le numéro existant
                rdv.num_rdv = CountNumeroRdvForDay(rdv_date)
                rdv.save()  # Sauvegarde du rendez-vous
                return redirect('rdv_list')  # Redirection vers la liste des rendez-vous
            except ValidationError as e:
                # En cas d'erreur, ajoute l'erreur à la liste des erreurs du formulaire
                form.add_error(None, str(e))

    # Rendu du formulaire de création de rendez-vous
    return render(request, 'panel.html', {'form': form})


@login_required
def rdv_list(request):
    """
    Affiche la liste des rendez-vous de l'utilisateur connecté.
    Si l'utilisateur est un administrateur, tous les rendez-vous sont affichés.
    Sinon, seul l'utilisateur connecté peut voir ses propres rendez-vous.
    Si aucun rendez-vous n'existe, un message est affiché et un bouton pour en créer un est proposé.
    """
    # Vérifie si l'utilisateur est un administrateur ou un utilisateur normal
    if request.user.is_superuser:
        rdv = Rdv.objects.all()  # Si l'utilisateur est admin, on récupère tous les rendez-vous
    else:
        rdv = Rdv.objects.filter(id_patient=request.user.id)  # Si l'utilisateur est un patient, on récupère ses propres rendez-vous
    
    data = {}

    if not rdv:  # Si l'utilisateur n'a pas de rendez-vous
        data['no_rdv_message'] = "Vous n'avez pas de rendez-vous. Vous pouvez en prendre un maintenant."
        data['show_button'] = True  # Affiche le bouton pour créer un nouveau rendez-vous
    else:
        data['object_list'] = rdv  # Sinon, affiche la liste des rendez-vous existants

    return render(request, 'rdv_list.html', data)


@login_required
def rdv_delete(request, pk, template_name='rdv_confirm_delete.html'):
    """
    Permet de supprimer un rendez-vous. 
    Si l'utilisateur est un administrateur, il peut supprimer n'importe quel rendez-vous.
    Sinon, l'utilisateur ne peut supprimer que ses propres rendez-vous.
    Un message de confirmation est montré avant de supprimer le rendez-vous.
    """
    # Si l'utilisateur est un administrateur, récupère n'importe quel rendez-vous
    if request.user.is_superuser:
        rdv = get_object_or_404(Rdv, id=pk)
    else:
        # Si l'utilisateur est un patient, récupère uniquement ses propres rendez-vous
        rdv = get_object_or_404(Rdv, id=pk, id_patient=request.user)

    # Si la méthode de requête est POST, supprime le rendez-vous
    if request.method == 'POST':
        rdv.delete()
        return redirect('rdv_list')  # Redirection vers la liste des rendez-vous après la suppression

    # Rendu de la page de confirmation de suppression
    return render(request, template_name, {'object': rdv})


def forgot_password(request):
    """
    Vue permettant la gestion de la réinitialisation du mot de passe.
    Si l'utilisateur entre une adresse email valide associée à un compte, un email contenant
    un lien de réinitialisation du mot de passe sera envoyé.
    """

    if request.method == "POST":
        # Récupération de l'email soumis par l'utilisateur
        email = request.POST.get("email")

        # Recherche de l'utilisateur correspondant à cet email
        user = User.objects.filter(email=email).first()

        if user:
            # Génération d'un token unique pour la réinitialisation du mot de passe
            token = default_token_generator.make_token(user)

            # Encodage de l'identifiant de l'utilisateur
            uid = urlsafe_base64_encode(force_bytes(user.id))

            # Récupération du domaine actuel pour inclure dans l'URL de réinitialisation
            current_site = request.META["HTTP_HOST"]

            # Création du contexte à passer au gabarit d'email
            context = {
                "token": token,
                "uid": uid,
                "domaine": f"http://{current_site}",
            }

            # Rendu du contenu HTML de l'email à partir d'un gabarit
            html_text = render_to_string("email.html", context)

            # Configuration de l'email avec le sujet, le contenu, l'expéditeur et le destinataire
            msg = EmailMessage(
                "Récupération de mot de passe",
                html_text,
                "MedDoc+<bilelbentaher9@gmail.com>",  # Adresse email de l'expéditeur
                [user.email],  # Adresse email du destinataire
            )

            # Définir le type de contenu à HTML
            msg.content_subtype = "html"

            # Envoi de l'email
            msg.send()

            # Ajout d'un message flash pour informer l'utilisateur que l'email a été envoyé
            messages.success(request, "Veuillez vérifier votre boîte mail pour les instructions de réinitialisation.")
        else:
            # Si aucun utilisateur n'est trouvé avec cet email, afficher un message d'erreur
            messages.error(request, "Aucun utilisateur trouvé avec cet email.")

    # Rendu de la page "Mot de passe oublié"
    return render(request, "forgot_password.html", {})


def update_password(request, token, uid):
    """
    Vue permettant à un utilisateur de réinitialiser son mot de passe via un lien contenant
    un token de validation et un identifiant utilisateur encodé.
    """
    try:
        # Décodage de l'UID encodé en base64 pour récupérer l'identifiant utilisateur
        user_id = urlsafe_base64_decode(uid)
        decode_uid = codecs.decode(user_id, "utf-8")
        user = User.objects.get(id=decode_uid)
    except Exception:
        # Si l'utilisateur n'est pas trouvé ou si une erreur survient, renvoyer une réponse 403
        return HttpResponseForbidden(
            "Vous n'aviez pas la permission de modifier ce mot de passe. Utilisateur introuvable"
        )

    # Validation du token de réinitialisation
    check_token = default_token_generator.check_token(user, token)
    if not check_token:
        return HttpResponseForbidden(
            "Vous n'aviez pas la permission de modifier ce mot de passe. Votre Token est invalide ou a expiré"
        )

    # Initialisation des variables pour gérer les erreurs et les succès
    error = False
    success = False
    message = ""

    if request.method == "POST":
        # Récupération des mots de passe soumis par l'utilisateur
        password = request.POST.get("password")
        repassword = request.POST.get("repassword")

        if repassword == password:
            try:
                # Validation de la robustesse du mot de passe
                validate_password(password, user)

                # Mise à jour du mot de passe utilisateur
                user.set_password(password)
                user.save()

                success = True
                message = "Votre mot de passe a été modifié avec succès !"
            except ValidationError as e:
                # Si une erreur de validation survient, renvoyer le message d'erreur
                error = True
                message = str(e)
        else:
            # Si les mots de passe ne correspondent pas
            error = True
            message = "Les deux mots de passe ne correspondent pas."

    # Contexte à transmettre à la vue
    context = {
        "error": error,
        "success": success,
        "message": message
    }

    # Affichage de la page de réinitialisation avec les messages appropriés
    return render(request, "update_password.html", context)

from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_protect
from django.core.mail import EmailMessage

@csrf_protect
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Vérifier que tous les champs sont remplis
        if not name or not email or not subject or not message:
            messages.error(request, "*Tous les champs doivent être remplis.")
            return redirect('/#contact')  # Redirige l'utilisateur en cas d'erreur

        full_message = f"nom: {name}\nEmail: {email}\n\nMessage:\n{message}"

        send_mail(
            subject,
            full_message,
            f"{name}<bilelbentaher9@gmail.com>",  # Adresse email de l'expéditeur
            ['bilelbentaher9@gmail.com'],
           
        )

        messages.success(request, 'Merci pour votre message. Nous vous contacterons bientôt.')
        return redirect('/#contact')

    return render(request, 'home.html')

def generate_ordonnance_pdf(request, ordonnance_id):
    # Récupérer l'ordonnance et les données associées
    ordonnance = Ordonnance.objects.get(id_ordonnance=ordonnance_id)
    patient = ordonnance.id_patient
    medicament = ordonnance.medicament
    cabinet_adresse = "Adresse du Cabinet"
    doctor_name_fr = "Docteur Foulen BEN FALTEN\nMédecin Dentiste"
    doctor_name_ar = "دكتور فلان بن فلتان\nطبيب أسنان"

    # Récupérer le chemin absolu vers la police dans le dossier static
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')
    
    # Enregistrer la police arabe dans ReportLab
    try:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Amiri', font_path))  # Enregistrer la police
        else:
            raise FileNotFoundError(f"Font file not found at {font_path}")
    except Exception as e:
        print(f"Error loading font: {e}")
        return HttpResponse("Font file loading error", status=500)

    # Créer une réponse pour envoyer le PDF en tant que page imprimable
    response = HttpResponse(content_type='application/pdf')

    # Créer un objet canvas pour générer le PDF
    c = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Définir la police pour le texte en français (gras pour "Docteur" et "Médecin Dentiste")
    c.setFont("Helvetica-Bold", 14)

    # Haut de la page - Nom du médecin en français centré à gauche
    c.drawString(60, height - 20, "Docteur")  # "Docteur" en gras
    c.setFont("Helvetica-Bold", 14)  # Garder "Foulen BEN FALTEN" en gras
    c.drawString(30, height - 40, "Foulen BEN FALTEN")  # "Foulen BEN FALTEN" en gras
    c.setFont("Helvetica", 12)  # Revenir à la police normale
    c.drawString(50, height - 60, "Médecin (Spécialité)")  # "Médecin Dentiste" en texte normal

    # Définir la police pour le texte en arabe (Amiri)
    c.setFont("Amiri", 12)
    
    # Reshaper et Bidi pour gérer correctement l'arabe
    reshaped_text = arabic_reshaper.reshape("دكتور")  # Reshape le texte arabe
    bidi_text = get_display(reshaped_text)  # Applique le processus bidi pour afficher de droite à gauche

    # Nom arabe centré à droite
    c.drawString(width-75, height - 20, bidi_text)  # Affiche le texte arabe "دكتور" de droite à gauche
    c.setFont("Amiri", 12)  # Revenir à la police normale pour la suite
    reshaped_text2 = arabic_reshaper.reshape("فلان بن فلتان")  # Reshape le texte arabe
    bidi_text2 = get_display(reshaped_text2)  # Applique le processus bidi pour afficher de droite à gauche
    c.drawString(width - 90, height - 40, bidi_text2)  # Affiche "فلان بن فلتان"
    c.setFont("Amiri", 12)  # Toujours utiliser la police normale
    reshaped_text3 = arabic_reshaper.reshape("طبيب(التخصص)")  # Reshape "طبيب أسنان"
    bidi_text3 = get_display(reshaped_text3)  # Applique le processus bidi pour afficher de droite à gauche
    c.drawString(width - 105, height - 60, bidi_text3)  # Affiche "طبيب أسنان"

    # Ligne de séparation sous le nom du médecin
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(32, height - 80, width - 32, height - 80)

    # Contenu principal - Détails du patient et médicaments
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 100, "Ordonnance Médicale")  # Ajouter "Ordonnance Médicale" centré

    # Contenu principal - Détails du patient et médicaments
    c.setFont("Helvetica", 12)
    c.drawString(30, height - 120, f"Patient : {patient.first_name} {patient.last_name}")
    c.drawString(30, height - 140, f"Tunis le {ordonnance.date.strftime('%d/%m/%Y')}")
    
    # Séparer "Médicaments :" du texte des médicaments
    medicament_title = "Médicaments :"
    medicament_body = medicament  # Le reste des médicaments

    # Découper le texte des médicaments en lignes
    wrapped_medicament = textwrap.wrap(medicament_body, width=80)  # Ajustez width selon la largeur souhaitée

    # Position initiale pour afficher les lignes
    current_y = height - 160
    line_spacing = 15  # Espacement entre les lignes

    # Affichage du titre "Médicaments :" à la première position
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, current_y, medicament_title)
    current_y -= line_spacing  # Espacer pour la ligne suivante

    # Affichage des lignes de médicaments
    c.setFont("Helvetica", 12)
    for line in wrapped_medicament:
        c.drawString(30, current_y, line)
        current_y -= line_spacing  # Déplacer la position vers le bas pour la ligne suivante

    # Exemple d'adresses
    cabinet_adresse_fr = "123 Rue Exemple, Ville, Code Postal, Pays"  # Adresse en français
    cabinet_adresse_ar = "شارع المثال 123، المدينة، الرمز البريدي، البلد"  # Adresse en arabe

    # Bas de page - Adresse en français
    c.setFont("Helvetica", 12)
    c.drawString(30, 25, f"Adresse: {cabinet_adresse_fr}")

    # Bas de page - Adresse en arabe (alignée à droite)
    c.setFont("Amiri", 12)
    reshaped_address_ar = arabic_reshaper.reshape(f"عنوان:{cabinet_adresse_ar}")  # Reshape l'adresse en arabe
    bidi_address_ar = get_display(reshaped_address_ar)  # Applique le processus bidi pour afficher de droite à gauche
    c.drawRightString(width - 30, 25, bidi_address_ar)  # Affiche l'adresse arabe alignée à droite

    # Ajouter l'email à gauche
    email = "exemple@email.com"  # Remplacez par l'email réel
    c.setFont("Helvetica", 10)
    c.drawString(30, 10, f"Email : {email}")

    # Ajouter le numéro GSM à droite
    gsm = "+212 6 12 34 56 78"  # Remplacez par le numéro GSM réel
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 30, 10, f"GSM : {gsm}")

    # Ligne de séparation finale ajustée
    c.setStrokeColor(colors.black)
    c.line(30, 40, width - 30, 40)  # Ligne juste au-dessus de l'email et du GSM (ajustée plus près)

    # Sauvegarder le PDF
    c.showPage()
    c.save()

    return response


def generate_certificat_pdf(request, certificat_id):
    """
    Génère un fichier PDF pour un certificat médical, incluant les informations du patient, le contenu du certificat,
    ainsi que les informations du médecin et les adresses en français et en arabe.
    """

    # Récupérer le certificat
    certificat = get_object_or_404(Certificat, id_certificat=certificat_id)  # Recherche du certificat
    patient = certificat.id_patient  # Récupérer les informations du patient
    contenu = certificat.contenu  # Récupérer le contenu du certificat

    # Informations fixes
    doctor_name_fr = "Docteur Foulen BEN FALTEN\nMédecin (Spécialité)"
    doctor_name_ar = "دكتور فلان بن فلتان\nطبيب (التخصص)"
    cabinet_adresse_fr = "123 Rue Exemple, Ville, Code Postal, Pays"
    cabinet_adresse_ar = "شارع المثال 123، المدينة، الرمز البريدي، البلد"
    email = "exemple@email.com"
    gsm = "+212 6 12 34 56 78"

    # Charger la police arabe
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Amiri', font_path))
    else:
        return HttpResponse("Police arabe introuvable", status=500)

    # Créer la réponse PDF
    response = HttpResponse(content_type='application/pdf')
    c = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Haut de la page - Informations du médecin en français et arabe
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, height - 20, "Docteur")
    c.drawString(30, height - 40, "Foulen BEN FALTEN")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 60, "Médecin (Spécialité)")

    # Informations en arabe
    c.setFont("Amiri", 12)
    c.drawString(width - 75, height - 20, get_display(arabic_reshaper.reshape("دكتور")))
    c.drawString(width - 90, height - 40, get_display(arabic_reshaper.reshape("فلان بن فلتان")))
    c.drawString(width - 105, height - 60, get_display(arabic_reshaper.reshape("طبيب (التخصص)")))

    # Ligne de séparation sous le nom du médecin
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(32, height - 80, width - 32, height - 80)

    # Titre du certificat
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 100, "Certificat Médical")

    # Contenu du certificat
    c.setFont("Helvetica", 12)

    # Ajuster la largeur du wrap() pour qu'il soit plus large (par exemple, de 80 à 100)
    wrapped_content = textwrap.wrap(contenu, width=100)

    current_y = height - 120
    for line in wrapped_content:
        c.drawString(30, current_y, line)
        current_y -= 15  # Espacement entre les lignes

    # Bas de page - Adresse en français
    c.setFont("Helvetica", 12)
    c.drawString(30, 25, f"Adresse: {cabinet_adresse_fr}")

    # Bas de page - Adresse en arabe (alignée à droite)
    c.setFont("Amiri", 12)
    reshaped_address_ar = arabic_reshaper.reshape(f"عنوان:{cabinet_adresse_ar}")  # Reshape l'adresse en arabe
    bidi_address_ar = get_display(reshaped_address_ar)  # Applique le processus bidi pour afficher de droite à gauche
    c.drawRightString(width - 30, 25, bidi_address_ar)  # Affiche l'adresse arabe alignée à droite

    # Ajouter un espace pour la signature et la date
    current_y -= 40  # Ajustez la position pour l'espace avant la signature

    # Ajouter la signature du médecin
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(30, current_y, "Signature du Médecin")

    # Ajouter la date (en bas à gauche)
    c.setFont("Helvetica", 10)
    c.drawString(30, current_y - 20, f"Tunis le {certificat.date.strftime('%d/%m/%Y')}")  # Date du certificat

    # Ajouter l'email à gauche
    c.setFont("Helvetica", 10)
    c.drawString(30, 10, f"Email : {email}")

    # Ajouter le numéro GSM à droite
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 30, 10, f"GSM : {gsm}")

    # Ligne de séparation finale ajustée
    c.setStrokeColor(colors.black)
    c.line(30, 40, width - 30, 40)  # Ligne juste au-dessus de l'email et du GSM (ajustée plus près)

    # Sauvegarder le PDF
    c.showPage()
    c.save()

    return response









