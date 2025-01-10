# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db.models import Q
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.db.models import Func
from pages.models import FichePatient,  Rdv, Consultation, Facture, Ordonnance, Certificat
from .forms import SignUpForm  

class AlphabetFilter(admin.SimpleListFilter):
    # Définir le titre qui sera affiché dans le filtre de l'interface d'administration
    title = 'Filtrer par première lettre'
    # Nom du paramètre qui sera utilisé dans l'URL pour indiquer le filtre
    parameter_name = 'alphabet'

    def lookups(self, request, model_admin):
        # Générer les lettres de l'alphabet pour le filtre
        # Ici, on retourne une liste de tuples où chaque tuple est une lettre de l'alphabet
        # et cette lettre sera utilisée pour filtrer les résultats
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return [(letter, letter) for letter in alphabet]

    def queryset(self, request, queryset):
        # Filtrer les résultats par la première lettre du nom d'utilisateur (id_patient)
        # ou du prénom de la fiche (FichePatient)
        letter = self.value()  # Récupérer la valeur de la lettre sélectionnée dans le filtre
        if letter:
            # Si une lettre est sélectionnée, on filtre les utilisateurs qui commencent par cette lettre
            return queryset.filter(
                Q(id_patient__username__istartswith=letter) |  # Filtrer par nom d'utilisateur (id_patient)
                Q(id_patient__first_name__istartswith=letter)  # Filtrer par prénom dans FichePatient
            )
        return queryset  # Si aucune lettre n'est sélectionnée, retourner le queryset non modifié



# Filtre personnalisé pour afficher les rendez-vous par date
class DateRdvFilter(SimpleListFilter):
    # Définition du titre du filtre qui apparaîtra dans l'interface d'administration
    title = 'Date de rendez-vous'
    # Nom du paramètre dans l'URL qui indique la sélection du filtre
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        # Cette méthode définit les options disponibles dans le filtre dans l'interface d'administration
        # Ici, on propose deux options : 'Aujourd'hui' et 'Demain'
        return [
            ('aujourdhui', 'Aujourd\'hui'),  # Option pour filtrer les rendez-vous du jour
            ('demain', 'Demain'),  # Option pour filtrer les rendez-vous du lendemain
        ]

    def queryset(self, request, queryset):
        # Importation des modules nécessaires pour travailler avec les dates
        from datetime import date, timedelta

        # Vérification de la valeur sélectionnée dans le filtre
        if self.value() == 'aujourdhui':
            # Si la valeur sélectionnée est 'aujourdhui', on filtre les rendez-vous pour la date actuelle
            return queryset.filter(date=date.today())
        elif self.value() == 'demain':
            # Si la valeur sélectionnée est 'demain', on filtre les rendez-vous pour la date du lendemain
            return queryset.filter(date=date.today() + timedelta(days=1))
        return queryset  # Si aucune valeur n'est sélectionnée, on retourne le queryset non filtré



class RdvAdmin(admin.ModelAdmin):
    # Définition des champs à afficher dans la liste des rendez-vous dans l'interface d'administration
    list_display = ('patient_full_name', 'date', 'time', 'num_rdv')
    
    # Définition des champs sur lesquels il est possible de faire une recherche
    search_fields = ['id_patient__first_name', 'id_patient__last_name']
    
    # Définition de l'ordre de tri par défaut des rendez-vous (par date puis numéro de rendez-vous)
    ordering = ['date', 'num_rdv']  # Ordre de tri par défaut
    
    # Définition des filtres disponibles dans l'interface d'administration
    # Ajout du filtre de date standard et du filtre personnalisé pour les rendez-vous
    list_filter = ['date', DateRdvFilter]  # Ajout du filtre personnalisé pour la date

    def patient_full_name(self, obj):
        """
        Cette méthode permet d'afficher le nom et prénom complet du patient dans la colonne 'Nom et Prénom'
        de la liste des rendez-vous. Si aucun patient n'est lié, retourne 'Patient non défini'.
        """
        if obj.id_patient:  # Vérifie si id_patient est défini
            return f"{obj.id_patient.first_name} {obj.id_patient.last_name}"  # Retourne le nom complet du patient
        return "Patient non défini"  # Si aucun patient n'est défini, retourne une valeur par défaut
    
    # Définition de la description de la colonne pour l'affichage dans l'interface d'administration
    patient_full_name.short_description = "Nom et Prénom"

    def get_queryset(self, request):
        """
        Cette méthode permet d'afficher les rendez-vous en fonction de la date choisie, tout en maintenant un tri
        par date et par numéro de rendez-vous. Si aucun filtre de date n'est appliqué, elle applique un tri
        par défaut par date et numéro de rendez-vous.
        """
        qs = super().get_queryset(request)  # Récupère le queryset de base
        # Applique le tri par défaut si aucun filtre spécifique n'est appliqué
        if not request.GET.get('date'):  # Si aucun filtre 'date' n'est appliqué
            qs = qs.order_by('date', 'num_rdv')  # Assure que le tri par défaut est appliqué
        return qs  # Retourne le queryset filtré et trié

    
