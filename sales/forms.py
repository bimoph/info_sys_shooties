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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default the payment method to QRIS on a fresh (unbound) form.
        # The Shooties Passport flow overrides this client-side when a passport
        # is scanned.
        if not self.is_bound and not self.initial.get('payment_method'):
            qris = PaymentMethod.objects.filter(is_active=True, name__iexact='QRIS').first()
            if qris:
                self.fields['payment_method'].initial = qris.pk