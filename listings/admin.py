from django.contrib import admin
from .models import Category, Region, District, Listing, ListingImage, Favorite


# Category admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_uz', 'slug')
    prepopulated_fields = {'slug': ('name_uz',)}


# Region admin
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_uz')


# District admin
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_uz', 'region')


# Listing admin
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'region', 'price', 'status', 'created_at')
    list_filter = ('status', 'category', 'region')
    search_fields = ('title',)


admin.site.register(ListingImage)
admin.site.register(Favorite)