class FactureConsultation(admin.ModelAdmin):
    # Définir les champs à afficher dans la vue liste de l'interface d'administration
    # Ici, on affiche le nom et prénom du patient ainsi que le prix de la facture
    list_display = ('patient_full_name', 'prix')
    
    # Définir les champs sur lesquels il est possible de rechercher
    # Permet de chercher par prénom ou nom de famille du patient
    search_fields = ['id_patient__first_name', 'id_patient__last_name']

    def patient_full_name(self, obj):
        """
        Cette méthode permet de générer le nom et prénom complet du patient à partir de
        l'objet de la facture. Elle combine le prénom et le nom de famille du patient.
        """
        return f"{obj.id_patient.first_name} {obj.id_patient.last_name}"  # Retourne le nom complet du patient

    # Définir la description de la colonne dans l'interface d'administration
    patient_full_name.short_description = "Nom et Prénom"


    
# Personnalisation de l'administration pour le modèle Consultation
class ConsultationAdmin(admin.ModelAdmin):
    # Définir les champs à afficher dans la vue liste de l'interface d'administration
    list_display = ('patient_full_name', 'date_consultation', 'valide')  # Affichage du nom complet du patient, de la date de consultation et du statut de validation
    
    # Ajouter des filtres dans l'interface d'administration pour trier les consultations
    list_filter = ('valide', 'date_consultation')  # Permet de filtrer par statut de validation et par date de consultation

    # Définir les champs sur lesquels il est possible de rechercher dans l'interface d'administration
    search_fields = ['id_patient__first_name', 'id_patient__last_name']  # Recherche possible par prénom et nom de famille du patient

    # Exclure le champ 'id_patient' des champs affichés dans le formulaire d'administration
    exclude = ('id_patient',)  # Le champ 'id_patient' ne sera pas affiché lors de la modification de la consultation

    def patient_full_name(self, obj):
        """
        Cette méthode permet de générer le nom et prénom complet du patient à partir de l'objet Consultation.
        Elle combine le prénom et le nom de famille du patient.
        """
        return f"{obj.id_patient.first_name} {obj.id_patient.last_name}"  # Retourne le nom complet du patient

    # Définir la description de la colonne 'Nom et Prénom' dans l'interface d'administration
    patient_full_name.short_description = "Nom et Prénom"

    def get_queryset(self, request):
        """
        Modifie la liste des objets affichés dans l'interface d'administration pour n'afficher que les
        consultations non validées par défaut, tout en respectant l'ordre de création des consultations.
        """
        qs = super().get_queryset(request)
        # Filtrage des consultations non validées, triées par date de consultation et id pour maintenir l'ordre de création
        return qs.filter(valide=False).order_by('date_consultation', 'id_consultation')  # Tri par date de consultation et id

    # Définir les actions personnalisées que l'utilisateur peut appliquer aux consultations sélectionnées
    actions = ['valider_consultations', 'invalider_consultations']

    @admin.action(description='Valider les consultations sélectionnées')
    def valider_consultations(self, request, queryset):
        """
        Cette action permet de valider les consultations sélectionnées par l'administrateur.
        Elle met à jour le champ 'valide' des consultations sélectionnées à True.
        """
        queryset.update(valide=True)

    @admin.action(description='Invalider les consultations sélectionnées')
    def invalider_consultations(self, request, queryset):
        """
        Cette action permet d'invalider les consultations sélectionnées par l'administrateur.
        Elle met à jour le champ 'valide' des consultations sélectionnées à False.
        """
        queryset.update(valide=False)



