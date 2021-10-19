from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from warrant.views import warrant_market_closed_ViewSet

router = DefaultRouter()
router.register(r'warrant', warrant_market_closed_ViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')),
    path('', include('warrant.urls')),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('react/', TemplateView.as_view(template_name='index.html'))
]
