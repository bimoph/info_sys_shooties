from django.shortcuts import render
from .models import Customer
from .forms import CustomerForm
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from sales.models import Order
from customers.utils import find_customer_by_phone, normalize_phone  # import helper
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie



@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-joined_at')
    return render(request, 'customers/customer_list.html', {'customers': customers, 'role': request.user.role,})

@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'customers/add_customer.html', {'form': form, 'role': request.user.role,})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.order_set.prefetch_related('orderitem_set__smoothie').all()
    return render(request, 'customers/customer_detail.html', {'customer': customer, 'orders': orders, 'role': request.user.role,})

@login_required
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer, 'role': request.user.role,})

@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customers/edit_customer.html', {'form': form, 'customer': customer, 'role': request.user.role,})


@login_required
def customer_orders(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    return render(request, 'customers/customer_orders.html', {
        'customer': customer,
        'orders': orders,
        'role': request.user.role,
    })


@login_required
def customer_spending_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    customers = Customer.objects.all()

    report_data = []
    for customer in customers:
        total = customer.total_spent(start_date, end_date)
        report_data.append({
            'name': customer.name,
            'phone': customer.phone,
            'total_spent': total,
            'pk': customer.pk,
        })

    report_data.sort(key=lambda x: x['total_spent'], reverse=True)

    return render(request, 'customers/customer_spending.html', {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'role': request.user.role,
    })


def register_customer(request):
    already_registered = False
    existing_customer = None

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        phone = request.POST.get('phone', '').strip()
        existing = find_customer_by_phone(phone)

        if existing:
            already_registered = True
            existing_customer = existing
        elif form.is_valid():
            customer = form.save()
            return redirect(f"{reverse('member_profile', args=[customer.phone])}?welcome=1")
    else:
        form = CustomerForm()

    return render(request, 'customers/register.html', {
        'form': form,
        'already_registered': already_registered,
        'existing_customer': existing_customer,
    })


@ensure_csrf_cookie
def member_profile(request, phone):
    customer = get_object_or_404(Customer, phone=phone)

    # Shooties Passport: active card (auto-created if none) + claimed history.
    active_passport = customer.active_passport()
    passport_history = customer.passports.filter(free_claimed=True).order_by('-claimed_at')

    orders = customer.order_set.prefetch_related('orderitem_set__smoothie').order_by('-created_at')

    total_orders = orders.count()
    total_spent = sum(o.total_price for o in orders)
    total_cups = sum(
        item.quantity
        for order in orders
        for item in order.orderitem_set.all()
    )

    def rupiah_compact(value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}jt"
        elif value >= 1_000:
            return f"{int(value / 1_000)}rb"
        return str(int(value))

    total_spent_formatted = rupiah_compact(total_spent)

    # ── Shareable stats ────────────────────────────────────────────────
    from collections import Counter
    from datetime import timedelta

    passports_redeemed = passport_history.count()

    week_ago = timezone.now() - timedelta(days=7)
    weekly_cups = 0
    drink_counter = Counter()
    for order in orders:
        for item in order.orderitem_set.all():
            drink_counter[item.smoothie.name] += item.quantity
            if order.created_at and order.created_at >= week_ago:
                weekly_cups += item.quantity

    if drink_counter:
        favorite_drink, favorite_drink_count = drink_counter.most_common(1)[0]
    else:
        favorite_drink, favorite_drink_count = None, 0

    avg_cup_price = (total_spent / total_cups) if total_cups else 0
    money_saved = int(round(avg_cup_price * passports_redeemed))
    money_saved_formatted = rupiah_compact(money_saved)

    member_url = request.build_absolute_uri(reverse('member_profile', args=[customer.phone]))

    return render(request, 'customers/member_profile.html', {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent_formatted': total_spent_formatted,
        'total_cups': total_cups,
        'welcome': request.GET.get('welcome') == '1',
        'member_url': member_url,
        'active_passport': active_passport,
        'passport_history': passport_history,
        'passport_goal': Customer.PASSPORT_GOAL,
        'passports_redeemed': passports_redeemed,
        'weekly_cups': weekly_cups,
        'favorite_drink': favorite_drink,
        'favorite_drink_count': favorite_drink_count,
        'money_saved_formatted': money_saved_formatted,
    })


# POST: /{phone}/passport/claim/  — customer taps "Claim", generates a claim UUID
@require_POST
def passport_claim(request, phone):
    customer = get_object_or_404(Customer, phone=phone)
    passport = customer.active_passport()
    if not passport.can_claim:
        return JsonResponse({'success': False, 'error': 'Passport not complete yet.'}, status=400)
    claim_uuid = passport.generate_claim_uuid()
    return JsonResponse({'success': True, 'claim_uuid': str(claim_uuid)})


# GET: /customers/passport/lookup/?uuid=...  — cashier scans the claim QR
@login_required
def passport_lookup(request):
    claim_uuid = request.GET.get('uuid', '').strip()
    if not claim_uuid:
        return JsonResponse({'valid': False, 'error': 'Missing UUID'}, status=400)

    from .models import Passport
    passport = Passport.objects.filter(claim_uuid=claim_uuid).select_related('customer').first()
    if not passport:
        return JsonResponse({'valid': False, 'error': 'Passport not found.'})
    if passport.free_claimed:
        return JsonResponse({'valid': False, 'error': 'This free cup was already claimed.'})
    if not passport.can_claim:
        return JsonResponse({'valid': False, 'error': 'Passport not complete yet.'})

    c = passport.customer
    return JsonResponse({
        'valid': True,
        'claim_uuid': claim_uuid,
        'customer_id': c.id,
        'name': c.name,
        'phone': c.phone,
    })


#### AJAX endpoints for customer management
# GET: /customers/check-phone/?phone=...
@login_required
def check_phone(request):
    phone = request.GET.get('phone', '').strip()
    existing = find_customer_by_phone(phone)
    if existing:
        return JsonResponse({'exists': True, 'id': existing.id, 'name': existing.name, 'phone': existing.phone})
    return JsonResponse({'exists': False})

# POST: /customers/create-ajax/  (expects form fields 'name' and 'phone')
@login_required
@require_POST
def create_customer_ajax(request):
    name = request.POST.get('name', '').strip()
    phone = request.POST.get('phone', '').strip()
    if not name or not phone:
        return JsonResponse({'success': False, 'error': 'Missing name or phone'}, status=400)

    existing = find_customer_by_phone(phone)
    if existing:
        # Don't create duplicate — return existing information
        return JsonResponse({'success': True, 'created': False, 'id': existing.id, 'name': existing.name, 'phone': existing.phone})

    # create new customer
    customer = Customer.objects.create(name=name, phone=phone)
    return JsonResponse({'success': True, 'created': True, 'id': customer.id, 'name': customer.name, 'phone': customer.phone})