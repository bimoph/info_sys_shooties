from django.shortcuts import render
from .models import Customer
from .forms import CustomerForm
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from sales.models import Order
from customers.utils import find_customer_by_phone, normalize_phone  # import helper
from django.http import JsonResponse
from django.views.decorators.http import require_POST



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