from django.shortcuts import render, get_object_or_404, redirect
from .models import Listing, ListingImage, Region, Category, Favorite, Notification, Profile, AuditLog
from django.contrib.auth.decorators import login_required
from .forms import ListingForm, ProfileForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
import re

BAD_WORDS = [
    'sex', 'porn', 'xxx', 'nude',
    'fuck', 'shit', 'bitch',
    'казино', 'ставка'
]

SPAM_PATTERNS = [
    r'http[s]?://',
    r'www\.',
    r't\.me/',
    r'@\w+',
]


def check_listing_content(title, description):
    text = f"{title} {description}".lower()

    # 🔴 BAD WORDS → reject
    for word in BAD_WORDS:
        if word in text:
            return 'reject', f"Ruxsat etilmagan so‘z: {word}"

    # 🔴 SPAM → reject
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text):
            return 'reject', "Spam yoki tashqi link aniqlangan"

    # ⚠️ juda qisqa → pending
    if len(description.strip()) < 20:
        return 'pending', "Tavsif juda qisqa"

    # ⚠️ juda ko‘p katta harf
    if description.isupper():
        return 'pending', "Tavsif noto‘g‘ri formatda"

    return 'ok', None


def business_list_view(request):
    listings = Listing.objects.filter(
        status='approved',
        category__slug='tayyor-biznes'
    )

    query = request.GET.get('q')
    region_id = request.GET.get('region')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')

    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    if region_id:
        listings = listings.filter(region_id=region_id)

    if min_price:
        listings = listings.filter(price__gte=min_price)

    if max_price:
        listings = listings.filter(price__lte=max_price)

    if sort == 'oldest':
        listings = listings.order_by('created_at')
    elif sort == 'price_low':
        listings = listings.order_by('price')
    elif sort == 'price_high':
        listings = listings.order_by('-price')
    else:
        listings = listings.order_by('-created_at')

    regions = Region.objects.all()

    paginator = Paginator(listings, 6)  # har sahifada 6 ta listing
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'listings/business_list.html', {
        'listings': page_obj,
        'regions': regions
    })

def business_detail_view(request, slug):
    """
    Bitta listing (e'lon) detail sahifasi.
    Approved bo'lsa hamma ko'radi.
    Approved bo'lmasa faqat egasi ko'ra oladi.
    """
    listing = get_object_or_404(Listing, slug=slug)

    listing.view_count = F('view_count') + 1
    listing.save(update_fields=['view_count'])
    listing.refresh_from_db()

    # Agar listing approved bo'lmasa, faqat egasiga ko'rsatamiz
    if listing.status != 'approved':
        if not request.user.is_authenticated or listing.owner != request.user:
            return render(request, '404.html', status=404)
    
    images = listing.images.all() # related_name='images' dan keladi.

    is_favorited = False

    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user,
            listing=listing
        ).exists()

    context = {
        'listing': listing,
        'images': images,
        'is_favorited': is_favorited,
    }

    return render(request, 'listings/business_detail.html', context)

@login_required
def create_listing_view(request):
    """
    User yangi e'lon qo'shadi.
    """

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)

        if form.is_valid():
            title = form.cleaned_data.get('title')
            description = form.cleaned_data.get('description')

            status, reason = check_listing_content(title, description)

            if status == 'reject':
                messages.error(request, reason)
                return redirect('create_listing')

            listing = form.save(commit=False)
            listing.owner = request.user

            if status == 'pending':
                listing.status = 'pending'
            else:
                listing.status = 'pending'   # MVP: hammasi pendingga tushadi
            listing.save()

            if status == 'pending':
                Notification.objects.create(
                    user=request.user,
                    message="E'loningiz tekshiruvga yuborildi."
                )

            create_audit_log(
                listing=listing,
                actor=request.user,
                action='created',
                old_status=None,
                new_status=listing.status,
                note="AI filter orqali tekshirildi"
            )

            Notification.objects.create(
                user=request.user,
                message="E'loningiz muvaffaqiyatli yuborildi va ko‘rib chiqilmoqda."
            )

            # Multi image fayllarni olamiz
            gallery_images = request.FILES.getlist('gallery_images')

            # 1 tadan kam bo'lmasin, 8 tadan ko'p bo'lmasin
            if len(gallery_images) < 1:
                messages.error(request, "Kamida 1 ta qo‘shimcha rasm yuklang.")
                listing.delete()
                return redirect('create_listing')

            if len(gallery_images) > 8:
                messages.error(request, "Maksimum 8 ta rasm yuklash mumkin.")
                listing.delete()
                return redirect('create_listing')

            # Rasmlarni saqlaymiz
            for image in gallery_images:
                ListingImage.objects.create(
                    listing=listing,
                    image=image
                )

            messages.success(request, "E'lon muvaffaqiyatli qo‘shildi. Admin tasdiqlashini kuting.")
            return redirect('category_list', category_slug=listing.category.slug)

    else:
        form = ListingForm()

    return render(request, 'listings/create_listing.html', {'form': form})

