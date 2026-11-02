from django.urls import path

from . import views


app_name = "racp"
urlpatterns = [
    path("", views.home, name="home"),
    path("matrix/", views.matrix, name="matrix"),
    path("pdf/", views.pdf_view, name="pdf"),
    path("pdf/download/", views.pdf_download, name="pdf_download"),
]
