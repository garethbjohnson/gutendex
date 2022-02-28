from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.contrib import admin
from rest_framework import routers

from books import views


router = routers.DefaultRouter()
router.register(r'books', views.BookViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^$', TemplateView.as_view(template_name='home.html')),
    re_path(r'^', include(router.urls)),
]
