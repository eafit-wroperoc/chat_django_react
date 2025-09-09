from rest_framework import serializers
from .models import ChatSession, Product, CartItem

class ProductSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['sku', 'name', 'price', 'image_url', 'category']
    
    def get_price(self, obj):
        return obj.get_price_formatted()

class CartItemSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source='product.sku', read_only=True)
    name = serializers.CharField(source='product.name', read_only=True)
    price_total = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['sku', 'name', 'quantity', 'price_total']
    
    def get_price_total(self, obj):
        return obj.get_total_formatted()

class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total = serializers.CharField()

class SessionCreateSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(source='id', read_only=True)
    timeout_minutes = serializers.IntegerField(read_only=True)
    message = serializers.CharField(read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['session_id', 'timeout_minutes', 'message']

class MessageRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    message = serializers.CharField(max_length=500)

class HeartbeatRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()

class MessageResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    products = ProductSerializer(many=True, required=False)
    cart = CartSerializer(required=False)
    payment_link = serializers.URLField(required=False)