@login_required
def my_listings_view(request):
    """
    Login qilgan userning o'z e'lonlari ro'yxati.
    """
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        listings = listings.filter(status=status_filter)

    total = Listing.objects.filter(owner=request.user).count()
    approved = Listing.objects.filter(owner=request.user, status='approved').count()
    pending = Listing.objects.filter(owner=request.user, status='pending').count()
    inactive = Listing.objects.filter(owner=request.user, status='inactive').count()
    delete_requested = Listing.objects.filter(owner=request.user, status='delete_requested').count()

    # Har bir listing uchun qolgan kunni hisoblaymiz
    for listing in listings:
        if listing.status == 'delete_requested' and listing.delete_requested_at:
            allowed_time = listing.delete_requested_at + timedelta(days=10)
            remaining_days = (allowed_time - timezone.now()).days
            listing.remaining_days = max(remaining_days, 0)
        else:
            listing.remaining_days = None

    context = {
        'listings': listings,
        'total': total,
        'approved': approved,
        'pending': pending,
        'inactive': inactive,
        'delete_requested': delete_requested,
    }

    return render(request, 'listings/my_listings.html', context)


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Avval unread notificationlarni o‘qilgan qilamiz
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    context = {
        'notifications': notifications
    }

    return render(request, 'listings/notifications.html', context)


@login_required
def edit_listing_view(request, slug):
    """
    User o'z e'lonini tahrir qiladi.
    Gallery rasmlarini ham boshqaradi:
    - eski rasmlarni o'chirish
    - yangi rasmlar qo'shish
    """
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)

    if request.method == 'POST':
        old_status = listing.status
        
        form = ListingForm(request.POST, request.FILES, instance=listing)

        if form.is_valid():
            edited_listing = form.save(commit=False)
            edited_listing.owner = request.user
            edited_listing.save()

            create_audit_log(        # 👈 SAVE dan KEYIN
                listing=edited_listing,
                actor=request.user,
                action='updated',
                old_status=old_status,
                new_status=edited_listing.status,
                note="User e'lonni tahrirladi."
            )

            Notification.objects.create(
                user=request.user,
                message="E'loningiz yangilandi."
            )

            # 1. O'chiriladigan gallery rasmlarni olish
            delete_image_ids = request.POST.getlist('delete_images')

            if delete_image_ids:
                ListingImage.objects.filter(
                    id__in=delete_image_ids,
                    listing=listing
                ).delete()

            # 2. Yangi qo'shilgan gallery rasmlar
            new_gallery_images = request.FILES.getlist('gallery_images')

            # Hozirgi rasm sonini hisoblaymiz
            current_count = listing.images.count()
            new_count = len(new_gallery_images)

            if current_count + new_count > 8:
                messages.error(request, "Gallery uchun maksimum 8 ta rasm bo‘lishi mumkin.")
                return render(request, 'listings/edit_listing.html', {
                    'form': form,
                    'listing': listing
                })

            for image in new_gallery_images:
                ListingImage.objects.create(
                    listing=listing,
                    image=image
                )

            messages.success(request, "E'lon muvaffaqiyatli yangilandi.")
            return redirect('business_detail', slug=edited_listing.slug)

    else:
        form = ListingForm(instance=listing)

    return render(request, 'listings/edit_listing.html', {
        'form': form,
        'listing': listing
    })

@login_required
def deactivate_listing_view(request, slug):
    """
    User o'z e'lonini inactive holatga o'tkazadi.
    Faqat egasi buni qila oladi.
    """
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)

    if listing.status == 'approved':
        old_status = listing.status   # 👈 SHU YERGA

        listing.status = 'inactive'
        listing.save()

        create_audit_log(             # 👈 SAVE dan KEYIN
            listing=listing,
            actor=request.user,
            action='inactive',
            old_status=old_status,
            new_status='inactive',
            note="User e'lonni faol emas holatga o'tkazdi."
        )

    Notification.objects.create(
        user=request.user,
        message="E'lon faol emas holatga o‘tkazildi."
    )

    messages.success(request, "E'lon faol emas holatiga o'tkazildi.")
    return redirect('my_listings')

@login_required
def request_delete_listing_view(request, slug):
    """
    User o'z e'loni uchun o'chirish so'rovi yuboradi.
    Faqat inactive bo'lgan e'lon uchun ruxsat beramiz.
    """
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)

    if listing.status == 'inactive':
        old_status = listing.status

        listing.status = 'delete_requested'
        listing.delete_requested_at = timezone.now()
        listing.save()

        create_audit_log(             # 👈 SAVE dan KEYIN
            listing=listing,
            actor=request.user,
            action='delete_requested',
            old_status=old_status,
            new_status='delete_requested',
            note="User e'lonni o‘chirish so‘rovini yubordi."
        )

        Notification.objects.create(
            user=request.user,
            message="E'lon faol emas holatga o‘tkazildi."
        )
        messages.success(request, "E'lon uchun o‘chirish so‘rovi yuborildi.")
    else:
        messages.error(request, "Avval e'lonni faol emas holatiga o'tkazing.")

    return redirect('my_listings')

