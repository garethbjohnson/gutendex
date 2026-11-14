from django.urls import include, re_path
from django.views.generic import TemplateView

from rest_framework import routers

from books import views
from .middleware import require_app_secret


router = routers.DefaultRouter()
router.register(r'books', views.BookViewSet)

# Apply the decorator to every view inside router.urls
decorated_router_urls = [
    re_path(
        url.pattern.regex.pattern,
        require_app_secret(url.callback),
        url.default_args,
        name=url.name,
    )
    for url in router.urls
]

urlpatterns = [
    re_path(r'^$', require_app_secret(TemplateView.as_view(template_name='home.html'))),
    re_path(r'^', include(decorated_router_urls)),
]