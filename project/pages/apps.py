from django.apps import AppConfig

# Configuration de l'application 'pages' dans le projet Django
class PagesConfig(AppConfig):
    # Définir le type de champ par défaut pour les identifiants d'objet dans les modèles
    # 'BigAutoField' est un champ d'ID auto-incrémenté de type entier très grand
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Le nom de l'application (doit correspondre au nom du dossier de l'application dans votre projet)
    name = 'pages'

    # Le nom affiché de l'application dans l'interface d'administration de Django
    # Ce nom peut être personnalisé pour rendre l'application plus lisible dans l'admin
    verbose_name = "Gestion Médicale"


