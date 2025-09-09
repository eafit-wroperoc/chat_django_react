# Chat-Based E-Commerce Assistant

A complete demo project featuring a chat-based e-commerce assistant built with Django REST Framework backend and React frontend.

## Features

- **Chat Interface**: Interactive chat widget for customer support
- **Product Management**: Search and browse products by category, name, or SKU
- **Shopping Cart**: Add items to cart with quantity support
- **Payment Flow**: Dummy payment page integration
- **Session Management**: Automatic session handling with inactivity timeout
- **Heartbeat System**: Keep-alive mechanism to maintain active sessions
- **Django REST Framework**: Uses proper serializers and API structure

## Tech Stack

### Backend
- **Django 4.2+**: Web framework
- **Django REST Framework**: API development with serializers
- **django-cors-headers**: CORS handling
- **SQLite**: Database (default)

### Frontend
- **React 18+**: UI framework
- **react-chat-widget**: Chat interface component
- **Axios**: HTTP client for API communication

# Proyecto
Este proyecto está diseñado para enseñar a crear una experiencia de e-commerce guiada por chat usando un backend en Django REST y un frontend en React.

- Cómo modelar datos de e-commerce (Productos, Carrito, Sesiones de chat) en Django.
- Cómo crear endpoints REST con serializadores en DRF y consumirlos desde React con Axios.
- Cómo integrar un widget de chat (react-chat-widget) y manejar estados como sesión activa, heartbeat y expiración.
- Cómo depurar problemas comunes de integración (CORS, dependencias NPM/Python, doble inicialización en React 18).

### Componentes principales del proyecto

- Backend (Django, carpeta `backend/`)
  - `chat/models.py`: define `Product`, `CartItem` y `ChatSession` (UUID, inactividad y cierre automático).
  - `chat/serializers.py`: transforma datos entre modelos y JSON para la API.
  - `chat/views.py`: lógica principal de intents del chat: "ver ofertas", "buscar ...", "agregar SKU xN", "carrito", "pagar" y latido (heartbeat).
  - `chat/urls.py`: rutas de API (`/api/chat/session`, `/message`, `/heartbeat`).
  - `chat/payment_urls.py`: ruta `/pay/<session_id>/` para una página de pago DEMO (HTML simple).
  - `chat/seed.py`: script para sembrar productos de ejemplo.
  - `mysite/settings.py`: configuración de Django (CORS habilitado para `http://localhost:3000`).

- Frontend (React, carpeta `frontend/`)
  - `src/App.js`: integra `react-chat-widget`, crea la sesión, envía mensajes, muestra productos/carrito y gestiona heartbeat/expiración.
  - `src/index.js`: arranque de React (sin `StrictMode` en dev para evitar doble-mount).
  - `public/index.html`: HTML base.

### Mejoras recientes para estabilidad (importante)

- React StrictMode desactivado en desarrollo para evitar doble inicialización del widget (React 18 monta dos veces en dev).
- Inicialización protegida: el widget se abre una sola vez y la sesión se crea una sola vez para evitar ráfagas de peticiones.
- Se eliminó el launcher personalizado del chat para no tapar el botón de enviar; se usa el launcher nativo del widget.

## Flujo de Comunicación y Arquitectura

### ¿Cómo se comunica el chat con el backend?

Este proyecto usa una API REST sobre HTTP. No utiliza WebSockets. La comunicación es petición/respuesta:

1) Inicialización
   - El frontend abre el widget y hace un POST a `/api/chat/session/` para crear una sesión (`session_id`) y recibir el mensaje de bienvenida.

2) Envío de mensajes del usuario
   - Cada vez que el estudiante escribe en el chat, el frontend hace un POST a `/api/chat/message/` con `{ session_id, message }`.
   - El backend procesa el intent (ver ofertas, buscar, agregar, carrito, pagar) y responde con un JSON que puede incluir:
     - `reply` (texto), `products` (lista), `cart` (resumen), `payment_link` (URL demo).
   - El frontend renderiza la respuesta y, si hay productos o carrito, los muestra como componentes.

3) Mantener la sesión viva (Heartbeat)
   - Cada 60 segundos, si la ventana está activa, el frontend envía un POST a `/api/chat/heartbeat/` con `{ session_id }`.
   - El backend actualiza `last_activity` de la sesión. Si han pasado más de 5 minutos sin actividad, la sesión se marca como expirada (`CLOSED`).
   - Si el backend responde 410 (Gone), el frontend crea automáticamente una nueva sesión para que el alumno siga trabajando.