# Personnalisation de l'administration pour le modèle Ordonnance
class OrdonnanceAdmin(admin.ModelAdmin):
    # Définir les champs à afficher dans la vue liste de l'interface d'administration
    list_display = ('patient_full_name', 'date', 'print_button')  # Affichage du nom complet du patient, de la date et d'un bouton pour imprimer l'ordonnance
    
    # Définir les champs sur lesquels il est possible de rechercher dans l'interface d'administration
    search_fields = ['id_patient__first_name', 'id_patient__last_name']  # Recherche possible par prénom et nom de famille du patient associé

    def patient_full_name(self, obj):
        """
        Cette méthode génère le nom et prénom complet du patient à partir de l'objet Ordonnance.
        Elle combine le prénom et le nom de famille du patient.
        """
        return f"{obj.id_patient.first_name} {obj.id_patient.last_name}"  # Retourne le nom complet du patient

    # Définir la description de la colonne 'Nom et Prénom' dans l'interface d'administration
    patient_full_name.short_description = "Nom et Prénom"

    def print_button(self, obj):
        """
        Cette méthode génère un bouton "Imprimer" pour chaque ordonnance.
        Ce bouton redirige vers une page permettant d'imprimer l'ordonnance sous forme de PDF.
        """
        # Utilisation de format_html pour générer un lien avec un bouton pour imprimer l'ordonnance au format PDF
        return format_html(
            '<a class="button" href="/ordonnance/pdf/{}/" target="_blank">Imprimer </a>',
            obj.id_ordonnance  # Ajoute l'ID de l'ordonnance dans l'URL pour générer le PDF
        )

    # Définir la description de la colonne 'Imprimer' dans l'interface d'administration
    print_button.short_description = "Imprimer"
    
    # Permet l'affichage des balises HTML dans le bouton
    print_button.allow_tags = True


# Personnalisation de l'administration pour le modèle Certificat
class CertificatAdmin(admin.ModelAdmin):
    # Définir les champs à afficher dans la vue liste de l'interface d'administration
    list_display = ('patient_full_name', 'date', 'print_button')  # Affichage du nom complet du patient, de la date et d'un bouton pour imprimer le certificat

    # Définir les champs sur lesquels il est possible de rechercher dans l'interface d'administration
    search_fields = ['id_patient__first_name', 'id_patient__last_name']  # Recherche possible par prénom et nom de famille du patient associé

    # Exclure le champ 'id_patient' de l'affichage dans le formulaire d'administration
    exclude = ('id_patient',)

    def patient_full_name(self, obj):
        """
        Cette méthode génère le nom et prénom complet du patient à partir de l'objet Certificat.
        Elle combine le prénom et le nom de famille du patient ou affiche 'Inconnu' si l'id_patient est vide.
        """
        # Si 'id_patient' existe, afficher le nom complet du patient, sinon afficher 'Inconnu'
        return f"{obj.id_patient.first_name} {obj.id_patient.last_name}" if obj.id_patient else "Inconnu"

    # Définir la description de la colonne 'Nom et Prénom' dans l'interface d'administration
    patient_full_name.short_description = "Nom et Prénom"

    def print_button(self, obj):
        """
        Cette méthode génère un bouton "Imprimer" pour chaque certificat.
        Ce bouton redirige vers une page permettant d'imprimer le certificat sous forme de PDF.
        """
        # Utilisation de format_html pour générer un lien avec un bouton pour imprimer le certificat au format PDF
        return format_html(
            '<a class="button" href="/certificat/pdf/{}/" target="_blank">Imprimer</a>',
            obj.id_certificat  # Ajoute l'ID du certificat dans l'URL pour générer le PDF
        )

    # Définir la description de la colonne 'Imprimer' dans l'interface d'administration
    print_button.short_description = "Imprimer"



