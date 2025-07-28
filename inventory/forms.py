from django import forms
from .models import StockEntry, Ingredient, SmoothieMenu, SmoothieIngredient
from django.forms import inlineformset_factory


class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ['ingredient', 'quantity']
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'ingredient': 'Select Ingredient',
            'quantity': 'Quantity to Add',
        }

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'unit', 'quantity_in_stock', 'low_stock_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SmoothieMenuForm(forms.ModelForm):
    class Meta:
        model = SmoothieMenu
        fields = ['name', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SmoothieIngredientForm(forms.ModelForm):
    class Meta:
        model = SmoothieIngredient
        fields = ['ingredient', 'amount']