4) Pago (Demo)
   - Si el intent es "pagar", el backend genera un enlace a `/pay/<session_id>/` con un resumen HTML del carrito (no procesa pagos reales).

### ¿Por qué REST y no WebSockets?

- Objetivo educativo: REST es más simple para enseñar conceptos de API, serialización (DRF) y consumo desde React con Axios.
- Latencia aceptable: el flujo de chat no requiere actualización en tiempo real desde el servidor hacia el cliente (push). El usuario inicia todas las acciones.
- Sencillez operativa: evita la complejidad de configurar ASGI + Channels y el manejo de conexiones persistentes.

Si se quisiera usar WebSockets en el futuro (para typing indicators, mensajes push, multiusuario en tiempo real), se podría integrar Django Channels y un `<WebSocket>` o `socket.io` en el frontend.

### ¿Para qué sirve el Heartbeat?

- Mantener viva la sesión: actualiza `last_activity` en el backend cuando el alumno tiene el chat abierto y activo.
- Expiración automática: si no hay heartbeat ni mensajes durante 5 minutos, la sesión expira y el backend limpia estado.
- Experiencia estable: si el backend responde que la sesión expiró (410), el frontend crea una nueva sesión y continúa sin errores.

### Diagrama de Arquitectura (alto nivel)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (React)                          │
│  - react-chat-widget                                                │
│  - Axios                                                            │
│                                                                     │
│  [1] POST /api/chat/session   ──────────────────────────────►       │
│  [2] POST /api/chat/message   ──────────────────────────────►       │
│  [3] POST /api/chat/heartbeat ──────────────────────────────►       │
│  [4] Abrir /pay/<session_id> (GET) ─────────────────────────►       │
└─────────────────────────────────────────────────────────────────────┘
                                   │ HTTP (REST)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend (Django + DRF)                        │
│  Views (chat/views.py):                                              │
│   - create_session()  (/api/chat/session/)                           │
│   - process_message() (/api/chat/message/)                           │
│   - heartbeat()       (/api/chat/heartbeat/)                         │
│   - dummy_payment_page() (/pay/<session_id>/)                        │
│                                                                     │
│  Serializers: validación y formato (JSON)                            │
│  Models: ChatSession, Product, CartItem                              │
│  DB: SQLite                                                          │
└─────────────────────────────────────────────────────────────────────┘
```

Flujo resumido: React crea sesión -> el alumno envía mensajes -> DRF responde con texto/productos/carrito/enlace de pago -> React renderiza la respuesta -> heartbeat mantiene la sesión.

### REST vs WebSockets: ¿cuándo usar cada uno?

REST (petición/respuesta)
- Ideal cuando el cliente inicia cada acción: formularios, búsquedas, comandos puntuales del usuario.
- Simplicidad: fácil de aprender, depurar (Network tab), cacheable, stateless.
- Escala bien con balanceadores HTTP y CDNs.
- Ejemplos típicos: CRUD de productos, checkout, autenticación, este chat “por turnos”.

WebSockets (conexión persistente)
- Comunicación bidireccional en tiempo real: el servidor puede “empujar” eventos sin que el cliente pregunte.
- Útil para latencia muy baja y alta frecuencia de eventos.
- Más complejidad: requiere ASGI (Django Channels), gestión de conexiones, escalado distinto.
- Ejemplos típicos: chats multiusuario con mensajes push, notificaciones live, colaboraciones en tiempo real, dashboards de trading.

Reglas prácticas para decidir
- Usa REST cuando:
  - El flujo es iniciado por el usuario y la latencia de 1 petición por acción es aceptable.
  - Quieres mantener el backend simple y fácil de desplegar.
  - No necesitas eventos push desde el servidor.
- Considera WebSockets cuando:
  - Necesitas que el servidor envíe mensajes en tiempo real sin que el usuario interactúe (notificaciones, typing indicators, presencia).
  - Tienes múltiples clientes interactuando simultáneamente y la experiencia debe ser síncrona (salas de chat, pizarras en vivo).
  - Requieres latencia muy baja y alto throughput de eventos.

Cómo evolucionar este proyecto a WebSockets (a alto nivel)
- Backend: agregar Django Channels (ASGI), definir consumidores para eventos de chat, administrar grupos/salas por sesión.
- Frontend: reemplazar las llamadas Axios puntuales por un cliente WebSocket (nativo, socket.io, o similar) para enviar/recibir mensajes.
- Mantener REST para operaciones idempotentes/lentas (CRUD, catálogo) y usar WebSockets para eventos de chat en vivo.

## ¿Cómo funciona el chat widget (react-chat-widget)?

Este proyecto usa el componente `Widget` de `react-chat-widget` para renderizar el chat flotante y sus mensajes.

Documentación oficial:
- GitHub: https://github.com/Wolox/react-chat-widget
- npm: https://www.npmjs.com/package/react-chat-widget

APIs clave que usamos
- `<Widget handleNewUserMessage={fn} />`: componente principal del chat. `handleNewUserMessage` se ejecuta cuando el usuario envía un mensaje.
- `addResponseMessage(text)`: agrega un mensaje del “bot” al hilo.
- `addUserMessage(text)`: agrega un mensaje del usuario (lo usamos en botones rápidos).
- `renderCustomComponent(Component, props)`: inserta un componente React dentro del chat (lo usamos para tarjetas de productos y resumen de carrito).
- `addLinkSnippet({ title, link, target })`: muestra un enlace (lo usamos para el link de pago).
- `dropMessages()`: borra el historial del chat (se usa al crear una nueva sesión).
- `toggleWidget()`: abre/cierra el widget (lo usamos una sola vez en el inicio, con guarda para no duplicar).

Ciclo de vida en `src/App.js`
1) Montaje: abrimos el widget una sola vez (guardado con `initializedRef`), luego creamos la sesión vía `/api/chat/session/`.
2) Heartbeat: cada 60s, si la ventana está activa, mandamos `/api/chat/heartbeat/` con el `session_id`.
3) Mensajes: cuando el usuario escribe, enviamos `/api/chat/message/` y, según la respuesta, mostramos texto, productos, carrito y/o enlace de pago.
4) Expiración: si el backend responde 410, mostramos aviso y creamos una nueva sesión automáticamente.

Buenas prácticas implementadas
- Sin `React.StrictMode` en desarrollo para evitar doble montaje (que duplicaba timers y causaba aperturas tardías del widget).
- Guardas de inicialización (`initializedRef`) para que los efectos corran solo una vez.
- Uso del launcher nativo del widget para evitar que un botón personalizado tape el botón de enviar dentro del chat.
- Mensajes esperan una sesión activa: `createSession()` devuelve el `session_id` y `handleNewUserMessage` lo espera si hace falta, evitando ráfagas de peticiones posteriores.

Problemas comunes y cómo resolverlos
- “El widget abre tarde / se abre dos veces”: causado por doble-mount en React 18. Solución: quitar StrictMode en dev y agregar guardas.
- “No se ven mensajes hasta que hago clic en emojis”: se estaban encolando sin sesión activa. Solución: esperar `createSession()` y luego enviar.
- “El botón flotante tapa el botón de enviar”: usar el launcher nativo del widget o ajustar estilos/Z-index.
- “CORS o 404/500”: verificar que el backend esté en `http://localhost:8000` y que los endpoints existan; revisar consola/Network del navegador.

