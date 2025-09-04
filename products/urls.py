from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('update/<int:product_id>/', views.product_update, name='product_update'),
    path('delete/<int:product_id>/', views.product_delete, name='product_delete'),
]