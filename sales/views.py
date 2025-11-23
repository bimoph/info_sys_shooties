from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.http import HttpResponse
from customers.models import Customer  # import at the top
from django.db import transaction
import pytz
from datetime import datetime, time
from django.db.models import Sum

from django.utils.dateparse import parse_date



from inventory.models import SmoothieMenu, SmoothieIngredient, StockEntry
from .forms import OrderForm
from .models import Order, OrderItem

from customers.utils import find_customer_by_phone, normalize_phone  # import helper

@login_required
def view_order(request):
    # Get Jakarta timezone
    jakarta_tz = pytz.timezone("Asia/Jakarta")
    now_jakarta = timezone.now().astimezone(jakarta_tz)

    # Start & end of today in Jakarta time
    start_of_day = datetime.combine(now_jakarta.date(), time.min).replace(tzinfo=jakarta_tz)
    end_of_day = datetime.combine(now_jakarta.date(), time.max).replace(tzinfo=jakarta_tz)
    print(request.user.role)
    # If user is Admin → do NOT filter by store
    if request.user.role == "admin":
        base_filter = {
            "created_at__range": (start_of_day, end_of_day)
        }
    else:
        base_filter = {
            "store": request.user.store,
            "created_at__range": (start_of_day, end_of_day)
        }

    pending_orders = Order.objects.filter(
        is_ready=False,
        is_served=False,
        **base_filter
    ).order_by('created_at')

    ready_orders = Order.objects.filter(
        is_ready=True,
        is_served=False,
        **base_filter
    ).order_by('ready_at')

    served_orders = Order.objects.filter(
        is_served=True,
        **base_filter
    ).order_by('served_at')
    # --- New: Aggregate pending quantities per menu ---
    pending_items_summary = (
        OrderItem.objects
        .filter(order__in=pending_orders)
        .values('smoothie__name')
        .annotate(pending_qty=Sum('quantity'))
        .order_by('-pending_qty')
    )

    return render(request, 'sales/orders.html', {
        'pending_orders': pending_orders,
        'ready_orders': ready_orders,
        'served_orders': served_orders,
        'role': request.user.role,
        'pending_items_summary' : pending_items_summary,
    })


@require_POST
@login_required
def mark_ready(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.mark_ready()
    return HttpResponse(status=204)

@require_POST
@login_required
def mark_served(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.mark_served()
    return HttpResponse(status=204)

@require_POST
@login_required
def move_to_pending(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.is_ready = False
    order.is_served = False
    order.ready_at = None
    order.served_at = None
    order.save()
    return HttpResponse(status=204)

@require_POST
@login_required
def move_to_ready(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    jakarta_tz = pytz.timezone("Asia/Jakarta")
    # now_jakarta = timezone.now().astimezone(jakarta_tz)
    order.is_ready = True
    order.is_served = False
    order.ready_at = timezone.now().astimezone(jakarta_tz)
    order.served_at = None
    order.save()
    return HttpResponse(status=204)

@login_required
def order_list(request):
    # Get filter params from GET
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    orders = Order.objects.filter(store=request.user.store)

    if start_date_str:
        start_date = parse_date(start_date_str)
        if start_date:
            orders = orders.filter(created_at__date__gte=start_date)

    if end_date_str:
        end_date = parse_date(end_date_str)
        if end_date:
            orders = orders.filter(created_at__date__lte=end_date)

    # Calculate total price by payment method in filtered orders
    payment_totals = (
        orders.values('payment_method')
        .annotate(total_amount=Sum('total_price'))
        .order_by('payment_method')
    )

    context = {
        'orders': orders.order_by('-created_at'),
        'payment_totals': payment_totals,
        'start_date': start_date_str or '',
        'end_date': end_date_str or '',
        'role': request.user.role,
    }
    return render(request, 'sales/order_list.html', context)

@require_POST
@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    with transaction.atomic():
        for item in order.orderitem_set.all():
            smoothie = item.smoothie
            qty = item.quantity
            smoothie_ingredients = SmoothieIngredient.objects.filter(smoothie=smoothie)

            for si in smoothie_ingredients:
                total_restore = qty * si.amount
                si.ingredient.quantity_in_stock += total_restore
                si.ingredient.save()

                StockEntry.objects.create(
                    ingredient=si.ingredient,
                    quantity=total_restore,
                    reason='sale_cancellation'
                )

        order.delete()

    return HttpResponse(status=204)


@login_required
def create_order(request):
    smoothies = SmoothieMenu.objects.filter(stores=request.user.store)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        print("POST received:", request.POST)
        print("Form errors:", form.errors)
        if form.is_valid():
            print('order valid')
            order = form.save(commit=False)

            customer_id = request.POST.get('selected_customer_id', '').strip()
            new_phone = request.POST.get('new_phone', '').strip()
            new_name = form.cleaned_data.get('name', '').strip()

            # 1) If customer_id provided -> use it
            selected_customer = None
            if customer_id:
                try:
                    selected_customer = Customer.objects.get(pk=customer_id)
                except Customer.DoesNotExist:
                    selected_customer = None

            # 2) else if new_phone provided -> find existing by normalized phone; if not found create new
            elif new_phone:
                existing = find_customer_by_phone(new_phone)
                if existing:
                    selected_customer = existing
                else:
                    # create new safely
                    selected_customer = Customer.objects.create(name=new_name or new_phone, phone=new_phone)

            # 3) else -> guest (no customer)
            if selected_customer:
                order.customer = selected_customer
                order.name = selected_customer.name
            else:
                order.customer = None
                order.name = new_name or 'Guest'

            jakarta_tz = pytz.timezone("Asia/Jakarta")
            order.created_at = timezone.now().astimezone(jakarta_tz)
            order.store = request.user.store
            order.total_price = 0
            order.save()

            # Build items + stock deductions
            total_price = 0
            for smoothie in smoothies:
                qty_raw = request.POST.get(f'smoothie_{smoothie.id}', 0)
                try:
                    qty = int(qty_raw)
                except (TypeError, ValueError):
                    qty = 0
                if qty > 0:
                    OrderItem.objects.create(order=order, smoothie=smoothie, quantity=qty)
                    total_price += qty * float(smoothie.price)

                    # Deduct ingredients
                    smoothie_ingredients = SmoothieIngredient.objects.filter(smoothie=smoothie)
                    for si in smoothie_ingredients:
                        total_deduction = qty * si.amount
                        ing = si.ingredient
                        ing.quantity_in_stock = ing.quantity_in_stock - total_deduction
                        ing.save()

                        StockEntry.objects.create(
                            ingredient=ing,
                            quantity=-total_deduction,
                            reason='sale_deduct'
                        )

            order.total_price = total_price
            order.save()
            print('ok order masuk')
            return redirect('view_order')
    else:
        print('order invalidd')
        form = OrderForm()

    customers = Customer.objects.all()
    return render(request, 'sales/create_order.html', {
        'form': form,
        'smoothies': smoothies,
        'customers': customers,
        'role': request.user.role,
    })