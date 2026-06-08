import re
from .models import Customer
from django import forms


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone']

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        # No alphabet allowed in a phone number.
        if any(ch.isalpha() for ch in phone):
            raise forms.ValidationError("Phone number must contain digits only (no letters).")
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone
