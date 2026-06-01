from django import forms
from .models import Order, PaymentMethod
from customers.models import Customer


class OrderForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        label="Select Member (optional)"
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        required=True,
        label="Payment Method",
    )

    class Meta:
        model = Order
        fields = ['name', 'payment_method', 'customer']