## Pasos por Sistema Operativo (Backend y Frontend)

Sigue estos pasos según tu sistema. Si es tu primera vez, lee completo y avanza paso a paso.

### Requisitos previos
- macOS: Python 3 instalado (prueba `python3 --version`), Node 16+ y npm, git.
- Windows: Python 3 (prueba `py --version`), Node 16+ y npm, git. Activa ejecución de scripts si es necesario.

### Backend (macOS / Linux)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py shell -c "from chat.seed import seed_products; seed_products()"
python3 manage.py runserver 8000
```
Backend en: http://localhost:8000/

### Backend (Windows)
```bat
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py manage.py migrate
py manage.py shell -c "from chat.seed import seed_products; seed_products()"
py manage.py runserver 8000
```
Backend en: http://localhost:8000/

### Frontend (macOS / Linux / Windows)
Usa otra terminal:
```bash
cd frontend
npm install
npm start
```
Frontend en: http://localhost:3000/

Notas:
- Si `npm install` muestra conflictos de dependencias, intenta con `npm install --legacy-peer-deps`.
- Si ves el chat que no responde, confirma que el backend esté corriendo y que los endpoints devuelvan 200.

## Quick Start

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create and run migrations**:
   ```bash
   python manage.py makemigrations chat
   python manage.py migrate
   ```

5. **Seed sample products**:
   ```bash
   python manage.py shell -c "from chat.seed import seed_products; seed_products(); print('Products seeded successfully!')"
   ```

6. **Start Django development server**:
   ```bash
   python manage.py runserver 8000
   ```

The backend API will be available at `http://localhost:8000/`

### Frontend Setup

1. **Navigate to frontend directory** (in a new terminal):
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies** (use legacy peer deps to resolve React version conflicts):
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Fix AJV dependency issue**:
   ```bash
   npm install ajv@latest --legacy-peer-deps
   ```

