from django.urls import path
from . import views

urlpatterns = [
	path('', views.get_routes, name="get-routes"),
	path('user/register/', views.user_register, name="user-register"),
    path('user/login/', views.user_login, name="user-login"),
    path('user/logout/', views.user_logout, name="user-logout"),
]
