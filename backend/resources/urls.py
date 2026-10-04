from django.urls import path

from . import views

urlpatterns = [
    path('resources/', views.ResourceListView.as_view(), name='resource-list'),
    path('resources/<int:pk>/', views.ResourceDetailView.as_view(), name='resource-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('creators/', views.CreatorListView.as_view(), name='creator-list'),
    path('languages/', views.LanguageListView.as_view(), name='language-list'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('recommendations/', views.RecommendationListView.as_view(), name='recommendations'),
]
