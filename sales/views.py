from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from inventory.models import SmoothieMenu
from .forms import OrderForm
from .models import Order, OrderItem

@login_required
def view_order(request):
    pending_orders = Order.objects.filter(is_ready=False, is_served=False).order_by('created_at')
    ready_orders = Order.objects.filter(is_ready=True, is_served=False).order_by('ready_at')
    served_orders = Order.objects.filter(is_served=True).order_by('served_at')

    context = {
        'pending_orders': pending_orders,
        'ready_orders': ready_orders,
        'served_orders': served_orders,
    }
    return render(request, 'sales/orders.html', context)


@require_POST
@login_required
def mark_ready(request, order_id):
    order = Order.objects.get(id=order_id)
    order.is_ready = True
    order.ready_at = timezone.now()
    order.save()
    return JsonResponse({'success': True})

@require_POST
@login_required
def mark_served(request, order_id):
    order = Order.objects.get(id=order_id)
    if not order.is_ready:
        order.is_ready = True
        order.ready_at = timezone.now()
    order.is_served = True
    order.served_at = timezone.now()
    order.save()
    return JsonResponse({'success': True})

@require_POST
@login_required
def move_to_pending(request, order_id):
    order = Order.objects.get(id=order_id)
    order.is_served = False
    order.served_at = None
    order.is_ready = False
    order.ready_at = None
    order.save()
    return JsonResponse({'success': True})

@require_POST
@login_required
def move_to_ready(request, order_id):
    order = Order.objects.get(id=order_id)
    order.is_served = False
    order.served_at = None
    order.save()
    return JsonResponse({'success': True})

@require_POST
@login_required
def delete_order(request, order_id):
    order = Order.objects.get(id=order_id)
    order.delete()
    return JsonResponse({'success': True})

@login_required
def create_order(request):
    smoothies = SmoothieMenu.objects.all()

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_at = timezone.now()
            order.save()

            total_price = 0
            for smoothie in smoothies:
                qty = int(request.POST.get(f'smoothie_{smoothie.id}', 0))
                if qty > 0:
                    OrderItem.objects.create(order=order, smoothie=smoothie, quantity=qty)
                    total_price += qty * smoothie.price

            order.total_price = total_price
            order.save()

            return redirect('view_order')
    else:
        form = OrderForm()

    return render(request, 'sales/create_order.html', {'form': form, 'smoothies': smoothies})


