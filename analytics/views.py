# analytics/views.py
from collections import defaultdict
import json
from datetime import datetime, date, time, timedelta
import pytz

from django.shortcuts import render
from django.db.models import Sum
from sales.models import Order, OrderItem
from inventory.models import SmoothieMenu, Ingredient, StockEntry
from core.decorators import role_required
from django.contrib.auth.decorators import login_required


@login_required
@role_required(['admin', 'manager'])
def analytics_dashboard(request):
    jakarta = pytz.timezone("Asia/Jakarta")

    # --- Filters from request ---
    start_date = request.GET.get('start_date')  # YYYY-MM-DD or None
    end_date = request.GET.get('end_date')
    menu_ids = request.GET.getlist('menu')  # list of ids as strings
    time_division = request.GET.get('time_division')  # morning/lunch/after_lunch/afternoon

    # --- Base queryset filtered by date & menu (DB-level) ---
    orders_qs = Order.objects.filter(store=request.user.store)
    if start_date:
        orders_qs = orders_qs.filter(created_at__date__gte=start_date)
    if end_date:
        orders_qs = orders_qs.filter(created_at__date__lte=end_date)
    if menu_ids:
        orders_qs = orders_qs.filter(list_menu__id__in=menu_ids).distinct()

    # Evaluate queryset into list so we can do timezone-aware time filtering in Python
    orders_list = list(orders_qs)

    # --- Time division filter (apply in Python using Jakarta local time) ---
    if time_division:
        time_ranges = {
            'morning': (time(9, 0), time(11, 0)),
            'lunch': (time(11, 0), time(13, 0)),
            'after_lunch': (time(13, 0), time(15, 0)),
            'afternoon': (time(15, 0), time(18, 0)),
        }
        if time_division in time_ranges:
            start_t, end_t = time_ranges[time_division]
            filtered = []
            for o in orders_list:
                # created_at may be timezone-aware; astimezone handles naive vs aware safely
                local_dt = o.created_at.astimezone(jakarta)
                if start_t <= local_dt.time() < end_t:
                    filtered.append(o)
            orders_list = filtered

    order_ids = [o.id for o in orders_list]

    # --- Fetch related order items for these orders ---
    order_items_qs = OrderItem.objects.filter(order_id__in=order_ids).select_related('order', 'smoothie')

    # --- Daily sales (Rp) and daily cups (grouped by Jakarta local date) ---
    sales_by_date = defaultdict(int)
    cups_by_date = defaultdict(int)

    for o in orders_list:
        local_date = o.created_at.astimezone(jakarta).date()
        sales_by_date[local_date] += o.total_price

    for item in order_items_qs:
        local_date = item.order.created_at.astimezone(jakarta).date()
        cups_by_date[local_date] += item.quantity

    # union of dates, sorted
    all_dates = sorted(set(list(sales_by_date.keys()) + list(cups_by_date.keys())))
    sales_labels = [d.strftime('%Y-%m-%d') for d in all_dates]
    sales_data_rp = [sales_by_date.get(d, 0) for d in all_dates]
    cups_data = [cups_by_date.get(d, 0) for d in all_dates]

    # --- Menu sales percentage (pie) ---
    menu_agg = (
        order_items_qs
        .values('smoothie__name')
        .annotate(total=Sum('quantity'))
        .order_by('-total')
    )
    menu_labels = [m['smoothie__name'] for m in menu_agg]
    menu_cups = [m['total'] for m in menu_agg]

    # --- Payment method breakdown (sum of total_price per method) ---
    payment_agg = (
        Order.objects
        .filter(id__in=order_ids)
        .values('payment_method')
        .annotate(total=Sum('total_price'))
    )
    payment_labels = [p['payment_method'] for p in payment_agg]
    payment_totals = [p['total'] for p in payment_agg]

    # --- Cups sold by time division (use Jakarta local times) ---
    divisions = {
        'Morning (09-11)': (time(9, 0), time(11, 0)),
        'Lunch (11-13)': (time(11, 0), time(13, 0)),
        'After Lunch (13-15)': (time(13, 0), time(15, 0)),
        'Afternoon (15-18)': (time(15, 0), time(18, 0)),
    }
    division_labels = list(divisions.keys())
    division_cups = []
    for start_t, end_t in divisions.values():
        count = 0
        for item in order_items_qs:
            local_time = item.order.created_at.astimezone(jakarta).time()
            if start_t <= local_time < end_t:
                count += item.quantity
        division_cups.append(count)

    # --- JSON-encode lists for Chart.js usage in template ---
    ctx = {
        'menus': SmoothieMenu.objects.all(),
        'selected_menus': menu_ids,
        'sales_labels': json.dumps(sales_labels),
        'sales_data_rp': json.dumps(sales_data_rp),
        'cups_data': json.dumps(cups_data),
        'menu_labels': json.dumps(menu_labels),
        'menu_cups': json.dumps(menu_cups),
        'payment_labels': json.dumps(payment_labels),
        'payment_totals': json.dumps(payment_totals),
        'division_labels': json.dumps(division_labels),
        'division_cups': json.dumps(division_cups),
        'time_division_selected': time_division or "",
        'start_date': start_date or "",
        'end_date': end_date or "",
    }
    return render(request, 'analytics/dashboard.html', ctx)








