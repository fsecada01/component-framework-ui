from django.urls import path

from tests.integration.cotton_app import views

urlpatterns = [
    path("form-field/", views.form_field_view),
    path("modal/", views.modal_view),
    path("card/", views.card_view),
]
