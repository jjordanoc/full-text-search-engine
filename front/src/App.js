import './App.css';
import { useEffect, useState } from 'react';
import { PacmanLoader } from 'react-spinners';
import Tabla from './tabla';

function App() {
  const [query, setQuery] = useState('');
  const [k, setK] = useState('');
  const [isRunning, setisRunning] = useState(false);
  const [isRunning2, setisRunning2] = useState(false);
  const [isfirstOpen1, setisfirstOpen1] = useState(true);
  const [isfirstOpen2, setisfirstOpen2] = useState(true);
  const [elapsedTime, setelapsedTime] = useState(0);
  const [elapsedTime2, setelapsedTime2] = useState(0);
  const headers = ['Title', 'Abstract', 'Rank'];
  const headers2 = ['Title', 'Abstract', 'Rank'];
  const [data1, setData1] = useState([]);
  const [data2, setData2] = useState([]);

  useEffect(() => {
    let intervalId;
    if (isRunning) {
      intervalId = setInterval(() => {
        setelapsedTime((prevElapsedTime) => prevElapsedTime + 1);
      }, 1000);
    }
    return () => clearInterval(intervalId);
  }, [isRunning]);

  useEffect(() => {
    let intervalId;
    if (isRunning2) {
      intervalId = setInterval(() => {
        setelapsedTime2((prevElapsedTime) => prevElapsedTime + 1);
      }, 1000);
    }
    return () => clearInterval(intervalId);
  }, [isRunning2]);

  const handleStart = () => {
    setisRunning(true);
    setisRunning2(true);
  };

  const handleStop = (n) => {
    if (n === 1) {
      setisRunning(false);
    } else {
      setisRunning2(false);
    }
  };

  const handleReset = () => {
    setisRunning(false);
    setisRunning2(false);
    setelapsedTime(0);
    setelapsedTime2(0);
  };

  const sendQuery = async (e) => {
    setisfirstOpen1(true);
    setisfirstOpen2(true);
    handleReset();
    if (e) e.preventDefault();
    console.log(query);

    try {
      const response = await fetch('http://localhost:8000/postgresql_recover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, k }),
      });
      if (response.ok) {
        const { data: d_response } = await response.json();
        setData1(d_response);
        handleStop(1);
        setisfirstOpen1(false);
      } else {
        console.log('error al obtener datos');
      }
    } catch (error) {
      console.error('error en la solicitud', error);
    }

    try {
      const response = await fetch('http://localhost:8000/local_index_recover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, k }),
      });
      if (response.ok) {
        const { data: d_response } = await response.json();
        setData2(d_response);
        handleStop(2);
        setisfirstOpen2(false);
      } else {
        console.log('error 2');
      }
    } catch (error) {
      console.error('error 2', error);
    }
  };

  return (
    <section className="app">
      <h2>Inverted Index</h2>
      <form className="query">
        <input
          type="text"
          id="texto"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ingresa la query"
        />
        <input
          type="text"
          id="topk"
          value={k}
          onChange={(e) => setK(e.target.value)}
          placeholder="Top K"
        />
        <button onClick={(e) => { sendQuery(e); handleStart(); }} disabled={isRunning}>Enviar</button>
      </form>
      <section className="tablas">
        <div className="tabla-inside">
          {!isfirstOpen1 && (
            <>
              <h3>Postgres</h3>
              <Tabla headers={headers} data={data1} />
            </>
          )}
          {!isfirstOpen1 &&(<span>Elapsed Time: {elapsedTime} seconds</span>)}
          {isRunning && (
            <PacmanLoader color="#36D7B7" size={25} />
          )}
        </div>
        <div className="tabla-inside">
          {!isfirstOpen2 && (
            <>
              <h3>Python</h3>
              <Tabla headers={headers2} data={data2} />
            </>
          )}
          {!isfirstOpen2 && (<span>Elapsed Time: {elapsedTime2} seconds</span>)}
          {isRunning2 && (
            <PacmanLoader color="#36D7B7" size={25} />
          )}
        </div>
      </section>
    </section>
  );
}

export default App;