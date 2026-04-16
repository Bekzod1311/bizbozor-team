from django.shortcuts import render
from listings.models import Listing, Category

def home_view(request):
    featured_listings = Listing.objects.filter(
        status='approved',
        is_featured=True
    ).order_by('-created_at')[:6]

    popular_listings = Listing.objects.filter(
        status='approved'
    ).order_by('-view_count', '-created_at')[:6]

    categories = Category.objects.all()

    context = {
        'featured_listings': featured_listings,
        'popular_listings': popular_listings,
        'categories': categories,
    }

    return render(request, 'home.html', context)