import re
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.urls import reverse
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import ChatSession, Product, CartItem
from .serializers import (
    SessionCreateSerializer, 
    MessageRequestSerializer, 
    MessageResponseSerializer,
    HeartbeatRequestSerializer,
    ProductSerializer,
    CartItemSerializer
)

TIMEOUT_MINUTES = 5

def is_expired(session):
    """Check if a session has expired based on inactivity"""
    expiry_time = session.last_activity + timedelta(minutes=TIMEOUT_MINUTES)
    return timezone.now() > expiry_time


@api_view(['POST'])
@permission_classes([AllowAny])
def create_session(request):
    """Create a new chat session"""
    session = ChatSession.objects.create()
    
    intro_message = (
        "¡Hola! Soy tu asistente de compras. Puedo ayudarte con:\n"
        "• 'ver ofertas' - Ver productos destacados\n"
        "• 'buscar [producto]' - Buscar productos\n"
        "• 'agregar [SKU] x2' - Agregar al carrito\n"
        "• 'carrito' - Ver tu carrito\n"
        "• 'pagar' - Proceder al pago\n\n"
        "¿En qué puedo ayudarte hoy?"
    )
    
    data = {
        'session_id': str(session.id),
        'timeout_minutes': TIMEOUT_MINUTES,
        'message': intro_message
    }
    
    return Response(data)

@api_view(['POST'])
@permission_classes([AllowAny])
def heartbeat(request):
    """Keep session alive with heartbeat"""
    serializer = HeartbeatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data['session_id']
    
    try:
        session = ChatSession.objects.get(id=session_id, status='OPEN')
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if is_expired(session):
        session.status = 'CLOSED'
        session.save()
        return Response({'error': 'Session expired'}, status=status.HTTP_410_GONE)
    
    session.touch()
    return Response({'ok': True})

