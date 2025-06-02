import { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [minPrice, setMinPrice] = useState('0');
  const [maxPrice, setMaxPrice] = useState('');
  const [daysSinceListed, setDaysSinceListed] = useState('1');
  const [radius, setRadius] = useState('20');
  const [anuncios, setAnuncios] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Não envie maxPrice se estiver vazio
    const payload = { query, minPrice, daysSinceListed, radius };
    if (maxPrice) payload.maxPrice = maxPrice;

    const response = await fetch('http://localhost:5000/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    setAnuncios(data.resultados || []);
  };

  return (
    <div style={{
      backgroundColor: '#3e3b3a',
      minHeight: '100vh',
      color: 'white',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '40px 20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>Buscar Anúncios no Marketplace</h1>

      <form onSubmit={handleSubmit} style={{ width: '300px' }}>
        <input
          placeholder="Nome do item"
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={inputStyle}
        />
        <select
          value={minPrice}
          onChange={e => setMinPrice(e.target.value)}
          style={inputStyle}
        >
          <option value="0">Preço mínimo: 0</option>
          <option value="1000">Preço mínimo: 1000</option>
          <option value="2000">Preço mínimo: 2000</option>
          <option value="5000">Preço mínimo: 5000</option>
          <option value="10000">Preço mínimo: 10000</option>
        </select>
        <input
          placeholder="Preço máximo (opcional)"
          value={maxPrice}
          onChange={e => setMaxPrice(e.target.value)}
          style={inputStyle}
        />
        <select
          value={daysSinceListed}
          onChange={e => setDaysSinceListed(e.target.value)}
          style={inputStyle}
        >
          <option value="1">Últimos 1 dia</option>
          <option value="2">Últimos 2 dias</option>
          <option value="3">Últimos 3 dias</option>
          <option value="7">Últimos 7 dias</option>
        </select>
        <select
          value={radius}
          onChange={e => setRadius(e.target.value)}
          style={inputStyle}
        >
          <option value="20">20 km</option>
          <option value="40">40 km</option>
          <option value="60">60 km</option>
          <option value="80">80 km</option>
          <option value="100">100 km</option>
          <option value="150">150 km</option>
          <option value="200">200 km</option>
        </select>
        <button type="submit" style={buttonStyle}>Buscar</button>
      </form>

      <hr style={{
        margin: '40px 0',
        width: '300px',
        border: '1px solid black'
      }} />

      <h2>Resultados:</h2>
      <ul style={{ width: '100%', maxWidth: '900px', paddingLeft: '0px' }}>
        {anuncios.map((a, index) => {
          const [cidade, distancia] = (a.localizacao || '').split('·').map(s => s.trim());

          return (
            <li key={index} style={{ marginBottom: '20px', listStyle: 'none' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '20px',
                backgroundColor: '#2e2c2b',
                padding: '12px',
                borderRadius: '8px'
              }}>
                {/* Imagem */}
                {a.imagem && (
                  <img
                    src={a.imagem}
                    alt="Imagem do anúncio"
                    style={{
                      width: '120px',
                      height: '120px',
                      objectFit: 'cover',
                      borderRadius: '8px',
                      backgroundColor: '#ccc',
                    }}
                  />
                )}

                {/* Conteúdo */}
                <div style={{ flex: 1 }}>
                  <a
                    href={a.link}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#81c784', fontWeight: 'bold', fontSize: '18px', textDecoration: 'none' }}
                  >
                    {a.titulo}
                  </a>
                  <div style={{ fontSize: '16px', marginTop: '6px' }}>
                    💰 <strong>{a.preco}</strong> <br />
                    📍 {cidade || 'Localização não informada'} <br />
                  </div>
                </div>
              </div>
              <hr style={{ marginTop: '12px', border: '0.5px solid #222' }} />
            </li>
          );
        })}
      </ul>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: '8px',
  marginBottom: '12px',
  borderRadius: '4px',
  border: '1px solid #555',
  backgroundColor: '#5a5957',
  color: 'white',
  fontSize: '14px',
};

const buttonStyle = {
  width: '100%',
  padding: '10px',
  backgroundColor: '#81c784',
  border: 'none',
  borderRadius: '4px',
  color: '#222',
  fontWeight: 'bold',
  fontSize: '16px',
  cursor: 'pointer',
};

export default App;
