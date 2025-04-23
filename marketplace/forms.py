from django import forms
from .models import MarketplaceListing

class ListingForm(forms.ModelForm):
    class Meta:
        model = MarketplaceListing
        fields = ['price']
        widgets = {
            'price': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'})
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price 