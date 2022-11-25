from django.contrib.auth.views import LogoutView, LoginView, PasswordResetView
from django.urls import path
from . import views

app_name = 'users'

path_name = {
    'login': 'users/login.html',
    'logout': 'users/logged_out.html',
    'passreset': 'users/password_reset_form.html'
}

urlpatterns = [
    path('logout/', LogoutView.as_view(template_name=path_name.get('logout')),
         name='logout'),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('login/', LoginView.as_view(template_name=path_name.get('login')),
         name='login'),
    path(
        "password_reset/",
        PasswordResetView.as_view(template_name=path_name.get('passreset')),
        name="password_reset_form"),
]
