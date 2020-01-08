from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from apiv1 import views

#app_name = 'apiv1'

urlpatterns = [
    #path('get-verification-code/', views.get_verification_code, name='get-verification-code'),
    path('register/', views.register, name='register'),
    path('verify-account/', views.verify_account, name='verify-account'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile-change/', views.profile_change, name='profile-change'),
    path('password-change/', views.password_change, name='password-change'),
    path('password-reset/', views.password_reset, name='password-reset'),
    path('init-app/', views.init_app, name='init-app'),
    path('devices/', views.device_list, name='device-list'),
    path('sync-cloud/', views.sync_cloud, name='sync-cloud'),

    path('users/', views.user_list, name='user-list'),
    path('users/<uuid:pk>/', views.user_detail, name='user-detail'),

    path('', views.dummy, name='dummy'),
]

# add format suffix like /snippets.json
urlpatterns = format_suffix_patterns(urlpatterns)
