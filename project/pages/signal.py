from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FichePatient, Consultation
from django.utils.timezone import now

# Récepteur de signal qui se déclenche après la sauvegarde d'un objet FichePatient
@receiver(post_save, sender=FichePatient)
def create_consultation(sender, instance, created, **kwargs):
    # Vérifie si la fiche patient a été validée et si l'enregistrement est nouveau
    if instance.valide and created:
        print("FichePatient validée, création d'une consultation.")  # Message de débogage pour vérifier la création de la consultation
        
        # Créer une consultation pour chaque patient dont la fiche a été validée
        # Cela associe le patient à une nouvelle consultation avec un contenu et un traitement par défaut
        Consultation.objects.create(
            id_patient=instance.id_patient,  # Lier la consultation au patient de la fiche
            id_facture=None,  # Optionnel: vous pouvez ajouter une logique pour associer une facture si nécessaire
            contenue="Consultation générée automatiquement",  # Contenu par défaut de la consultation
            traitement="Aucun traitement spécifié",  # Traitement par défaut, peut être mis à jour selon le cas
            date_consultation=now().date()  # Utilisation de la date actuelle pour la consultation
        )

