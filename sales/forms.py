from django import forms
from .models import Order
from customers.models import Customer


class OrderForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        label="Select Member (optional)"
    )

    class Meta:
        model = Order
        fields = ['name', 'payment_method', 'customer']