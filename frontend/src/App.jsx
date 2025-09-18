import React, { useEffect, useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function UploadCSV({ onUploaded }){
  const [file, setFile] = useState(null)
  const [msg, setMsg] = useState('')

  async function submit(e){
    e.preventDefault()
    if(!file) return setMsg('Escolha um arquivo .csv')
    const fd = new FormData()
    fd.append('file', file)
    try{
      await axios.post(`${API}/upload`, fd, { headers: {'Content-Type':'multipart/form-data'} })
      setMsg('Upload realizado com sucesso')
      setFile(null)
      onUploaded && onUploaded()
    }catch(err){
      setMsg(err.response?.data?.error || 'Erro no upload')
    }
  }

  return (<div className='card p-3 mb-3'>
    <h5>Upload CSV</h5>
    <form onSubmit={submit}>
      <input type='file' accept='.csv' onChange={e=>setFile(e.target.files[0])} className='form-control mb-2'/>
      <button className='btn btn-primary' type='submit'>Enviar</button>
    </form>
    {msg && <div className='mt-2'>{msg}</div>}
  </div>)
}

function PatientFilter({ onSelect }){
  const [patients, setPatients] = useState([])
  useEffect(()=>{
    axios.get(`${API}/patients`).then(r=>setPatients(r.data)).catch(()=>setPatients([]))
  },[])
  return (<div className='card p-3 mb-3'>
    <h5>Pacientes</h5>
    <select className='form-select' onChange={e=>onSelect(e.target.value)}>
      <option value=''>-- selecione --</option>
      {patients.map(p=> <option key={p.paciente_id} value={p.paciente_id}>{p.paciente_nome} ({p.paciente_id})</option>)}
    </select>
  </div>)
}

function PatientTable({ pacienteId }){
  const [rows, setRows] = useState([])
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')

  useEffect(()=>{
    if(!pacienteId) return setRows([])
    fetchData()
  },[pacienteId])

  async function fetchData(){
    try{
      const params = {}
      if(start) params.start = start
      if(end) params.end = end
      const res = await axios.get(`${API}/patients/${pacienteId}`, { params })
      setRows(res.data)
    }catch(e){
      setRows([])
    }
  }

  async function download(full=false){
    try{
      const params = {}
      if(!full){
        if(start) params.start = start
        if(end) params.end = end
      }
      const resp = await axios.get(`${API}/download/${pacienteId}`, { params, responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `${pacienteId}_dados.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
    }catch(e){
      alert('Erro ao gerar CSV')
    }
  }

  return (<div className='card p-3'>
    <h5>Dados do paciente {pacienteId}</h5>
    <div className='row mb-2'>
      <div className='col'>
        <label>Start (HH:MM:SS or HH:MM:SS.sss)</label>
        <input className='form-control' value={start} onChange={e=>setStart(e.target.value)} placeholder='12:00:00'/>
      </div>
      <div className='col'>
        <label>End</label>
        <input className='form-control' value={end} onChange={e=>setEnd(e.target.value)} placeholder='13:00:00'/>
      </div>
      <div className='col d-flex align-items-end'>
        <button className='btn btn-primary me-2' onClick={fetchData}>Aplicar filtro</button>
        <button className='btn btn-success me-2' onClick={()=>download(false)}>Download filtrado</button>
        <button className='btn btn-secondary' onClick={()=>download(true)}>Download completo</button>
      </div>
    </div>

    <div style={{overflowX:'auto'}}>
    <table className='table table-bordered'>
      <thead>
        <tr>
          <th>HR</th><th>SPO2</th><th>Pressão SYS</th><th>Pressão DIA</th><th>Temp</th><th>Resp</th><th>Status</th><th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r=> <tr key={r.id} className={r.status==='ALERTA' ? 'table-danger' : ''}>
          <td>{r.hr}</td><td>{r.spo2}</td><td>{r.pressao_sys}</td><td>{r.pressao_dia}</td><td>{r.temp}</td><td>{r.resp_freq}</td><td>{r.status}</td><td>{r.timestamp}</td>
        </tr>)}
      </tbody>
    </table>
    </div>
  </div>)
}

export default function App(){
  const [selected, setSelected] = useState('')
  const [refresh, setRefresh] = useState(0)
  return (<div className='container'>
    <h2>HealthGo - Monitoramento (versão simples)</h2>
    <div className='row'>
      <div className='col-md-4'>
        <UploadCSV onUploaded={()=>setRefresh(r=>r+1)} />
        <PatientFilter onSelect={id=>setSelected(id)} key={refresh} />
      </div>
      <div className='col-md-8'>
        {selected ? <PatientTable pacienteId={selected} /> : <div className='alert alert-info'>Selecione um paciente para ver dados</div>}
      </div>
    </div>
  </div>)
}
