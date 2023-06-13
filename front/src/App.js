import './App.css';
import {useState} from 'react'
function App() {

  const [query, setQuery] = useState('')
  
  const sendQuery= (e) =>{
    e.preventDefault()
    console.log(query)
  } 


  return (
    <section className='app'>
      <h2>Proyecto 2</h2>
      <form className='query'>
        <input type="text" id="texto" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ingresa la query"/>
        <button onClick={sendQuery}>Enviar</button>
      </form>
    </section>
  );
}

export default App;