# Classe personnalisée pour appliquer une fonction SQL LOWER pour ignorer la casse dans les requêtes de tri
class Lower(Func):
    """
    Cette classe est utilisée pour forcer le tri des champs de la base de données sans tenir compte de la casse des caractères.
    Elle permet de s'assurer que le tri est insensible à la casse pour les colonnes sur lesquelles elle est appliquée.
    """
    function = 'LOWER'  # La fonction SQL 'LOWER' est utilisée pour convertir les caractères en minuscules lors du tri.

# Personnalisation de l'administration pour le modèle FichePatient
class FicheAdmin(admin.ModelAdmin):
    # Définir les champs à afficher dans la vue liste de l'interface d'administration
    list_display = ['id_patient']  # Afficher uniquement l'ID du patient dans la liste

    # Définir les champs sur lesquels il est possible de rechercher dans l'interface d'administration
    search_fields = ['nom', 'prenom', 'id_patient__username']  # Recherche par nom, prénom ou nom d'utilisateur du patient

    # Appliquer un tri personnalisé insensible à la casse sur le prénom des patients
    ordering = [Lower('prenom')]  # Le champ 'prenom' sera trié en utilisant la fonction SQL LOWER pour ignorer la casse

    # Ajouter un filtre personnalisé pour trier par la première lettre du nom du patient
    list_filter = [AlphabetFilter]  # Filtrage par première lettre du nom d'utilisateur (id_patient) ou du prénom de la fiche



# Personnalisation de l'interface d'administration pour le modèle User
class CustomUserAdmin(UserAdmin):
    # Spécifie le formulaire personnalisé à utiliser lors de l'ajout d'un utilisateur
    add_form = SignUpForm  # Utilise le formulaire SignUpForm pour l'ajout d'un utilisateur

    # Définit les champs à afficher dans le formulaire d'ajout d'un utilisateur dans l'interface d'administration
    add_fieldsets = (
        (None, {
            'classes': ('wide',),  # Applique un style large au formulaire
            'fields': ('username', 'first_name', 'last_name', 'email', 'age', 'gender', 'phone', 'password1', 'password2'),  # Champs du formulaire
        }),
    )

    # Surcharge de la méthode save_model pour effectuer des actions supplémentaires lors de la sauvegarde de l'utilisateur
    def save_model(self, request, obj, form, change):
        # Sauvegarde de l'utilisateur via la méthode parent pour enregistrer l'utilisateur
        super().save_model(request, obj, form, change)

        # Si c'est un nouvel utilisateur (pas une modification d'utilisateur existant)
        if not change:
            # Crée une fiche patient associée à l'utilisateur nouvellement créé
            FichePatient.objects.create(
                id_patient=obj,  # L'utilisateur créé est lié à la fiche patient
                nom=obj.last_name,  # Le nom du patient est récupéré du champ 'last_name' de l'utilisateur
                prenom=obj.first_name,  # Le prénom du patient est récupéré du champ 'first_name' de l'utilisateur
                age=form.cleaned_data['age'],  # L'âge du patient est récupéré depuis le formulaire
                sexe=form.cleaned_data['gender'],  # Le sexe est récupéré depuis le formulaire
                tel=form.cleaned_data['phone'],  # Le numéro de téléphone est récupéré depuis le formulaire
                motif_consultation='',  # Motif de consultation est initialisé avec une chaîne vide
            )


# Désenregistrez le modèle User par défaut
admin.site.unregister(User)

# Enregistrement des modèles dans l'administration

admin.site.register(User, CustomUserAdmin)
admin.site.register(FichePatient,FicheAdmin)
admin.site.register(Rdv, RdvAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Facture, FactureConsultation)
admin.site.register(Ordonnance, OrdonnanceAdmin)
admin.site.register(Certificat, CertificatAdmin)

