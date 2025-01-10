from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from django.core.exceptions import ValidationError
from pages.models import Rdv
import re


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Prénom"
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nom"
    )
    username = forms.CharField(
        max_length=150,
        help_text="Le nom d'utilisateur doit être au format : prénom-nom-dd-mm-année."
    )
    age = forms.IntegerField(
        required=True,
        label="Âge"
    )
    gender = forms.ChoiceField(
        required=True,
        choices=[('', 'Sélectionnez votre genre'), ('M', 'Homme'), ('F', 'Femme')],
        label="Genre"
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        label="Numéro de téléphone"
    )
    email = forms.EmailField(  
        max_length=50,
        required=True,
        label="Adresse e-mail"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'age', 'gender', 'phone', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        pattern = r'^[a-zA-Z]+-[a-zA-Z]+-\d{2}-\d{2}-\d{4}$'
        if not re.match(pattern, username):
            raise ValidationError(
                "Le nom d'utilisateur doit être au format : prénom-nom-dd-mm-année.",
                code='invalid'
            )
        return username


class PostForm(forms.ModelForm):
    # Définition de la classe Meta pour lier le formulaire au modèle Rdv et définir les champs à inclure
    class Meta:
        model = Rdv  # Le formulaire est basé sur le modèle 'Rdv'
        fields = ['date']  # Seul le champ 'date' est inclus dans ce formulaire

    def __init__(self, *args, **kwargs):
        # Initialisation du formulaire en appelant le constructeur parent pour garder le comportement standard
        super(PostForm, self).__init__(*args, **kwargs)
        
        # Applique un widget personnalisé au champ 'date' pour améliorer l'interface utilisateur
        self.fields['date'].widget = DateInput(attrs={
            'class': 'datepicker',  # Classe CSS pour appliquer un style spécifique au champ (par exemple, pour un calendrier)
            'type': 'date',  # Utilisation du type HTML5 'date' pour afficher un sélecteur de date natif dans le navigateur
            'placeholder': 'Choisir une date',  # Texte d'aide pour guider l'utilisateur sur ce qu'il doit saisir
        })


class RdvForm(forms.ModelForm):
    # Définition de la classe Meta pour lier le formulaire au modèle Rdv et spécifier les champs à inclure
    class Meta:
        model = Rdv  # Le formulaire est basé sur le modèle 'Rdv'
        fields = ['date', 'num_rdv']  # Inclure uniquement les champs 'date' et 'num_rdv' dans le formulaire


class LoginForm(forms.Form):
    # Définition du champ 'username' pour le nom d'utilisateur
    username = forms.CharField(
        max_length=150,  # Le nom d'utilisateur ne peut pas dépasser 150 caractères
        label='',  # Ne pas afficher de label (label vide)
        widget=forms.TextInput(attrs={
            'placeholder': "Nom d'utilisateur",  # Texte d'aide affiché dans le champ de saisie
            'style': 'width: 215px; color: black;',  # Style CSS appliqué au champ (largeur de 215px et couleur du texte noir)
        })
    )
    
    # Définition du champ 'password' pour le mot de passe
    password = forms.CharField(
        label='',  # Ne pas afficher de label (label vide)
        widget=forms.PasswordInput(attrs={
            'placeholder': "Mot de passe",  # Texte d'aide affiché dans le champ de saisie
            'style': 'width: 215px; color: black;',  # Style CSS appliqué au champ (largeur de 215px et couleur du texte noir)
        })
    )




