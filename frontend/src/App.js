import { useState, useMemo } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [minPrice, setMinPrice] = useState('gratuito');
  const [maxPrice, setMaxPrice] = useState('');
  const [daysSinceListed, setDaysSinceListed] = useState('1');
  const [radius, setRadius] = useState('20');
  const [baseLocation, setBaseLocation] = useState('indaial');
  const [anuncios, setAnuncios] = useState([]);
  const [sortOrder, setSortOrder] = useState('none');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Não envie maxPrice se estiver vazio
    // Não envie minPrice se for "gratuito"
    const payload = { query, daysSinceListed, radius, baseLocation };
    if (minPrice !== 'gratuito') payload.minPrice = minPrice;
    if (maxPrice) payload.maxPrice = maxPrice;

    try {
      const response = await fetch('http://localhost:5000/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.erro || 'Erro ao buscar anúncios.');
      setAnuncios(data.resultados || []);
    } catch (err) {
      setAnuncios([]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Função para extrair número do preço (ex: "R$ 1.234" => 1234)
  function parsePreco(preco) {
    if (!preco) return NaN;
    // Remove pontos e espaços, depois pega apenas números
    const num = preco.replace(/\./g, '').replace(/[^\d]/g, '');
    return num ? parseInt(num, 10) : NaN;
  }

  // Função para extrair UF do campo localizacao
  function getUF(localizacao) {
    if (!localizacao) return '';
    const partes = localizacao.split(',');
    if (partes.length < 2) return '';
    const uf = partes[partes.length - 1].trim();
    return uf.slice(-2).toUpperCase();
  }

  // Ordenação global: SC primeiro, depois ordenação por preço se selecionado
  const anunciosOrdenados = useMemo(() => {
    const arr = [...anuncios];
    arr.sort((a, b) => {
      // SC sempre primeiro
      const ufA = getUF(a.localizacao);
      const ufB = getUF(b.localizacao);
      if (ufA === 'SC' && ufB !== 'SC') return -1;
      if (ufA !== 'SC' && ufB === 'SC') return 1;
      // Ambos SC ou ambos não SC, ordena por preço se necessário
      if (sortOrder === 'asc') {
        return parsePreco(a.preco) - parsePreco(b.preco);
      }
      if (sortOrder === 'desc') {
        return parsePreco(b.preco) - parsePreco(a.preco);
      }
      return 0;
    });
    return arr;
  }, [anuncios, sortOrder]);

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
          value={baseLocation}
          onChange={e => setBaseLocation(e.target.value)}
          style={inputStyle}
        >
          <option value="indaial">Base: Indaial, SC</option>
          <option value="blumenau">Base: Blumenau, SC</option>
        </select>
        <select
          value={minPrice}
          onChange={e => setMinPrice(e.target.value)}
          style={inputStyle}
        >
          <option value="gratuito">Gratuito</option>
          <option value="50">Preço mínimo: 50</option>
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
        <button type="submit" style={buttonStyle} disabled={loading}>
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span
                style={{
                  width: '18px',
                  height: '18px',
                  border: '3px solid #fff',
                  borderTop: '3px solid #81c784',
                  borderRadius: '50%',
                  display: 'inline-block',
                  marginRight: '8px',
                  animation: 'spin 1s linear infinite'
                }}
              />
              Buscando...
            </span>
          ) : (
            'Buscar'
          )}
        </button>
      </form>

      {error && (
        <div style={{ width: '300px', color: '#ffb4ab', marginTop: '12px' }}>
          {error}
        </div>
      )}

      <div style={{ width: '300px', margin: '20px 0 0 0' }}>
        <label style={{ color: '#fff', marginRight: '10px' }}>Ordenar por preço:</label>
        <select
          value={sortOrder}
          onChange={e => setSortOrder(e.target.value)}
          style={inputStyle}
        >
          <option value="none">Sem ordenação</option>
          <option value="asc">Menor preço</option>
          <option value="desc">Maior preço</option>
        </select>
      </div>

      <hr style={{
        margin: '40px 0',
        width: '300px',
        border: '1px solid black'
      }} />

      <h2>Resultados:</h2>
      <ul style={{ width: '100%', maxWidth: '900px', paddingLeft: '0px' }}>
        {anunciosOrdenados.map((a, index) => {
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
                    {/* Valor ao lado do emoji */}
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

      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg);}
            100% { transform: rotate(360deg);}
          }
        `}
      </style>
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
