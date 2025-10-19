import React, { useState, useEffect } from 'react';
import './pantelmed_shop.css';

const PantelmedShop: React.FC = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [cart, setCart] = useState<any[]>([]);
  const [userId, setUserId] = useState('');
  const [contactInfo, setContactInfo] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  // Завантаження продуктів
  useEffect(() => {
    fetch(`http://localhost:8000/api/shop/products?category=${selectedCategory === 'all' ? '' : selectedCategory}`)
      .then(response => response.json())
      .then(data => setProducts(data.products || []))
      .catch(error => console.error('Error fetching products:', error));
  }, [selectedCategory]);

  // Перевірка авторизації та статусу підписки
  useEffect(() => {
    if (userId) {
      fetch(`http://localhost:8000/api/profile?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
          setIsAuthenticated(!!data.profile);
          setIsSubscribed(data.profile?.subscription_end > new Date().toISOString());
        })
        .catch(error => console.error('Error fetching profile:', error));
    }
  }, [userId]);

  // Завантаження результатів тесту для нових користувачів
  useEffect(() => {
    if (userId && !testResults) {
      fetch(`http://localhost:8000/api/test?user_id=${userId}`)
        .then(response => response.json())
        .then(data => setTestResults(data.results || null))
        .catch(error => console.error('Error fetching test:', error));
    }
  }, [userId]);

  const addToCart = (product: any) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    if (existingItem) {
      setCart(cart.map(item =>
        item.product_id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { product_id: product.id, quantity: 1, price: product.price_usd }]);
    }
  };

  const handleOrder = async () => {
    if (!userId || !cart.length) {
      alert('Введіть User ID та додайте товари до кошика');
      return;
    }
    const orderData = {
      user_id: userId,
      items: cart,
      usdt_address: contactInfo
    };
    try {
      const response = await fetch('http://localhost:8000/api/shop/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });
      const result = await response.json();
      alert(result.status === 'success'
        ? `Замовлення #${result.cart_id} створено! Сума: ${result.total_price} USDT`
        : result.error || 'Помилка при замовленні');
    } catch (error) {
      alert('Помилка при замовленні: ' + error);
    }
  };

  const connectMessenger = async (messenger: string) => {
    const messengerId = prompt(`Введи ${messenger} ID:`);
    if (messengerId) {
      try {
        const response = await fetch('http://localhost:8000/api/shop/connect_messenger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, messenger, messenger_id: messengerId })
        });
        const result = await response.json();
        alert(result.message || result.error);
      } catch (error) {
        alert('Помилка підключення месенджера: ' + error);
      }
    }
  };

  const handleTestSubmit = async (answers: any) => {
    try {
      const response = await fetch('http://localhost:8000/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, answers, language: 'uk' })
      });
      const result = await response.json();
      setTestResults(result);
    } catch (error) {
      alert('Помилка при відправці тесту: ' + error);
    }
  };

  const categories = ['all', 'minerals', 'adaptogens', 'skincare', 'antiaging', 'vitamins', 'nootropics', 'pharma'];

  return (
    <div className="shop-container">
      <h1 className="shop-title">PantelMed Shop</h1>
      {!isAuthenticated && (
        <div className="auth-section">
          <input
            type="text"
            placeholder="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="input-field"
          />
          <button onClick={() => setIsAuthenticated(!!userId)} className="order-btn">Увійти</button>
        </div>
      )}
      {isAuthenticated && !testResults && (
        <div className="test-section">
          <h2>Тест на рівень здоров’я</h2>
          <p>Пройдіть тест, щоб отримати персональні рекомендації</p>
          <button onClick={() => handleTestSubmit({ sample: 'test' })} className="order-btn">Пройти тест</button>
        </div>
      )}
      {isAuthenticated && testResults && (
        <div className="test-results">
          <h2>Результати тесту</h2>
          {isSubscribed ? (
            <div>
              <p>Ваші відповіді:</p>
              <ul>
                {Object.entries(testResults.answers || {}).map(([question, answer]: any) => (
                  <li key={question}>
                    <span className="selected-answer">{question}: {answer}</span>
                    <span className="unselected-answer"> (Інші варіанти: закреслені)</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p>Оформіть підписку, щоб побачити детальні результати</p>
          )}
        </div>
      )}
      <div className="menu-container">
        <div className="menu-column">
          <button className="menu-btn" onClick={() => setSelectedCategory('test')}>Тест на рівень здоров’я</button>
          <button className="menu-btn" onClick={() => window.location.href = '/ai-doctor'}>AI Лікар</button>
          <button className="menu-btn" onClick={() => setSelectedCategory('antiaging')}>Антиейджинг</button>
          <button className="menu-btn" onClick={() => setSelectedCategory('skincare')}>Луксмаксинг-косметологія</button>
        </div>
        <div className="menu-column">
          <button className="menu-btn" onClick={() => window.location.href = '/profile'}>Особистий кабінет</button>
          <button className="menu-btn" onClick={() => setSelectedCategory('diets')}>Дієти</button>
          <button className="menu-btn" onClick={() => setSelectedCategory('antifitness')}>Антифітнес</button>
          <button className="menu-btn" onClick={() => setSelectedCategory('pharma')}>Фармакологія</button>
        </div>
      </div>
      <div className="consultation-section">
        <button className="consultation-btn">Консультація</button>
      </div>
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
            <p>Ціна: {product.price_usd} USDT</p>
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
          placeholder="USDT адреса"
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