@api_view(['POST'])
@permission_classes([AllowAny])
def process_message(request):
    """Process chat message and return appropriate response"""
    serializer = MessageRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data['session_id']
    message = serializer.validated_data['message'].strip().lower()
    
    try:
        session = ChatSession.objects.get(id=session_id, status='OPEN')
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if is_expired(session):
        session.status = 'CLOSED'
        session.save()
        return Response({'error': 'Session expired'}, status=status.HTTP_410_GONE)
    
    session.touch()
    
    response_data = {
        'reply': '',
        'products': None,
        'cart': None,
        'payment_link': None
    }
    
    # Intent: ver ofertas
    if message == 'ver ofertas':
        products = Product.objects.all()[:4]  # Top 4 products
        response_data['reply'] = '🏷️ Aquí tienes nuestras ofertas destacadas:'
        response_data['products'] = ProductSerializer(products, many=True).data
    
    # Intent: buscar <query>
    elif message.startswith('buscar '):
        query = message[7:].strip()  # Remove 'buscar '
        if query:
            products = Product.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(category__icontains=query) |
                models.Q(sku__icontains=query)
            )[:8]
            
            if products:
                response_data['reply'] = f'🔍 Encontré {products.count()} producto(s) para "{query}":'
                response_data['products'] = ProductSerializer(products, many=True).data
            else:
                response_data['reply'] = f'😔 No encontré productos para "{query}". Intenta con otro término de búsqueda.'
        else:
            response_data['reply'] = 'Por favor especifica qué producto quieres buscar. Ejemplo: "buscar zapatillas"'
    
    # Intent: agregar <SKU> [xN]
    elif message.startswith('agregar '):
        add_text = message[8:].strip()  # Remove 'agregar '
        
        # Parse quantity (x2, ×2, etc.)
        quantity = 1
        qty_match = re.search(r'[x×]\s*(\d+)', add_text)
        if qty_match:
            quantity = int(qty_match.group(1))
            add_text = re.sub(r'\s*[x×]\s*\d+', '', add_text).strip()
        
        sku = add_text.upper()
        
        try:
            product = Product.objects.get(sku=sku)
            cart_item, created = CartItem.objects.get_or_create(
                session=session,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            response_data['reply'] = f'✅ Agregado al carrito: {quantity}x {product.name} ({product.get_price_formatted()} c/u)'
            cart_items = CartItem.objects.filter(session=session).select_related('product')
            response_data['cart'] = {
                'items': CartItemSerializer(cart_items, many=True).data,
                'total': f"${sum(item.get_total_cents() for item in cart_items) / 100:,.2f}"
            }
            
        except Product.DoesNotExist:
            response_data['reply'] = f'❌ Producto con SKU "{sku}" no encontrado. Usa "ver ofertas" para ver productos disponibles.'
    
    # Intent: carrito
    elif message == 'carrito':
        cart_items = CartItem.objects.filter(session=session)
        if cart_items.exists():
            response_data['reply'] = '🛒 Tu carrito actual:'
            response_data['cart'] = {
                'items': CartItemSerializer(cart_items, many=True).data,
                'total': f"${sum(item.get_total_cents() for item in cart_items) / 100:,.2f}"
            }
        else:
            response_data['reply'] = '🛒 Tu carrito está vacío. Usa "ver ofertas" para explorar productos.'
    
    # Intent: pagar/checkout/pago
    elif message in ['pagar', 'checkout', 'pago']:
        cart_items = CartItem.objects.filter(session=session)
        if cart_items.exists():
            payment_url = request.build_absolute_uri(
                reverse('chat_dummy_pay', kwargs={'session_id': session.id})
            )
            response_data['reply'] = '💳 Tu enlace de pago está listo:'
            response_data['payment_link'] = payment_url
            cart_items = CartItem.objects.filter(session=session).select_related('product')
            response_data['cart'] = {
                'items': CartItemSerializer(cart_items, many=True).data,
                'total': f"${sum(item.get_total_cents() for item in cart_items) / 100:,.2f}"
            }
        else:
            response_data['reply'] = '🛒 Tu carrito está vacío. Agrega productos antes de proceder al pago.'
    
    # Fallback: try search or show help
    else:
        # Try to search with the message as query
        products = Product.objects.filter(
            models.Q(name__icontains=message) |
            models.Q(category__icontains=message)
        )[:3]
        
        if products:
            response_data['reply'] = f'🔍 ¿Te refieres a alguno de estos productos?'
            response_data['products'] = ProductSerializer(products, many=True).data
        else:
            response_data['reply'] = (
                '🤔 No entiendo tu mensaje. Puedo ayudarte con:\n'
                '• "ver ofertas" - Ver productos destacados\n'
                '• "buscar zapatillas" - Buscar productos\n'
                '• "agregar ZAP-001 x2" - Agregar al carrito\n'
                '• "carrito" - Ver tu carrito\n'
                '• "pagar" - Proceder al pago'
            )
    
    # Remove None values from response
    response_data = {k: v for k, v in response_data.items() if v is not None}
    
    return Response(response_data)

def dummy_payment_page(request, session_id):
    """Dummy payment page for demo"""
    try:
        session = ChatSession.objects.get(id=session_id)
        cart_items = CartItem.objects.filter(session=session).select_related('product')
        
        if not cart_items.exists():
            return HttpResponse("No hay items en el carrito para esta sesión.", status=404)
        
        cart_data = {
            'items': CartItemSerializer(cart_items, many=True).data,
            'total': f"${sum(item.get_total_cents() for item in cart_items) / 100:,.2f}"
        }
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Página de Pago - Demo</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .header {{ text-align: center; color: #2c3e50; }}
                .cart-summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .item {{ padding: 10px 0; border-bottom: 1px solid #ddd; }}
                .total {{ font-size: 1.5em; font-weight: bold; color: #e74c3c; text-align: right; margin-top: 15px; }}
                .demo-notice {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .btn {{ background: #3498db; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 1.1em; cursor: not-allowed; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛒 Página de Pago</h1>
                <p>Sesión: {session_id}</p>
            </div>
            
            <div class="cart-summary">
                <h2>Resumen de tu pedido:</h2>
        """
        
        for item in cart_data['items']:
            html += f"""
                <div class="item">
                    <strong>{item['name']}</strong> (SKU: {item['sku']})<br>
                    Cantidad: {item['quantity']} - Subtotal: {item['price_total']}
                </div>
            """
        
        html += f"""
                <div class="total">Total a pagar: {cart_data['total']}</div>
            </div>
            
            <div class="demo-notice">
                <strong>⚠️ DEMO:</strong> Esta es una página de pago de demostración. 
                En un entorno real, aquí se integraría con un procesador de pagos 
                como Stripe, PayPal, o la pasarela de pago de tu preferencia.
            </div>
            
            <div style="text-align: center;">
                <button class="btn">Procesar Pago (Demo)</button>
                <p><small>Este botón no procesa pagos reales</small></p>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html)
        
    except ChatSession.DoesNotExist:
        return HttpResponse("Sesión no encontrada.", status=404)