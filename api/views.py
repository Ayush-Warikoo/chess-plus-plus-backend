from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User

# Create your views here.

@api_view(['GET'])
def get_routes(request):
    routes = [
        {'POST': '/api/v1/user/register/'},
        {'POST': '/api/v1/user/login/'},
        {'GET': '/api/v1/user/logout/'},
    ]
    return Response(routes)

@api_view(['POST'])
def user_register(request):
    data = request.data
    if User.objects.filter(username=data['username']).exists():
        return Response({'message': 'Username already exists'})
    User.objects.create_user(username=data['username'], password=data['password'])
    return Response({'message': 'User Registered'})

@api_view(['POST'])
def user_login(request):
    # if request.user.is_authenticated:
    #     return Response({'message': 'User is already logged in'})
    data = request.data
    # check if user exists
    if User.objects.filter(username=data['username']).exists():
        user = User.objects.get(username=data['username'])
        if user.check_password(data['password']):
            return Response({'message': 'User logged in'})
        else:
            return Response({'message': 'Incorrect password'})

@api_view(['GET'])
def user_logout(request):
    return Response({'message': 'User logged out'})
