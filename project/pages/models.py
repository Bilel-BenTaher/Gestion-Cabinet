from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField
from datetime import timedelta, datetime, time

# Create your models here.

class Rdv(models.Model):
    id = models.AutoField(primary_key=True)
    id_patient = models.ForeignKey(User, related_name="rdv_patient", on_delete=models.CASCADE, null=True, blank=True)
    fiche = models.ForeignKey('FichePatient', related_name="cons_fact", on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()  # Date du rendez-vous
    time = models.TimeField(null=True, blank=True)  # Heure calculée du rendez-vous
    num_rdv = models.IntegerField(default=1)  # Numéro du rendez-vous dans la journée (1, 2, 3, etc.)

    def calculate_time(self):
        """
        Cette méthode calcule l'heure du prochain rendez-vous en fonction de l'heure actuelle et du dernier rendez-vous
        uniquement si le rendez-vous est pour aujourd'hui.
        """

        start_time = time(9, 0)  # Le cabinet ouvre à 9h00
        end_time = time(17, 0)  # Le cabinet ferme à 17h00
        saturday_end_time = time(14, 0)  # Le cabinet ferme à 14h00 le samedi
        consultation_duration = timedelta(minutes=35)  # Durée d'une consultation (35 minutes)

        now = datetime.now()  # Heure actuelle
        current_time = now.time()

        # Vérifier si la date choisie est un samedi (index 5 pour samedi)
        if self.date.weekday() == 5:  # 5 correspond à samedi
            end_time = saturday_end_time  # On ajuste l'heure de fin pour le samedi

        # Vérifier si la date choisie est aujourd'hui
        if self.date == now.date():
            # Récupérer tous les rendez-vous existants pour cette date
            rdvs_on_date = Rdv.objects.filter(date=self.date).order_by('time')

            # Si aucun rendez-vous n'existe pour cette journée
            if not rdvs_on_date:
                # Si l'heure actuelle est avant 9h, on retourne 9h
                if current_time < start_time:
                    return start_time
                # Sinon, on retourne l'heure actuelle si c'est dans les heures d'ouverture
                elif start_time <= current_time < end_time:
                    return current_time
                else:
                    raise ValidationError("Le cabinet est fermé. Veuillez choisir une autre date.")

            # Si des rendez-vous existent, récupérer le dernier rendez-vous
            last_rdv = rdvs_on_date.last()
            last_rdv_time = datetime.combine(now, last_rdv.time)

            # Si l'heure actuelle est après le dernier rendez-vous
            if current_time > last_rdv.time:
                # Si l'heure actuelle est avant l'heure de fermeture, on fixe l'heure du rendez-vous à l'heure actuelle
                if current_time < end_time:
                    return current_time
                else:
                    raise ValidationError("Le cabinet est fermé. Veuillez choisir une autre date.")
            
            # Sinon, fixer immédiatement après le dernier rendez-vous
            next_rdv_time = last_rdv_time + consultation_duration
            if next_rdv_time.time() >= end_time:
                raise ValidationError("Le cabinet est fermé. Veuillez choisir une autre date.")
            
            return next_rdv_time.time()

        else:
            # Si la date n'est pas aujourd'hui, appliquer la logique par défaut
            start_morning = timedelta(hours=9)  # Heure de début de la journée (9h)
            consultation_duration = timedelta(minutes=35)  # Durée d'une consultation

            # Récupérer les rendez-vous existants pour cette date
            rdvs_on_date = Rdv.objects.filter(date=self.date).order_by('time')

            if not rdvs_on_date:  # Aucun rendez-vous pour cette journée
                return (datetime.min + start_morning).time()

            # Si des rendez-vous existent, récupérer le dernier rendez-vous
            last_rdv = rdvs_on_date.last()
            last_rdv_time = datetime.combine(datetime.today(), last_rdv.time)
            next_rdv_time = last_rdv_time + consultation_duration

            return next_rdv_time.time()

    def save(self, *args, **kwargs):
        """
        Cette méthode est appelée pour enregistrer l'objet 'Rdv'. Elle inclut des validations et des 
        assignations automatiques avant de sauvegarder dans la base de données.
        """

        # Vérifier si le jour du rendez-vous est un dimanche (index 6 pour dimanche)
        if self.date.weekday() == 6:  # 6 correspond à dimanche (0 = lundi, 6 = dimanche)
            raise ValidationError("Le cabinet est fermé. Veuillez choisir une autre date.")

        # Si l'heure du rendez-vous n'est pas spécifiée, la calculer automatiquement
        if not self.time:
            self.time = self.calculate_time()  # Calculer l'heure automatiquement
    
        # Assignation automatique de la fiche patient basée sur l'id_patient
        if self.id_patient and not self.fiche:
            try:
                self.fiche = FichePatient.objects.get(id_patient=self.id_patient)
            except FichePatient.DoesNotExist:
                pass  # Si la fiche n'existe pas, on garde id_fiche à None (ou vous pouvez gérer autrement)

        super().save(*args, **kwargs)

    def __str__(self):
        # Retourne une représentation lisible de l'objet
        return f"Réf: {self.id_patient}"

class FichePatient(models.Model):
    id_fiche = models.AutoField(primary_key=True)  # Identifiant unique de la fiche (auto-incrémenté)
    id_patient = models.ForeignKey(User, related_name="fich_patient", on_delete=models.CASCADE)  # Lien vers l'utilisateur (patient)
    nom = models.CharField(max_length=254)  # Nom du patient
    prenom = models.CharField(max_length=254)  # Prénom du patient
    age = models.IntegerField()  # Âge du patient
    sexe = models.CharField(max_length=254)  # Sexe du patient
    tel = PhoneNumberField(blank=True)  # Numéro de téléphone du patient (optionnel)
    motif_consultation = models.CharField(max_length=254)  # Motif de la consultation
    valide = models.BooleanField(default=False)  # Champ pour valider ou non la fiche

    def __str__(self):
        """
        Cette méthode retourne une représentation lisible de l'objet 'FichePatient'.
        Elle affiche le prénom, le nom et l'âge du patient.
        """
        return f"{self.prenom} {self.nom} {self.age} ans "

# Signal pour créer une consultation automatiquement après la validation d'une fiche
@receiver(post_save, sender=FichePatient)
def create_consultation(sender, instance, created, **kwargs):
    """
    Cette fonction est déclenchée après la sauvegarde d'une instance de FichePatient.
    Elle crée automatiquement une consultation si la fiche a été validée.
    """
    if instance.valide:  # Vérifier si la fiche est validée
        # Créer une consultation seulement si elle n'existe pas déjà
        if not hasattr(instance, 'consultation'):  # Vérifie si aucune consultation n'est déjà associée à la fiche
            Consultation.objects.create(
                id_patient=instance.id_patient,  # Lier la consultation au même patient
                # Remplir d'autres champs nécessaires comme le contenu de la consultation ou le traitement
                Observation="Consultation ",  # Remarque initiale pour la consultation
                date_consultation=now().date(),  # Utiliser la date actuelle pour la consultation
            )
            # Rendre la fiche invalide après la création de la consultation
            instance.valide = False  # Réinitialiser la validation pour empêcher la création de consultations multiples
            instance.save()  # Sauvegarder la fiche avec son état modifié


class Consultation(models.Model):
    id_consultation = models.AutoField(primary_key=True)  # Identifiant unique de la consultation (auto-incrémenté)
    id_patient = models.ForeignKey(User, related_name="cons_patient", on_delete=models.CASCADE)  # Lien vers l'utilisateur (patient)
    patient = models.ForeignKey('FichePatient', related_name="consultations", on_delete=models.CASCADE, null=True, blank=True)  # Lien vers la fiche du patient (optionnel au départ)
    Observation = models.TextField(max_length=254)  # Observations de la consultation (max 254 caractères)
    Ordonnance = models.ForeignKey('Ordonnance', related_name="cons_ord", on_delete=models.CASCADE, null=True, blank=True)  # Lien vers une ordonnance (optionnel au départ)
    facture = models.ForeignKey('Facture', related_name="cons_fact", on_delete=models.CASCADE, null=True, blank=True)  # Lien vers la facture (optionnel au départ)
    date_consultation = models.DateField()  # Date de la consultation
    valide = models.BooleanField(default=False)  # Champ pour valider ou non la consultation

    def __str__(self):
        """
        Cette méthode retourne une représentation lisible de l'objet 'Consultation'.
        Elle affiche le nom d'utilisateur du patient associé à la consultation.
        """
        return f"Réf: {self.id_patient.username}"

    def save(self, *args, **kwargs):
        """
        Cette méthode est appelée avant de sauvegarder la consultation. Elle effectue plusieurs actions :
        1. Assigner automatiquement la fiche patient si elle n'est pas déjà définie.
        2. Vérifier si une facture existe pour le patient. Si elle n'existe pas, elle en crée une.
        3. Vérifier si une ordonnance existe pour le patient. Si elle n'existe pas, elle en crée une.
        """
        # Assigner automatiquement la fiche_patient si elle n'est pas définie
        if not self.patient:
            try:
                self.patient = FichePatient.objects.get(id_patient=self.id_patient)  # Récupérer la fiche patient en fonction de l'id_patient
            except FichePatient.DoesNotExist:
                pass  # Gérer l'absence de FichePatient si nécessaire, peut-être en affichant une erreur

        # Vérifier si une facture existe pour le patient, sinon en créer une
        if not self.facture:
            try:
                self.facture = Facture.objects.get(id_patient=self.id_patient)  # Récupérer la facture associée au patient
            except Facture.DoesNotExist:
                # Créer une nouvelle facture si aucune facture existante pour ce patient
                self.facture = Facture.objects.create(id_patient=self.id_patient, prix=0)  # Exemple : montant initial à 0

        # Vérifier si une ordonnance existe pour le patient, sinon en créer une
        if not self.Ordonnance:
            try:
                self.Ordonnance = Ordonnance.objects.get(id_patient=self.id_patient)  # Récupérer l'ordonnance existante pour le patient
            except Ordonnance.DoesNotExist:
                # Créer une ordonnance si aucune ordonnance existante pour ce patient
                self.Ordonnance = Ordonnance.objects.create(
                    id_patient=self.id_patient,  # Lier l'ordonnance au patient
                    date=now().date(),  # Utiliser la date actuelle pour l'ordonnance
                    medicament="Aucun Ordonnance prescrit"  # Valeur par défaut si aucun médicament n'est prescrit
                )

        super().save(*args, **kwargs)  # Appeler la méthode save() du parent pour sauvegarder l'objet


class Facture(models.Model):
    # Identifiant unique de la facture (auto-incrémenté)
    id_facture = models.AutoField(primary_key=True)  
    
    # Lien vers l'utilisateur (patient) associé à la facture. La suppression de l'utilisateur entraîne la suppression de la facture.
    id_patient = models.ForeignKey(User, related_name="factures", on_delete=models.CASCADE, null=True)  
    
    # Le prix de la facture (sous forme de nombre à virgule flottante)
    prix = models.FloatField()  
    
    def __str__(self):
        """
        Cette méthode retourne une représentation lisible de l'objet 'Facture'.
        Elle affiche le nom d'utilisateur du patient associé à la facture.
        """
        return f"Réf: {self.id_patient.username}"  # Affiche le nom d'utilisateur du patient associé à la facture

     

class Ordonnance(models.Model):
    # Identifiant unique de l'ordonnance (auto-incrémenté)
    id_ordonnance = models.AutoField(primary_key=True)  
    
    # Lien vers l'utilisateur (patient) associé à l'ordonnance. La suppression de l'utilisateur entraîne la suppression de l'ordonnance.
    id_patient = models.ForeignKey(User, related_name="Ordonnance", on_delete=models.CASCADE, null=True)  
    
    # Date et heure de la prescription de l'ordonnance
    date = models.DateTimeField()  
    
    # Description des médicaments prescrits dans l'ordonnance
    medicament = models.TextField()  
    
    def __str__(self):
        """
        Cette méthode retourne une représentation lisible de l'objet 'Ordonnance'.
        Elle affiche le nom d'utilisateur du patient associé à l'ordonnance.
        """
        return f"Réf: {self.id_patient.username}"  # Affiche le nom d'utilisateur du patient associé à l'ordonnance


class Certificat(models.Model):
    # Identifiant unique du certificat (auto-incrémenté)
    id_certificat = models.AutoField(primary_key=True)  
    
    # Lien vers l'utilisateur (patient) associé au certificat. La suppression de l'utilisateur entraîne la suppression du certificat.
    id_patient = models.ForeignKey(User, related_name="certificat", on_delete=models.CASCADE, null=True)  
    
    # Date de création du certificat
    date = models.DateField()  
    
    # Contenu du certificat, généralement des informations médicales ou administratives concernant le patient
    contenu = models.TextField()  
    
    def __str__(self):
        """
        Cette méthode retourne une représentation lisible de l'objet 'Certificat'.
        Elle affiche le nom d'utilisateur du patient associé au certificat.
        Si le patient n'est pas défini, elle affiche "Inconnu".
        """
        patient_name = self.id_patient.username if self.id_patient else "Inconnu"  # Récupère le nom d'utilisateur du patient, ou "Inconnu" si le patient n'est pas défini
        return f"Certificat du Patient: {patient_name}"  # Affiche "Certificat du Patient" suivi du nom du patient


