import { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [daysSinceListed, setDaysSinceListed] = useState('');
  const [anuncios, setAnuncios] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const response = await fetch('http://localhost:5000/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, minPrice, maxPrice, daysSinceListed }),
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
        <input
          placeholder="Preço mínimo"
          value={minPrice}
          onChange={e => setMinPrice(e.target.value)}
          style={inputStyle}
        />
        <input
          placeholder="Preço máximo"
          value={maxPrice}
          onChange={e => setMaxPrice(e.target.value)}
          style={inputStyle}
        />
        <input
          placeholder="Dias desde publicação"
          value={daysSinceListed}
          onChange={e => setDaysSinceListed(e.target.value)}
          style={inputStyle}
        />
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
