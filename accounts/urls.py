from django.urls import path
from .views import EmailLoginView, GoogleLoginView, RegisterView, LogoutView, UserListView, UserDetailView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", EmailLoginView.as_view()),
    path("login/google/", GoogleLoginView.as_view()),
    path("register/", RegisterView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("users/", UserListView.as_view()),
    path("users/<uuid:pk>/", UserDetailView.as_view()),
]
