# media_library/urls.py
from django.urls import path, re_path
from . import api_views, views

app_name = 'media_library'

urlpatterns = [
    path('', views.media_library, name='media_library'),
    path('upload/', views.media_upload, name='media_upload'),
    path('detail/<int:pk>/', views.media_detail, name='media_detail'),
    path('edit/<int:pk>/', views.media_edit, name='media_edit'),
    path('delete/<int:pk>/', views.media_delete, name='media_delete'),
    path('category/<slug:slug>/', views.media_category, name='media_category'),
    path('html-site/<int:media_id>/', views.serve_html_site, name='serve_html_site'),
    re_path(r'^html-site/(?P<media_id>\d+)/(?P<path>.+)$', views.serve_html_site, name='serve_html_site_path'),

    # API
    path('api/track-usage/', api_views.track_media_usage, name='api_track_usage'),
    path('api/remove-usage/', api_views.remove_media_usage, name='api_remove_usage'),
    path('api/media-list/', api_views.media_list, name='api_media_list'),
    path('api/media-detail/<int:pk>/', api_views.media_detail, name='api_media_detail'),
]
