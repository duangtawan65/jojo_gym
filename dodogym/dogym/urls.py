# urls.py
from django.urls import path
from . import views

urlpatterns = [

    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff/register/', views.register_staff, name='register_staff'),
  # ย้าย login ไปที่ /login/ แทน

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/delete/<str:user_type>/<str:user_id>/', views.delete_user, name='delete_user'),
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),

    path('api/member/<int:member_id>/', views.get_member_data, name='get_member_data'),
    path('member/edit/<int:member_id>/', views.edit_member, name='edit_member'),

    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/register_member/', views.register_member, name='register_member'),
    path('staff/add_subscription/', views.add_subscription, name='add_subscription'),
    path('staff/check_member_status/', views.check_member_status, name='check_member_status'),
    path('staff/check_in/', views.check_in_member, name='check_in_member'),

]