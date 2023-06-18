import './App.css';
import {useEffect, useState} from 'react'
import { PacmanLoader } from 'react-spinners';
import Tabla from './tabla';
function App() {

  const [query, setQuery] = useState('')
  const [k, setK] = useState('')
  const [isRunning, setisRunning] = useState(false)
  const [isfirstOpen, setisfirstOpen] = useState(true)
  const [elapsedTime, setelapsedTime] =  useState(0)
  const headers = ['title', 'abstract','rank']
  const [data, setData] = useState([])
  
  useEffect(() => {
    let intervalId;
    if(isRunning){
      intervalId = setInterval(() =>{
        setelapsedTime((prevElapsedTime) => prevElapsedTime + 1);
      }, 1000)
    }
    return () => clearInterval(intervalId);
  }, [isRunning])

  const handleStart = () =>{
    setisRunning(true)
  }

  const handleStop = () =>{
    setisRunning(false)
  }

  const handleReset = () => {
    setisRunning(false);
    setelapsedTime(0);
  }

  const sendQuery= async (e) =>{
    setisfirstOpen(true)
    handleReset()
    if(e)
      e.preventDefault()
    console.log(query)
    try{
      const response = await fetch('http://localhost:8000/obtener_datos',{
        method : "POST",
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({query,k}),
      })
      if(response.ok){
        const {data: d_response} = await response.json()
        setData(d_response)
        handleStop()
        setisfirstOpen(false)
      } else{
        console.log("error al obtener datos")
      }
    } catch(error){
      console.error("error en la solicitud",error)
    }
  } 



  return (
    <section className='app'>
      <h2>Inverted Index</h2>
      <form className='query'>
        <input type="text" id="texto" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ingresa la query"/>
        <input type='text' id='topk' value={k} onChange={(e) => setK(e.target.value)} placeholder="Top K"/>
        <button onClick={(e)=>{sendQuery(e); handleStart()}} disabled={isRunning}>Enviar</button>
      </form>
      {!isfirstOpen && (<Tabla headers={headers} data={data}/>)}
      <span>Elapsed Time: {elapsedTime} seconds</span>
      {isRunning && (
        <PacmanLoader color='#36D7B7' size={25}/>
      )}
    </section>
  );
}

export default App;