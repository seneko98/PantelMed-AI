import React, { useState, useEffect } from 'react';
import './pantelmed_shop.css';

const PantelmedShop: React.FC = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [cart, setCart] = useState<any[]>([]);
  const [userId, setUserId] = useState('');
  const [contactInfo, setContactInfo] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    fetch('http://localhost:5000/api/shop/products?category=' + (selectedCategory === 'all' ? '' : selectedCategory))
      .then(response => response.json())
      .then(data => setProducts(data.products || []));
  }, [selectedCategory]);

  const addToCart = (product: any) => {
    setCart([...cart, { product_id: product._id, quantity: 1, price: product.price }]);
  };

  const handleOrder = async () => {
    const orderData = {
      user_id: userId,
      cart_items: cart,
      contact_info: contactInfo
    };
    const response = await fetch('http://localhost:5000/api/shop/create_order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });
    const result = await response.json();
    alert(result.status === 'success' ? `Замовлення #{result.order_id} створено! Сума: ${result.total} USDT` : result.error);
  };

  const connectMessenger = async (messenger: string) => {
    const messengerId = prompt(`Введи ${messenger} ID:`);
    if (messengerId) {
      const response = await fetch('http://localhost:5000/api/shop/connect_messenger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, messenger, messenger_id: messengerId })
      });
      const result = await response.json();
      alert(result.message || result.error);
    }
  };

  const categories = ['all', 'minerals', 'adaptogens', 'skincare', 'antiaging', 'vitamins', 'nootropics'];

  return (
    <div className="shop-container">
      <h1 className="shop-title">PantelMed Shop</h1>
      <div className="category-filter">
        {categories.map(cat => (
          <button key={cat} onClick={() => setSelectedCategory(cat)} className="category-btn">
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>
      <div className="products-grid">
        {products.map((product, index) => (
          <div key={index} className={`product-card ${product.category === 'skincare' || product.category === 'antiaging' ? 'female-block' : product.category === 'minerals' || product.category === 'vitamins' ? 'nutrition' : 'sport-pharma'}`}>
            <h3>{product.name} {product.emoji}</h3>
            <p>Ціна: {product.price} USDT</p>
            <button onClick={() => addToCart(product)} className="add-btn">Додати до кошика</button>
          </div>
        ))}
      </div>
      <div className="cart-section">
        <h2>Кошик</h2>
        {cart.map((item, index) => (
          <div key={index}>{item.product_id} x{item.quantity} - {item.price} USDT</div>
        ))}
        <input
          type="text"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          className="input-field"
        />
        <input
          type="text"
          placeholder="Контактна інформація"
          value={contactInfo}
          onChange={(e) => setContactInfo(e.target.value)}
          className="input-field"
        />
        <button onClick={handleOrder} className="order-btn">Замовити</button>
      </div>
      <div className="messenger-section">
        <button onClick={() => connectMessenger('telegram')} className="messenger-btn">Підключити Telegram</button>
        <button onClick={() => connectMessenger('viber')} className="messenger-btn">Підключити Viber</button>
      </div>
    </div>
  );
};

export default PantelmedShop;
