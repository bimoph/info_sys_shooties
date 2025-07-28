from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('stock-entries/', views.stockentry_list, name='stockentry_list'),


    # ingredient URLs
    # path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/add/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/edit/', views.ingredient_update, name='ingredient_update'),
    path('ingredients/<int:pk>/delete/', views.ingredient_delete, name='ingredient_delete'),

    # # Smoothie Menu URLs
    path('smoothies/', views.smoothie_menu_list, name='smoothie_menu_list'),
    # path('smoothies/add/', views.smoothie_menu_create, name='smoothie_menu_create'),
    # path('smoothies/<int:pk>/edit/', views.smoothie_menu_update, name='smoothie_menu_update'),
    path('smoothies/<int:pk>/delete/', views.smoothie_menu_delete, name='smoothie_menu_delete'),

    # # Smoothie Menu URLs
    path('smoothies/create/', views.create_smoothie_menu, name='create_smoothie_menu'),
    path('smoothies/<int:pk>/edit/', views.smoothie_edit, name='smoothie_edit'),

    path('smoothies/<int:pk>/detail/', views.smoothie_detail, name='smoothie_detail'),

    path('smoothies/<int:pk>/add-ingredient/', views.add_smoothie_ingredient, name='add_smoothie_ingredient'),
    path(
        'smoothies/ingredients/<int:pk>/edit/',
        views.edit_smoothie_ingredient,
        name='edit_smoothie_ingredient'
    ),
    path(
    'smoothies/ingredients/<int:pk>/delete/',
    views.delete_smoothie_ingredient,
    name='delete_smoothie_ingredient'
),


]
