from django.urls import path
from . import views

urlpatterns = [
     path('', views.home, name='home'),
     path('signup/', views.signup, name='signup'),
     path('login/', views.login_view, name='login'),
     path('logout/', views.logout_view, name='logout'),
     path('panel/', views.rdv_list, name='rdv_list'),
     path('rdv/new/', views.rdv_new, name='rdv_new'),
     path('rdv/delete/<int:pk>/', views.rdv_delete, name='rdv_delete'),
     path('ordonnance/pdf/<int:ordonnance_id>/', views.generate_ordonnance_pdf, name='generate_ordonnance_pdf'),
     path('certificat/pdf/<int:certificat_id>/', views.generate_certificat_pdf, name='generate_certificat_pdf'),
     path("forgot-password", views.forgot_password, name="forgot_password"),
     path("update-password/<str:token>/<str:uid>/",views.update_password, name="update_password"),
     path('contact/', views.contact_view, name='contact'),
     ]
