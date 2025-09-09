import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Widget, addResponseMessage, addUserMessage, addLinkSnippet, toggleWidget, dropMessages, renderCustomComponent } from 'react-chat-widget';
import axios from 'axios';
import 'react-chat-widget/lib/styles.css';
import './index.css';

const API_BASE_URL = 'http://localhost:8000/api/chat';
const HEARTBEAT_INTERVAL = 60000; // 60 seconds
const REQUEST_TIMEOUT = 5000; // 5 seconds timeout for requests

// Custom component for product display
const ProductCard = ({ product }) => (
  <div className="product-card">
    <img src={product.image_url} alt={product.name} className="product-image" />
    <div className="product-info">
      <h4>{product.name}</h4>
      <p>SKU: {product.sku} | Precio: {product.price}</p>
      <p>Categoría: {product.category}</p>
      <small>💡 Para agregar: "agregar {product.sku}" o "agregar {product.sku} x2"</small>
    </div>
  </div>
);

// Custom component for cart display
const CartDisplay = ({ cart }) => (
  <div className="cart-display">
    <h4>🛒 Tu carrito:</h4>
    {cart.items.map((item, index) => (
      <div key={index} className="cart-item">
        <span>{item.name} ({item.sku})</span>
        <span>Cantidad: {item.quantity} - {item.price_total}</span>
      </div>
    ))}
    <div className="cart-total">
      <strong>💰 Total: {cart.total}</strong>
    </div>
  </div>
);

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const heartbeatInterval = useRef(null);
  const isWindowFocused = useRef(true);
  // Guards to prevent double initialization in React 18 dev and avoid race conditions
  const initializedRef = useRef(false);
  const widgetOpenedRef = useRef(false);

  // Create new session
  const createSession = useCallback(async () => {
    // If there is already an active session, do nothing and return it
    if (sessionId && isSessionActive) {
      return sessionId;
    }
    try {
      try { dropMessages(); } catch (e) { /* widget may not be ready yet */ }
      
      // Add a default welcome message while trying to connect
      setTimeout(() => {
        addResponseMessage('¡Hola! Soy tu asistente de compras. Intentando conectar con el servidor...');
      }, 500);
      
      const response = await axios.post(`${API_BASE_URL}/session/`, {}, { timeout: REQUEST_TIMEOUT });
      const { session_id, message } = response.data;
      
      setSessionId(session_id);
      setIsSessionActive(true);
      
      // Add intro message from backend
      setTimeout(() => {
        addResponseMessage(message || '¡Perfecto! Ya estamos conectados. ¿En qué puedo ayudarte?');
      }, 1000);
      
      // Start heartbeat
      startHeartbeat(session_id);
      
      console.log('New session created:', session_id);
      return session_id;
    } catch (error) {
      console.error('Error creating session:', error);
      
      // Create a fallback session for demo purposes
      const fallbackSessionId = 'demo-' + Math.random().toString(36).substr(2, 9);
      setSessionId(fallbackSessionId);
      setIsSessionActive(true);
      
      setTimeout(() => {
        addResponseMessage('🔗 Modo demo: El servidor no está disponible, pero puedes probar el chat. Comandos disponibles: "ver ofertas", "buscar zapatillas", "carrito"');
      }, 1000);
      return fallbackSessionId;
    }
  }, [sessionId, isSessionActive]);

  // Start heartbeat interval
  const startHeartbeat = useCallback((currentSessionId) => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }
    
    heartbeatInterval.current = setInterval(async () => {
      if (!isWindowFocused.current) return;
      
      try {
        await axios.post(`${API_BASE_URL}/heartbeat/`, {
          session_id: currentSessionId
        }, { timeout: REQUEST_TIMEOUT });
      } catch (error) {
        if (error.response?.status === 410) {
          handleSessionExpired();
        } else {
          console.error('Heartbeat error:', error);
        }
      }
    }, HEARTBEAT_INTERVAL);
  }, []);

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = null;
    }
  }, []);

  // Handle session expiration
  const handleSessionExpired = useCallback(() => {
    setIsSessionActive(false);
    stopHeartbeat();
    setTimeout(() => {
      addResponseMessage('⏰ Tu sesión ha expirado por inactividad. Creando una nueva sesión...');
    }, 100);
    
    setTimeout(() => {
      createSession();
    }, 2000);
  }, [createSession, stopHeartbeat]);

  // Handle new user message
  const handleNewUserMessage = useCallback(async (newMessage) => {
    console.log('New message received:', newMessage);
    
    // Ensure there is an active session before sending the message
    let currentSessionId = sessionId;
    if (!currentSessionId || !isSessionActive) {
      console.log('No active session, creating new one');
      setTimeout(() => { addResponseMessage('❌ No hay sesión activa. Creando nueva sesión...'); }, 100);
      currentSessionId = await createSession();
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/message/`, {
        session_id: currentSessionId,
        message: newMessage
      }, { timeout: REQUEST_TIMEOUT });

      const { reply, products, cart, payment_link } = response.data;

      // Add reply message
      if (reply) {
        setTimeout(() => {
          addResponseMessage(reply);
        }, 300);
      }

      // Display products using custom components
      if (products && products.length > 0) {
        setTimeout(() => {
          products.forEach((product, index) => {
            setTimeout(() => {
              renderCustomComponent(ProductCard, { product });
            }, index * 200);
          });
        }, 600);
      }

      // Display cart using custom component
      if (cart && cart.items && cart.items.length > 0) {
        const delay = products?.length ? (products.length * 200 + 800) : 600;
        setTimeout(() => {
          renderCustomComponent(CartDisplay, { cart });
        }, delay);
      }

      // Display payment link
      if (payment_link) {
        const delay = products?.length ? (products.length * 200 + 1000) : 800;
        setTimeout(() => {
          addLinkSnippet({
            title: '💳 Pagar ahora',
            link: payment_link,
            target: '_blank'
          });
        }, delay);
      }

    } catch (error) {
      if (error.response?.status === 410) {
        handleSessionExpired();
      } else {
        console.error('Error sending message:', error);
        
        // Demo mode fallback responses
        setTimeout(() => {
          if (newMessage.toLowerCase().includes('ofertas')) {
            addResponseMessage('🏷️ Aquí tienes algunas ofertas especiales (modo demo)');
          } else if (newMessage.toLowerCase().includes('buscar')) {
            addResponseMessage('🔍 Buscando productos... (modo demo)');
          } else if (newMessage.toLowerCase().includes('carrito')) {
            addResponseMessage('🛒 Tu carrito está vacío (modo demo)');
          } else if (newMessage.toLowerCase().includes('agregar')) {
            addResponseMessage('✅ Producto agregado al carrito (modo demo)');
          } else {
            addResponseMessage(`📱 Recibí tu mensaje: "${newMessage}" (modo demo sin servidor)`);
          }
        }, 300);
      }
    }
  }, [sessionId, isSessionActive, createSession, handleSessionExpired]);

  // Quick action helpers
  const sendQuickMessage = useCallback((message) => {
    addUserMessage(message);
    handleNewUserMessage(message);
  }, [handleNewUserMessage]);

  // Window focus/blur handlers
  useEffect(() => {
    const handleFocus = () => {
      isWindowFocused.current = true;
      if (sessionId && isSessionActive && !heartbeatInterval.current) {
        startHeartbeat(sessionId);
      }
    };

    const handleBlur = () => {
      isWindowFocused.current = false;
      stopHeartbeat();
    };

    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [sessionId, isSessionActive, startHeartbeat, stopHeartbeat]);

  // Initialize session on mount
  useEffect(() => {
    if (initializedRef.current) return; // prevent double init
    initializedRef.current = true;

    console.log('App mounted - initializing once');

    // Open widget once after initial paint to avoid race conditions
    const openTimer = setTimeout(() => {
      if (!widgetOpenedRef.current) {
        try {
          toggleWidget();
          widgetOpenedRef.current = true;
          console.log('Widget opened');
        } catch (e) {
          console.warn('Unable to toggle widget yet:', e);
        }
      }
    }, 800);

    // Create session shortly after opening widget
    const sessionTimer = setTimeout(() => {
      createSession();
    }, 1200);

    return () => {
      clearTimeout(openTimer);
      clearTimeout(sessionTimer);
      stopHeartbeat();
    };
  }, [createSession, stopHeartbeat]);

  return (
    <div className="App">
      <div className="app-header">
        <h1>🛍️ E-Commerce Chat Assistant</h1>
        <p>
          Tu asistente personal de compras te ayuda a encontrar productos, 
          gestionar tu carrito y proceder al pago. ¡Abre el chat para comenzar!
        </p>
      </div>

      <div className="quick-actions">
        <button 
          className="quick-btn" 
          onClick={() => sendQuickMessage('ver ofertas')}
        >
          🏷️ Ver Ofertas
        </button>
        <button 
          className="quick-btn" 
          onClick={() => sendQuickMessage('buscar zapatillas')}
        >
          👟 Buscar Zapatillas
        </button>
        <button 
          className="quick-btn" 
          onClick={() => sendQuickMessage('carrito')}
        >
          🛒 Ver Carrito
        </button>
      </div>

      <div className="chat-info">
        <strong>💬 Comandos útiles:</strong><br />
        • "ver ofertas" - Productos destacados<br />
        • "buscar [término]" - Buscar productos<br />
        • "agregar [SKU] x2" - Agregar al carrito<br />
        • "carrito" - Ver carrito<br />
        • "pagar" - Proceder al pago<br />
        <br />
        <small>
          Sesión: {isSessionActive ? '🟢 Activa' : '🔴 Inactiva'}<br />
          ID: {sessionId ? sessionId.substring(0, 8) + '...' : 'N/A'}
        </small>
      </div>

      <Widget
        handleNewUserMessage={handleNewUserMessage}
        title="🛍️ Asistente de Compras"
        subtitle="¿En qué puedo ayudarte hoy?"
        senderPlaceHolder="Escribe tu mensaje aquí..."
        showCloseButton={true}
        fullScreenMode={false}
        autofocus={true}
        // Use a valid image URL or omit to avoid rendering quirks
        // profileAvatar can be an image path; leaving it unset for stability
        showTimeStamp={true}
        emojis={true}
        showBadge={true}
      />
    </div>
  );
}

export default App;