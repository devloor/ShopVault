from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
    path('product/<int:pk>/', views.product_detail, name='product'),
    path('product/<int:pk>/review/', views.add_review, name='add_review'),
    path('review/<int:pk>/delete/', views.delete_review, name='delete_review'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:pk>/', views.toggle_wishlist, name='toggle_wishlist'),
    # Q&A
    path('product/<int:pk>/question/', views.ask_question, name='ask_question'),
    path('question/<int:question_pk>/answer/', views.answer_question, name='answer_question'),
    # Admin analytics
    path('staff/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Static pages
    path('deals/', views.deals, name='deals'),
    path('customer-service/', views.customer_service, name='customer_service'),
    path('gift-cards/', views.gift_cards, name='gift_cards'),
    path('sell/', views.sell, name='sell'),
    path('about/', views.about, name='about'),
    path('careers/', views.careers, name='careers'),
    path('advertise/', views.advertise, name='advertise'),
    path('conditions-of-use/', views.conditions, name='conditions'),
    path('privacy/', views.privacy, name='privacy'),
]
