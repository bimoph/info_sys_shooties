
import uuid

from django.db import models
from django.utils import timezone



class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_orders(self):
        return self.orders.all()

    def total_spent(self, start_date=None, end_date=None):
        orders = self.order_set.all()

        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        return sum(order.total_price for order in orders)

    # ── Shooties Passport ──────────────────────────────────────────────
    PASSPORT_GOAL = 5  # paid cups needed before the free cup unlocks

    def active_passport(self):
        """Return the customer's current (unclaimed) passport, creating one
        if none exists. Each customer holds exactly one active passport."""
        passport = self.passports.filter(free_claimed=False).order_by('created_at').first()
        if passport is None:
            passport = Passport.objects.create(customer=self)
        return passport

    def add_stamps(self, count):
        """Add `count` paid-cup stamps to the active passport, capped at the
        passport goal. Overflow beyond the goal is not carried over."""
        if count <= 0:
            return None
        passport = self.active_passport()
        passport.stamps = min(Customer.PASSPORT_GOAL, passport.stamps + count)
        passport.save(update_fields=['stamps'])
        return passport


class Passport(models.Model):
    """A Shooties Passport loyalty card: 5 paid stamps unlock 1 free cup."""

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='passports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    stamps = models.PositiveIntegerField(default=0)

    # Set when the customer taps "Claim" — encoded into the QR for the cashier.
    claim_uuid = models.UUIDField(null=True, blank=True, unique=True)

    free_claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(null=True, blank=True)
    claim_order = models.ForeignKey(
        'sales.Order', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='redeemed_passport',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Passport #{self.pk} — {self.customer.name} ({self.stamps}/{Customer.PASSPORT_GOAL})"

    @property
    def is_complete(self):
        return self.stamps >= Customer.PASSPORT_GOAL

    @property
    def can_claim(self):
        return self.is_complete and not self.free_claimed

    @property
    def stamp_range(self):
        """Helper for templates: list of (slot_number, is_stamped) for the
        5 paid slots."""
        return [(i, i <= self.stamps) for i in range(1, Customer.PASSPORT_GOAL + 1)]

    def generate_claim_uuid(self):
        """Generate (once) the claim UUID used to build the redemption QR."""
        if not self.claim_uuid:
            self.claim_uuid = uuid.uuid4()
            self.save(update_fields=['claim_uuid'])
        return self.claim_uuid

    def redeem(self, order):
        """Mark the free cup as claimed against `order`, then ensure the
        customer has a fresh active passport."""
        self.free_claimed = True
        self.claimed_at = timezone.now()
        self.claim_order = order
        self.save(update_fields=['free_claimed', 'claimed_at', 'claim_order'])
        # Start a new active passport for the next round.
        self.customer.active_passport()
