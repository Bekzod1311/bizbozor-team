from django.urls import path
from .views import (
    category_list_view,
    business_detail_view,
    create_listing_view,
    my_listings_view,
    edit_listing_view,
    deactivate_listing_view,
    request_delete_listing_view,
    delete_listing_view,
    toggle_favorite_view,
    favorite_list_view,
    notification_list_view,
    profile_view,
    edit_profile_view,
)

urlpatterns = [
    # CATEGORY LIST (YANGI)
    path('category/<slug:category_slug>/', category_list_view, name='category_list'),

    # DETAIL
    path('biznes/<slug:slug>/', business_detail_view, name='business_detail'),

    # CREATE
    path('create/', create_listing_view, name='create_listing'),

    # DASHBOARD
    path('my-listings/', my_listings_view, name='my_listings'),

    # EDIT / ACTIONS
    path('edit/<slug:slug>/', edit_listing_view, name='edit_listing'),
    path('deactivate/<slug:slug>/', deactivate_listing_view, name='deactivate_listing'),
    path('request-delete/<slug:slug>/', request_delete_listing_view, name='request_delete_listing'),
    path('delete/<slug:slug>/', delete_listing_view, name='delete_listing'),

    # FAVORITE
    path('favorites/', favorite_list_view, name='favorite_list'),
    path('favorite/<slug:slug>/', toggle_favorite_view, name='toggle_favorite'),
    path('notifications/', notification_list_view, name='notifications'),

    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
]