from django.urls import path
from .views import RegisterView, LoginTokenObtainPairView, LogoutView, ProfileView, RefreshTokenView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('refresh-token/', RefreshTokenView.as_view(), name='token_refresh'),
]
