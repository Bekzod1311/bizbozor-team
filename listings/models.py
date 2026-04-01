from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    """
    E'lon kategoriyasi.
    Masalan:
    - Tayyor biznes
    - Franshiza
    - Startap
    - Xizmat
    """
    name_uz = models.CharField(max_length=100, verbose_name="Nomi (UZ)")
    name_ru = models.CharField(max_length=100, verbose_name="Nomi (RU)")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")

    def save(self, *args, **kwargs):
        """
        Agar slug bo'sh bo'lsa, name_uz asosida avtomatik yasab beradi.
        """
        if not self.slug:
            self.slug = slugify(self.name_uz)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_uz


class Region(models.Model):
    """
    O'zbekiston viloyatlari.
    Masalan:
    - Toshkent
    - Samarqand
    - Farg'ona
    """
    name_uz = models.CharField(max_length=100, verbose_name="Viloyat nomi (UZ)")
    name_ru = models.CharField(max_length=100, verbose_name="Viloyat nomi (RU)")

    def __str__(self):
        return self.name_uz


class District(models.Model):
    """
    Tumanlar yoki shaharlar.
    Har biri bitta viloyatga tegishli bo'ladi.
    """
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='districts',
        verbose_name="Viloyat"
    )
    name_uz = models.CharField(max_length=100, verbose_name="Tuman nomi (UZ)")
    name_ru = models.CharField(max_length=100, verbose_name="Tuman nomi (RU)")

    def __str__(self):
        return f"{self.name_uz} ({self.region.name_uz})"


class Listing(models.Model):
    """
    Asosiy e'lon modeli.
    Marketplace'dagi barcha e'lonlar shu modelda saqlanadi.
    """

    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
        ('inactive', 'Faol emas'),
        ('delete_requested', 'O‘chirish so‘ralgan'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name="E'lon egasi"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name="Kategoriya"
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
        verbose_name="Viloyat"
    )

    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
        verbose_name="Tuman / shahar"
    )

    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")

    main_image = models.ImageField(
        upload_to='listings/main_images/',
        blank=True,
        null=True,
        verbose_name="Asosiy rasm"
    )

    price = models.PositiveBigIntegerField(verbose_name="Narx")
    short_description = models.CharField(max_length=300, verbose_name="Qisqa tavsif")
    description = models.TextField(verbose_name="To'liq tavsif")

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Manzil (ixtiyoriy)"
    )

    google_maps_link = models.URLField(
        blank=True,
        verbose_name="Google Maps link (ixtiyoriy)"
    )

    phone = models.CharField(max_length=30, verbose_name="Telefon raqam")
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram username"
    )

    is_active_business = models.BooleanField(
        default=True,
        verbose_name="Faol biznesmi?"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Holat"
    )

    view_count = models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar soni")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    delete_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="O‘chirish so‘rovi vaqti"
    )

    def save(self, *args, **kwargs):
        """
        Agar slug bo'sh bo'lsa, title asosida avtomatik yasab beradi.
        """
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

    view_count = models.PositiveIntegerField(default=0)

class ListingImage(models.Model):
    """
    Listing uchun qo‘shimcha rasmlar (gallery).
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='listings/gallery/',
        verbose_name="Rasm"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.listing.title} - Image"
    

class Favorite(models.Model):
    """
    User saqlab qo'ygan sevimli e'lonlar.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"

    def __str__(self):
        return f"{self.user.username} -> {self.listing.title}"
    

from django.contrib.auth.models import User


class Notification(models.Model):
    """
    User uchun notification.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"