4. **Start React development server**:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000/` and should automatically open in your browser.

### Troubleshooting

**If you get dependency conflicts during npm install:**
- Use `--legacy-peer-deps` flag with npm install
- If React chat widget conflicts with React 18, this is expected and should work fine

**If the database table errors occur:**
- Make sure to run `python manage.py makemigrations chat` before `migrate`
- Ensure the virtual environment is activated before running Django commands

**If the AJV codegen error occurs:**
- Run `npm install ajv@latest --legacy-peer-deps` to fix the compilation issue

## Usage Guide

### Chat Commands

The chat assistant recognizes these intents:

- **`ver ofertas`** - Display featured products
- **`buscar <texto>`** - Search products by name, category, or SKU
  - Example: `buscar zapatillas`
- **`agregar <SKU>`** - Add product to cart
  - Example: `agregar ZAP-001`
  - With quantity: `agregar ZAP-001 x2`
- **`carrito`** - View cart items and totals
- **`pagar`** / `checkout` / `pago` - Generate payment link

### Sample Products

The seed data includes these products:
- **ZAP-001**: Zapatillas Nike Air Max ($159,900)
- **CAM-002**: Camisa Polo Lacoste ($89,900)
- **REL-003**: Reloj Casio G-Shock ($259,900)
- **AUD-004**: Audífonos Sony WH-1000XM4 ($399,900)
- **MOC-005**: Mochila Samsonite ($129,900)
- **PAN-006**: Pantalón Jeans Levis ($69,900)

## API Endpoints

### Chat Session Management

**Create Session**
```bash
curl -X POST http://localhost:8000/api/chat/session/ \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "session_id": "uuid",
  "timeout_minutes": 5,
  "message": "Welcome message..."
}
```

**Heartbeat**
```bash
curl -X POST http://localhost:8000/api/chat/heartbeat/ \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id"}'
```

**Send Message**
```bash
curl -X POST http://localhost:8000/api/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "ver ofertas"
  }'
```

Response format:
```json
{
  "reply": "Response message",
  "products": [
    {
      "sku": "ZAP-001",
      "name": "Product name",
      "price": "$159,900.00",
      "image_url": "https://...",
      "category": "Category"
    }
  ],
  "cart": {
    "items": [
      {
        "sku": "ZAP-001",
        "name": "Product name",
        "quantity": 2,
        "price_total": "$319,800.00"
      }
    ],
    "total": "$319,800.00"
  },
  "payment_link": "http://localhost:8000/pay/session-id/"
}
```

## Session Management

- **Timeout**: Sessions expire after 5 minutes of inactivity
- **Heartbeat**: Frontend sends keep-alive every 60 seconds
- **Auto-recovery**: Expired sessions are automatically recreated
- **Window focus**: Heartbeat pauses when window loses focus

## Development Notes

### Django Models & Serializers

- **ChatSession**: UUID-based sessions with status tracking
- **Product**: Product catalog with SKU, pricing, and categories
- **CartItem**: Shopping cart with session association
- **Serializers**: Proper DRF serializers for data validation and transformation

### Frontend Features

- **Automatic session creation** on app load
- **Heartbeat management** with window focus detection
- **Quick action buttons** for common commands
- **Structured message display** for products and cart items
- **Payment link integration** with external window opening

### Error Handling

- **400**: Bad Request (validation errors)
- **404**: Session not found
- **410**: Session expired (triggers auto-recreation)
- **Network errors**: Graceful degradation with user feedback

## Project Structure

```
chat_django_react/
├── backend/
│   ├── requirements.txt
│   ├── manage.py
│   ├── mysite/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── chat/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── payment_urls.py
│       ├── seed.py
│       └── tests.py
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       ├── index.css
│       └── App.js
└── README.md
```

## Customization

### Adding New Products

Use Django admin or create products programmatically:

```python
from chat.models import Product

Product.objects.create(
    sku='NEW-001',
    name='New Product',
    description='Product description',
    price_cents=9990000,  # $99,900.00
    image_url='https://example.com/image.jpg',
    category='New Category'
)
```

### Extending Chat Intents

Add new intent patterns in `chat/views.py` in the `process_message` view.

### UI Customization

Modify the React components and CSS in `src/` to customize the appearance and behavior.

## Production Deployment

### Backend
- Set `DEBUG = False` in settings
- Configure proper database (PostgreSQL recommended)
- Set up proper CORS origins
- Use environment variables for sensitive settings
- Set up proper static file serving

### Frontend
- Build production bundle: `npm run build`
- Deploy to CDN or static hosting
- Update API URLs for production backend

## License

This is a demo project for educational purposes.