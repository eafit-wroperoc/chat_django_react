from .models import Product

def seed_products():
    """Create sample products for the e-commerce chat demo"""
    products = [
        {
            'sku': 'ZAP-001',
            'name': 'Zapatillas Nike Air Max',
            'description': 'Zapatillas deportivas de alta calidad para running y uso casual',
            'price_cents': 15990000,  # $159,900.00
            'image_url': 'https://picsum.photos/300/300?random=1',
            'category': 'Calzado'
        },
        {
            'sku': 'CAM-002',
            'name': 'Camisa Polo Lacoste',
            'description': 'Camisa polo clásica de algodón 100% premium',
            'price_cents': 8990000,   # $89,900.00
            'image_url': 'https://picsum.photos/300/300?random=2',
            'category': 'Ropa'
        },
        {
            'sku': 'REL-003',
            'name': 'Reloj Casio G-Shock',
            'description': 'Reloj deportivo resistente al agua y golpes',
            'price_cents': 25990000,  # $259,900.00
            'image_url': 'https://picsum.photos/300/300?random=3',
            'category': 'Accesorios'
        },
        {
            'sku': 'AUD-004',
            'name': 'Audífonos Sony WH-1000XM4',
            'description': 'Audífonos inalámbricos con cancelación de ruido',
            'price_cents': 39990000,  # $399,900.00
            'image_url': 'https://picsum.photos/300/300?random=4',
            'category': 'Electrónicos'
        },
        {
            'sku': 'MOC-005',
            'name': 'Mochila Samsonite',
            'description': 'Mochila para laptop de 15" con compartimientos múltiples',
            'price_cents': 12990000,  # $129,900.00
            'image_url': 'https://picsum.photos/300/300?random=5',
            'category': 'Accesorios'
        },
        {
            'sku': 'PAN-006',
            'name': 'Pantalón Jeans Levis',
            'description': 'Pantalón jeans clásico corte recto talla 32',
            'price_cents': 6990000,   # $69,900.00
            'image_url': 'https://picsum.photos/300/300?random=6',
            'category': 'Ropa'
        }
    ]
    
    for product_data in products:
        product, created = Product.objects.get_or_create(
            sku=product_data['sku'],
            defaults=product_data
        )
        if created:
            print(f"Created product: {product.sku} - {product.name}")
        else:
            print(f"Product already exists: {product.sku} - {product.name}")
    
    print(f"Seed completed. Total products in database: {Product.objects.count()}")