import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

class ChatSession(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def touch(self):
        """Update last_activity to current time"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def __str__(self):
        return f"Session {self.id} - {self.status}"

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price_cents = models.IntegerField()  # Price in cents
    image_url = models.URLField()
    category = models.CharField(max_length=100)
    
    def get_price_formatted(self):
        """Return formatted price as string"""
        price = self.price_cents / 100
        return f"${price:,.2f}"
    
    def __str__(self):
        return f"{self.sku} - {self.name}"

class CartItem(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['session', 'product']
    
    def get_total_cents(self):
        """Return total price for this cart item in cents"""
        return self.product.price_cents * self.quantity
    
    def get_total_formatted(self):
        """Return formatted total price as string"""
        total = self.get_total_cents() / 100
        return f"${total:,.2f}"
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Session: {self.session.id})"