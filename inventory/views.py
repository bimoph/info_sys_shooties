from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
# from django.db.models import F  # ✅ Import F from django.db.models
from .models import Ingredient, StockEntry, SmoothieMenu, SmoothieIngredient

from .forms import StockEntryForm, IngredientForm, SmoothieIngredientForm, SmoothieMenuForm, StockEntryEditForm
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
import csv





@login_required
def inventory_dashboard(request):
    ingredients = Ingredient.objects.all()
    # low_stock = ingredients.filter(quantity_in_stock__lt=5)  # ✅ fixed threshold
    return render(request, 'inventory/dashboard.html', {
        'ingredients': ingredients,
        'role': request.user.role,
    })

@login_required
def add_stock(request):
    if request.method == 'POST':
        form = StockEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.reason = 'manual_add'
            entry.timestamp = timezone.now()
            entry.save()

            # Update actual stock
            ingredient = entry.ingredient
            ingredient.quantity_in_stock += entry.quantity
            ingredient.save()

            messages.success(request, f"Successfully added {entry.quantity} {ingredient.unit} to {ingredient.name}.")
            return redirect('inventory_dashboard')
    else:
        form = StockEntryForm()

    return render(request, 'inventory/add_stock.html', {'form': form, 'role': request.user.role,})




# def ingredient_list(request):
#     ingredients = Ingredient.objects.all()
#     return render(request, 'inventory/ingredient_list.html', {'ingredients': ingredients})
@login_required
def ingredient_create(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory_dashboard')
    else:
        form = IngredientForm()
    return render(request, 'inventory/ingredient_form.html', {'form': form, 'title': 'Add Ingredient', 'role': request.user.role,})

@login_required
def ingredient_update(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('inventory_dashboard')
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, 'inventory/ingredient_form.html', {'form': form, 'title': 'Edit Ingredient', 'role': request.user.role,})

@login_required
def ingredient_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        ingredient.delete()
        return redirect('inventory_dashboard')
    return render(request, 'inventory/ingredient_confirm_delete.html', {'ingredient': ingredient, 'role': request.user.role,})

@login_required
def stockentry_list(request):
    user = request.user

    if user.role == 'cashier':
        entries = StockEntry.objects.select_related('ingredient').filter(reason='manual_add').order_by('-timestamp')
    else:
        entries = StockEntry.objects.select_related('ingredient').order_by('-timestamp')


    if 'export' in request.GET:
        # CSV export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stock_entries.csv"'

        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Quantity', 'Unit', 'Timestamp', 'Reason'])

        for entry in entries:
            writer.writerow([
                entry.ingredient.name,
                entry.quantity,
                entry.ingredient.unit,
                entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                entry.get_reason_display()
            ])
        return response

    return render(request, 'inventory/stockentry_list.html', {'entries': entries, 'role': request.user.role,})

@login_required
def stockentry_edit(request, pk):
    entry = get_object_or_404(StockEntry, pk=pk)

    if request.method == 'POST':
        form = StockEntryEditForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('stockentry_list')
    else:
        form = StockEntryEditForm(instance=entry)

    return render(request, 'inventory/stockentry_edit.html', {'form': form, 'entry': entry, 'role': request.user.role,})

@login_required
def stockentry_delete(request, pk):
    entry = get_object_or_404(StockEntry, pk=pk)

    if request.method == 'POST':
        entry.delete()
        return redirect('stockentry_list')

    return render(request, 'inventory/stockentry_delete_confirm.html', {'entry': entry, 'role': request.user.role,})


# Smoothie Menu Views
@login_required
def smoothie_menu_list(request):
    smoothies = SmoothieMenu.objects.all()
    return render(request, 'inventory/smoothie_menu_list.html', {'smoothies': smoothies, 'role': request.user.role,})

@login_required
def smoothie_menu_delete(request, pk):
    smoothie = get_object_or_404(SmoothieMenu, pk=pk)
    if request.method == 'POST':
        smoothie.delete()
        return redirect('smoothie_menu_list')
    return render(request, 'inventory/smoothie_menu_confirm_delete.html', {'smoothie': smoothie, 'role': request.user.role,})

# menu & ingredient creation/editing views
@login_required
def create_smoothie_menu(request):
    if request.method == 'POST':
        form = SmoothieMenuForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('smoothie_menu_list')  # or your success URL
    else:
        form = SmoothieMenuForm()
    return render(request, 'inventory/smoothie_menu_form.html', {'form': form, 'role': request.user.role,})

@login_required
def smoothie_detail(request, pk):
    smoothie = get_object_or_404(SmoothieMenu, pk=pk)
    ingredients = SmoothieIngredient.objects.filter(smoothie=smoothie)

    if request.method == 'POST':
        form = SmoothieMenuForm(request.POST, instance=smoothie)
        if form.is_valid():
            form.save()
    else:
        form = SmoothieMenuForm(instance=smoothie)

    return render(request, 'inventory/smoothie_detail.html', {
        'smoothie': smoothie,
        'form': form,
        'ingredients': ingredients,
        'role': request.user.role,
    })

@login_required
def add_smoothie_ingredient(request, pk):
    smoothie = get_object_or_404(SmoothieMenu, pk=pk)

    if request.method == 'POST':
        form = SmoothieIngredientForm(request.POST)
        if form.is_valid():
            smoothie_ingredient = form.save(commit=False)
            smoothie_ingredient.smoothie = smoothie
            smoothie_ingredient.save()
            return redirect('smoothie_detail', pk=smoothie.pk)
    else:
        form = SmoothieIngredientForm()

    return render(request, 'inventory/smoothie_ingredient_form.html', {
        'form': form,
        'smoothie': smoothie,
        'role': request.user.role,
    })

@login_required
def edit_smoothie_ingredient(request, pk):
    ingredient = get_object_or_404(SmoothieIngredient, pk=pk)
    if request.method == 'POST':
        form = SmoothieIngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('smoothie_detail', pk=ingredient.smoothie.pk)
    else:
        form = SmoothieIngredientForm(instance=ingredient)

    return render(request, 'inventory/smoothie_ingredient_form.html', {
        'form': form,
        'smoothie': ingredient.smoothie,
        'edit': True,
        'role': request.user.role,
    })

@login_required
def delete_smoothie_ingredient(request, pk):
    ingredient = get_object_or_404(SmoothieIngredient, pk=pk)
    smoothie_pk = ingredient.smoothie.pk
    if request.method == 'POST':
        ingredient.delete()
        messages.success(request, 'Ingredient deleted successfully.')
        return redirect('smoothie_detail', pk=smoothie_pk)

    return render(request, 'inventory/smoothie_ingredient_confirm_delete.html', {
        'ingredient': ingredient,
        'role': request.user.role,
    })