@login_required
def delete_listing_view(request, slug):
    """
    User o'z e'lonini faqat delete request yuborilganidan 10 kun o'tgach o'chira oladi.
    """
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)

    if listing.status != 'delete_requested' or not listing.delete_requested_at:
        messages.error(request, "Bu e'lon hali o‘chirish bosqichiga yetmagan.")
        return redirect('my_listings')

    allowed_time = listing.delete_requested_at + timedelta(days=10)

    if timezone.now() >= allowed_time:
        listing.delete()
        messages.success(request, "E'lon muvaffaqiyatli o‘chirildi.")
    else:
        remaining_days = (allowed_time - timezone.now()).days
        if remaining_days < 1:
            remaining_days = 1
        messages.error(request, f"E'lonni o‘chirish uchun yana {remaining_days} kun kutish kerak.")

    return redirect('my_listings')



def category_list_view(request, category_slug):
    """
    Kategoriya bo'yicha listinglar ro'yxati:
    tayyor-biznes, franshiza, startap, xizmat
    """
    category = get_object_or_404(Category, slug=category_slug)

    listings = Listing.objects.filter(
        status='approved',
        category=category
    )

    query = request.GET.get('q')
    region_id = request.GET.get('region')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')

    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    if region_id:
        listings = listings.filter(region_id=region_id)

    if min_price:
        listings = listings.filter(price__gte=min_price)

    if max_price:
        listings = listings.filter(price__lte=max_price)

    if sort == 'oldest':
        listings = listings.order_by('created_at')
    elif sort == 'price_low':
        listings = listings.order_by('price')
    elif sort == 'price_high':
        listings = listings.order_by('-price')
    else:
        listings = listings.order_by('-created_at')

    regions = Region.objects.all()

    paginator = Paginator(listings, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'listings': page_obj,
        'regions': regions,
        'current_category': category,
    }

    return render(request, 'listings/business_list.html', context)


@login_required
def toggle_favorite_view(request, slug):
    """
    E'lonni sevimlilarga qo'shish yoki olib tashlash.
    """
    listing = get_object_or_404(Listing, slug=slug, status='approved')

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing
    )

    if not created:
        favorite.delete()
        messages.success(request, "E'lon sevimlilardan olib tashlandi.")
    else:
        messages.success(request, "E'lon sevimlilarga qo‘shildi.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def favorite_list_view(request):
    """
    Userning sevimli e'lonlari ro'yxati.
    """
    favorites = Favorite.objects.filter(user=request.user).select_related('listing').order_by('-created_at')

    context = {
        'favorites': favorites
    }
    return render(request, 'listings/favorite_list.html', context)


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    user_listings = Listing.objects.filter(owner=request.user).order_by('-created_at')

    context = {
        'profile': profile,
        'user_listings': user_listings,
    }
    return render(request, 'listings/profile.html', context)

@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil muvaffaqiyatli yangilandi.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'listings/edit_profile.html', {
        'form': form,
        'profile': profile
    })


def public_profile_view(request, username):
    seller = get_object_or_404(User, username=username)
    seller_profile, created = Profile.objects.get_or_create(user=seller)

    seller_listings = Listing.objects.filter(
        owner=seller,
        status='approved'
    ).order_by('-created_at')

    context = {
        'seller': seller,
        'seller_profile': seller_profile,
        'seller_listings': seller_listings,
    }

    return render(request, 'listings/public_profile.html', context)


def create_audit_log(listing, actor, action, old_status=None, new_status=None, note=None):
    AuditLog.objects.create(
        listing=listing,
        actor=actor,
        action=action,
        old_status=old_status,
        new_status=new_status,
        note=note
    )


@staff_member_required
def moderation_queue_view(request):
    pending_listings = Listing.objects.filter(status='pending').order_by('-created_at')

    context = {
        'pending_listings': pending_listings
    }
    return render(request, 'listings/moderation_queue.html', context)

@staff_member_required
def approve_listing_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug)

    old_status = listing.status
    listing.status = 'approved'
    listing.save()

    create_audit_log(
        listing=listing,
        actor=request.user,
        action='approved',
        old_status=old_status,
        new_status='approved',
        note="Moderation queue orqali tasdiqlandi"
    )

    messages.success(request, "E'lon tasdiqlandi")
    return redirect('moderation_queue')


@staff_member_required
def reject_listing_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug)

    old_status = listing.status
    listing.status = 'rejected'
    listing.rejection_reason = "Moderation orqali rad etildi"
    listing.save()

    create_audit_log(
        listing=listing,
        actor=request.user,
        action='rejected',
        old_status=old_status,
        new_status='rejected',
        note="Moderation queue orqali rad etildi"
    )

    messages.warning(request, "E'lon rad etildi")
    return redirect('moderation_queue')