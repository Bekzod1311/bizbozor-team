from django import forms
from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'category',
            'region',
            'district',
            'title',
            'price',
            'short_description',
            'description',
            'phone',
            'telegram_username',
            'google_maps_link',
            'main_image',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'telegram_username': forms.TextInput(attrs={'class': 'form-control'}),
            'google_maps_link': forms.URLInput(attrs={'class': 'form-control'}),
            'main_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional placeholderlar
        self.fields['title'].widget.attrs.update({
            'placeholder': "Masalan: Tayyor kafe sotiladi"
        })
        self.fields['price'].widget.attrs.update({
            'placeholder': "Masalan: 120000000"
        })
        self.fields['short_description'].widget.attrs.update({
            'placeholder': "Qisqa va aniq tavsif"
        })
        self.fields['description'].widget.attrs.update({
            'placeholder': "To'liq ma'lumot yozing"
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': "+998901234567"
        })
        self.fields['telegram_username'].widget.attrs.update({
            'placeholder': "username"
        })

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError("Sarlavha kamida 5 ta belgidan iborat bo'lishi kerak.")
        return title

    def clean_short_description(self):
        short_description = self.cleaned_data.get('short_description', '').strip()
        if len(short_description) < 10:
            raise forms.ValidationError("Qisqa tavsif kamida 10 ta belgidan iborat bo'lishi kerak.")
        return short_description

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 20:
            raise forms.ValidationError("To'liq tavsif kamida 20 ta belgidan iborat bo'lishi kerak.")
        return description

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return price

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if len(phone) < 9:
            raise forms.ValidationError("Telefon raqam to'g'ri kiritilmagan.")
        return phone