from django.contrib import admin
from .models import ChatSession, Product, CartItem

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'last_activity', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['id', 'created_at', 'last_activity']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'get_price_formatted']
    list_filter = ['category']
    search_fields = ['sku', 'name', 'category']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['session', 'product', 'quantity', 'get_total_formatted']
    list_filter = ['product__category']