## Operations dashboard:
JKT = pytz.timezone("Asia/Jakarta")


def parse_date_param(s):
    """Return date object or None."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

@login_required
@role_required(['admin', 'manager'])
def operations_dashboard(request):
    """
    Operations dashboard:
    - Filters for orders: start_date, end_date, menu (list), time_division
    - Independent stock snapshot date: stock_date (used only for stock cards, snapshot at 23:00 Jakarta)
    """

    # --- Parse filter inputs ---
    start_date = parse_date_param(request.GET.get('start_date'))
    end_date = parse_date_param(request.GET.get('end_date'))
    menu_ids = request.GET.getlist('menu')               # list of strings
    time_division = request.GET.get('time_division')    # morning/lunch/after_lunch/afternoon

    # Stock snapshot date (independent)
    stock_date = parse_date_param(request.GET.get('stock_date'))
    if stock_date is None:
        stock_date = datetime.now(JKT).date()

    # --- Build base orders queryset based on DB filters (date & menu) ---
    orders_qs = Order.objects.filter(store=request.user.store)
    if start_date:
        orders_qs = orders_qs.filter(created_at__date__gte=start_date)
    if end_date:
        orders_qs = orders_qs.filter(created_at__date__lte=end_date)
    if menu_ids:
        orders_qs = orders_qs.filter(list_menu__id__in=menu_ids).distinct()

    # evaluate to list for accurate Jakarta-local time filtering
    orders_list = list(orders_qs.select_related('customer'))

    # --- Apply time division filter in Python using Jakarta local time ---
    if time_division:
        time_ranges = {
            'morning': (time(9, 0), time(11, 0)),
            'lunch': (time(11, 0), time(13, 0)),
            'after_lunch': (time(13, 0), time(15, 0)),
            'afternoon': (time(15, 0), time(18, 0)),
        }
        if time_division in time_ranges:
            start_t, end_t = time_ranges[time_division]
            filtered = []
            for o in orders_list:
                try:
                    local_dt = o.created_at.astimezone(JKT)
                except Exception:
                    # fallback: assume naive created_at is already Jakarta local
                    local_dt = JKT.localize(o.created_at) if o.created_at.tzinfo is None else o.created_at
                if start_t <= local_dt.time() < end_t:
                    filtered.append(o)
            orders_list = filtered

    order_ids = [o.id for o in orders_list]

    # --- KPI calculations (Jakarta local times) ---
    ready_durations = []           # seconds: ready_at - created_at
    served_from_ready = []         # seconds: served_at - ready_at
    served_from_created = []       # seconds: served_at - created_at

    for o in orders_list:
        try:
            created_local = o.created_at.astimezone(JKT)
        except Exception:
            created_local = JKT.localize(o.created_at) if o.created_at.tzinfo is None else o.created_at

        if o.ready_at:
            try:
                ready_local = o.ready_at.astimezone(JKT)
            except Exception:
                ready_local = JKT.localize(o.ready_at) if o.ready_at.tzinfo is None else o.ready_at
            ready_durations.append((ready_local - created_local).total_seconds())

        if o.ready_at and o.served_at:
            try:
                ready_local = o.ready_at.astimezone(JKT)
                served_local = o.served_at.astimezone(JKT)
            except Exception:
                ready_local = JKT.localize(o.ready_at) if o.ready_at.tzinfo is None else o.ready_at
                served_local = JKT.localize(o.served_at) if o.served_at.tzinfo is None else o.served_at
            served_from_ready.append((served_local - ready_local).total_seconds())

        if o.served_at:
            try:
                served_local = o.served_at.astimezone(JKT)
            except Exception:
                served_local = JKT.localize(o.served_at) if o.served_at.tzinfo is None else o.served_at
            served_from_created.append((served_local - created_local).total_seconds())

    def avg_seconds(lst):
        return (sum(lst) / len(lst)) if lst else 0

    avg_ready_sec = avg_seconds(ready_durations)
    avg_served_from_ready_sec = avg_seconds(served_from_ready)
    avg_served_from_created_sec = avg_seconds(served_from_created)

    def sec_to_minutes_display(sec):
        if not sec:
            return "—"
        return f"{(sec / 60.0):.2f} min"

    avg_ready_display = sec_to_minutes_display(avg_ready_sec)
    avg_served_from_ready_display = sec_to_minutes_display(avg_served_from_ready_sec)
    avg_served_from_created_display = sec_to_minutes_display(avg_served_from_created_sec)

    # numeric values in minutes for chart
    duration_chart_labels = ["Ready from Created", "Served from Ready", "Served from Created"]
    duration_chart_values = [
        round(avg_ready_sec / 60.0, 2),
        round(avg_served_from_ready_sec / 60.0, 2),
        round(avg_served_from_created_sec / 60.0, 2),
    ]

    # --- Stock snapshot at stock_date 23:00 Jakarta (independent of order filters) ---
    # compute snapshot datetime in Jakarta tz
    snapshot_dt_naive = datetime.combine(stock_date, time(23, 0))
    # make timezone-aware in JKT
    try:
        snapshot_dt = JKT.localize(snapshot_dt_naive)
    except Exception:
        snapshot_dt = snapshot_dt_naive.replace(tzinfo=JKT)

    # We'll compute stock at snapshot by taking current ingredient.quantity_in_stock
    # and subtract net of entries that occurred AFTER snapshot (i.e., future changes).
    # This assumes StockEntry.quantity is always positive and reason determines sign.
    add_reasons = {'manual_add', 'sale_cancellation'}
    deduct_reasons = {'manual_deduct', 'sale_deduct'}

    ingredient_cards = []
    for ing in Ingredient.objects.filter(store=request.user.store).order_by('name'):
        future_entries = StockEntry.objects.filter(ingredient=ing, timestamp__gt=snapshot_dt, store=request.user.store)
        future_net = 0.0
        for e in future_entries:
            q = e.quantity or 0.0
            if e.reason in add_reasons:
                future_net += q
            elif e.reason in deduct_reasons:
                future_net -= q
            else:
                future_net += q  # default: treat as addition if unknown

        # current stock minus future net changes gives stock at snapshot
        stock_at_snapshot = ing.quantity_in_stock - future_net
        ingredient_cards.append({
            'id': ing.id,
            'name': ing.name,
            'unit': ing.unit,
            'stock_at_snapshot': round(stock_at_snapshot, 3),
        })

    # --- Context for template ---
    context = {
        'menus': SmoothieMenu.objects.all(),
        'selected_menus': menu_ids,
        'start_date': start_date.isoformat() if start_date else "",
        'end_date': end_date.isoformat() if end_date else "",
        'time_division_selected': time_division or "",
        'stock_date': stock_date.isoformat(),
        # KPI displays
        'avg_ready_display': avg_ready_display,
        'avg_served_from_ready_display': avg_served_from_ready_display,
        'avg_served_from_created_display': avg_served_from_created_display,
        # chart data (JSON-encoded)
        'duration_chart_labels': json.dumps(duration_chart_labels),
        'duration_chart_values': json.dumps(duration_chart_values),
        # stock cards
        'ingredient_cards': ingredient_cards,
    }

    return render(request, 'analytics/operations_dashboard.html', context)