from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Region, District, Listing, ListingImage, Favorite, Notification


# 🔥 INLINE IMAGE (gallery admin ichida ko‘rish uchun)
class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


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


# 🔥 MAIN LISTING ADMIN (ENG MUHIM)
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'owner',
        'category',
        'region',
        'price',
        'colored_status',
        'approved_by',
        'approved_at',
        'view_count',
        'created_at'
    )

    list_filter = (
        'status',
        'category',
        'region',
        'created_at',
        'approved_at',
    )

    search_fields = (
        'title',
        'description',
        'owner__username',
        'phone',
        'rejection_reason'
    )

    list_editable = (
        'price',
    )

    ordering = ('-created_at',)

    readonly_fields = ('approved_at',)

    list_per_page = 20

    inlines = [ListingImageInline]

    # 🔥 IKKITA ACTION
    actions = ['make_approved', 'make_pending']

    # 🔥 STATUS RANG BILAN
    def colored_status(self, obj):
        color = {
            'approved': 'green',
            'pending': 'orange',
            'inactive': 'gray',
            'delete_requested': 'red'
        }.get(obj.status, 'black')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    colored_status.short_description = 'Status'

    # 🔥 APPROVE (notification bilan)
    def make_approved(self, request, queryset):
        for listing in queryset:
            listing.status = 'approved'
            listing.approved_at = timezone.now()
            listing.approved_by = request.user
            listing.rejection_reason = ''
            listing.save()

            Notification.objects.create(
                user=listing.owner,
                message=f'"{listing.title}" e\'loningiz tasdiqlandi.'
            )

        self.message_user(request, "Tanlangan e'lonlar tasdiqlandi.")

    make_approved.short_description = "Tanlanganlarni tasdiqlash"

    # 🔥 PENDING / REJECT
    def make_pending(self, request, queryset):
        for listing in queryset:
            listing.status = 'pending'
            listing.save()

            Notification.objects.create(
                user=listing.owner,
                message=f'"{listing.title}" e\'loningiz ko‘rib chiqish holatiga qaytarildi.'
            )

        self.message_user(request, "Tanlangan e'lonlar pending holatga qaytarildi.")

    make_pending.short_description = "Tanlanganlarni pending qilish"


# ListingImage admin
@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'image')


# Favorite admin
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')