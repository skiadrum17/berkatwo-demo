from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('access-2b5e18r11k1a20t-admin/', admin.site.urls),
    path('', include('payments.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', lambda request: redirect('unauthorized_access')),
    path('accounts/', include('allauth.urls')),
]
