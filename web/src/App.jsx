import { useState, useEffect, useRef } from 'react'
import { Send, Upload, Bot, User, Menu, Plus, Sun, Moon, LogOut, Copy, RefreshCw, Edit3, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './App.css'

const API = 'http://localhost:8000/api'

function LoginScreen({ theme }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const handleLogin = async () => {
    const res = await fetch(API+'/login', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ password })
    })
    const data = await res.json()
    if (data.token) {
      localStorage.setItem('acumen_token', data.token)
      window.location.reload()
    } else { setError('Wrong password') }
  }
  return (
    <div className={'login-screen ' + theme}>
      <div className="login-box">
        <div className="login-logo">A</div>
        <h1>ACUMEN</h1>
        <p>Personal AI Operating System</p>
        <input type="password" value={password} onChange={e=>setPassword(e.target.value)}
               onKeyDown={e=>e.key==='Enter'&&handleLogin()} placeholder="Enter password..." autoFocus/>
        <button className="login-btn" onClick={handleLogin}>Sign In</button>
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  )
}

function MessageContent({ content, theme }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
      code({node, inline, className, children, ...props}) {
        const match = /language-(\w+)/.exec(className || '')
        const codeStr = String(children).replace(/\n$/, '')
        if (!inline && match) {
          return (
            <div className="code-block">
              <div className="code-header">
                <span>{match[1]}</span>
                <button onClick={()=>navigator.clipboard.writeText(codeStr)}>Copy</button>
              </div>
              <SyntaxHighlighter style={theme==='dark'?oneDark:oneLight} language={match[1]}
                PreTag="div" customStyle={{margin:0,borderRadius:'0 0 8px 8px',fontSize:'13px'}}>
                {codeStr}
              </SyntaxHighlighter>
            </div>
          )
        }
        return <code className="inline-code" {...props}>{children}</code>
      }
    }}>{content}</ReactMarkdown>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button className="msg-action" onClick={handleCopy} title="Copy response">
      {copied ? <Check size={14}/> : <Copy size={14}/>}
    </button>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [convoId, setConvoId] = useState('')
  const [convos, setConvos] = useState([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [sidebar, setSidebar] = useState(true)
  const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem('acumen_token'))
  const [streamingText, setStreamingText] = useState('')
  const [theme, setTheme] = useState(localStorage.getItem('acumen_theme') || 'dark')
  const [editingIdx, setEditingIdx] = useState(-1)
  const [editText, setEditText] = useState('')
  const [notification, setNotification] = useState('')
  const notify = (msg) => { setNotification(msg); setTimeout(() => setNotification(''), 4000) }
  const endRef = useRef(null)

  useEffect(() => {
    localStorage.setItem('acumen_theme', theme)
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    if (!loggedIn) return
    fetch(API+'/status').then(r=>r.json()).then(setStatus).catch(()=>{})
    fetch(API+'/conversations').then(r=>r.json()).then(setConvos).catch(()=>{})
  }, [loggedIn])

  useEffect(() => { endRef.current?.scrollIntoView({behavior:'smooth'}) }, [messages, streamingText])

  useEffect(() => {
    const handleKey = (e) => {
      if (e.ctrlKey && e.key === 'n') { e.preventDefault(); newChat() }
      if (e.ctrlKey && e.key === 'l') { e.preventDefault(); document.querySelector('.input-area textarea')?.focus() }
      if (e.key === 'Escape') { setSidebar(s => !s) }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  if (!loggedIn) return <LoginScreen theme={theme}/>

  const sendMessage = async (msg, cid) => {
    if (!msg.trim() || loading) return
    const userMsg = { role:'user', content:msg, timestamp:new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    const currentInput = msg
    setInput(''); setLoading(true); setStreamingText('')
    try {
      const res = await fetch(API+'/chat', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ message:currentInput, conversation_id:cid || convoId })
      })
      const data = await res.json()
      if (data.conversation_id) setConvoId(data.conversation_id)
      if (data.messages) {
        setMessages(data.messages)
      } else if (data.response) {
        setMessages(prev => [...prev, {role:'assistant', content:data.response, timestamp:new Date().toISOString()}])
      }
      fetch(API+'/conversations').then(r=>r.json()).then(setConvos).catch(()=>{})
      notify('Response ready')
    } catch(e) {
      setMessages(prev => [...prev, {role:'assistant',content:'Connection error. Try again.'}])
      setStreamingText('')
    }
    setLoading(false)
  }

  const send = () => sendMessage(input, convoId)
  const newChat = () => { setConvoId(''); setMessages([]); setStreamingText('') }
  const loadConvo = async (id) => {
    const res = await fetch(API+'/conversation/'+id)
    const data = await res.json()
    setConvoId(id); setMessages(data.messages)
  }

  const regenerate = (idx) => {
    const userMsg = messages.slice(0, idx).reverse().find(m => m.role === 'user')
    if (userMsg) {
      setMessages(messages.slice(0, idx))
      sendMessage(userMsg.content, convoId)
    }
  }

  const editAndResend = (idx) => {
    setMessages(messages.slice(0, idx))
    sendMessage(editText, convoId)
    setEditingIdx(-1)
    setEditText('')
  }

  const uploadFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const fd = new FormData(); fd.append('file', file)
    setLoading(true)
    const isImage = file.name.match(/\.(png|jpg|jpeg|gif|webp)$/i)
    if (isImage) {
      setMessages(prev => [...prev, {role:'user', content:'[Uploaded image: '+file.name+']'}])
      const res = await fetch(API+'/upload', {method:'POST', body:fd})
      const data = await res.json()
      if (data.analysis) {
        setMessages(prev => [...prev, {role:'assistant', content:'**Image Analysis:**\n\n'+data.analysis}])
      }
    } else {
      const res = await fetch(API+'/upload', {method:'POST', body:fd})
      const data = await res.json()
      setMessages(prev => [...prev, {role:'assistant', content:`**${file.name}** uploaded and ingested (${data.chunks||0} chunks added to knowledge base).`}])
    }
    setLoading(false)
    e.target.value = ''
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      const fd = new FormData(); fd.append('file', file)
      setLoading(true)
      fetch(API+'/upload', {method:'POST', body:fd}).then(r=>r.json()).then(data => {
        if (data.analysis) {
          setMessages(prev => [...prev, {role:'user', content:'[Dropped image: '+file.name+']'}, {role:'assistant', content:'**Image Analysis:**\n\n'+data.analysis}])
        } else {
          setMessages(prev => [...prev, {role:'assistant', content:`**${file.name}** uploaded (${data.chunks||0} chunks ingested).`}])
        }
        setLoading(false)
      })
    }
  }

  const logout = () => { localStorage.removeItem('acumen_token'); setLoggedIn(false) }
  const toggleTheme = () => setTheme(t => t==='dark'?'light':'dark')
  const tokenCount = (text) => Math.ceil(text.length / 4)

  return (
    <div className={'app ' + theme} onDrop={handleDrop} onDragOver={e=>e.preventDefault()}>
      {sidebar && (
        <aside className="sidebar">
          <div className="sidebar-top">
            <button className="new-chat" onClick={newChat}><Plus size={16}/> New Chat <span className="shortcut">Ctrl+N</span></button>
          </div>
          <div className="convo-list">
            {convos.map(c => (
              <div key={c.id} className={'convo-item'+(convoId===c.id?' active':'')} onClick={()=>loadConvo(c.id)}>
                <span className="convo-text">{c.last_message}</span>
              </div>
            ))}
          </div>
          <div className="sidebar-bottom">
            <button onClick={toggleTheme}>{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>} {theme==='dark'?'Light':'Dark'} Mode</button>
            <button onClick={logout}><LogOut size={16}/> Sign Out</button>
            {status && (
              <div className="status-bar">
                <span>{status.knowledge_count.toLocaleString()} docs</span>
                <span>{status.cloud_available ? 'Cloud+Local' : 'Local Only'}</span>
              </div>
            )}
          </div>
        </aside>
      )}
      <main className="main">
        <header>
          <button className="menu-btn" onClick={()=>setSidebar(!sidebar)} title="Toggle sidebar (Esc)"><Menu size={20}/></button>
          <h1>ACUMEN</h1>
          <span className="header-sub">AI Operating System</span>
        </header>
        <div className="messages">
          {messages.length === 0 && !streamingText && (
            <div className="welcome">
              <div className="welcome-logo">A</div>
              <h2>Welcome to Acumen</h2>
              <p>Your personal AI with {status?.knowledge_count?.toLocaleString() || '...'} knowledge documents.</p>
              <div className="suggestions">
                <button onClick={()=>sendMessage('Explain how blockchain works', convoId)}>Explain blockchain</button>
                <button onClick={()=>sendMessage('Write a Python REST API', convoId)}>Write a REST API</button>
                <button onClick={()=>sendMessage('What are the best startup growth strategies?', convoId)}>Startup strategies</button>
              </div>
              <p className="shortcuts-hint">Ctrl+N: New chat | Ctrl+L: Focus input | Esc: Toggle sidebar</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={'msg ' + m.role}>
              <div className="avatar">{m.role==='user' ? <User size={16}/> : <span className="bot-avatar">A</span>}</div>
              <div className="msg-body">
                {editingIdx === i ? (
                  <div className="edit-area">
                    <textarea value={editText} onChange={e=>setEditText(e.target.value)} rows={3}/>
                    <div className="edit-actions">
                      <button onClick={()=>editAndResend(i)}>Send</button>
                      <button onClick={()=>setEditingIdx(-1)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="msg-content">
                    {m.role==='assistant' ? <MessageContent content={m.content} theme={theme}/> : <p>{m.content}</p>}
                  </div>
                )}
                <div className="msg-actions">
                  {m.role==='assistant' && (
                    <>
                      <CopyButton text={m.content}/>
                      <button className="msg-action" onClick={()=>regenerate(i)} title="Regenerate"><RefreshCw size={14}/></button>
                      <span className="token-count">{tokenCount(m.content)} tokens</span>
                    </>
                  )}
                  {m.role==='user' && editingIdx !== i && (
                    <button className="msg-action" onClick={()=>{setEditingIdx(i);setEditText(m.content)}} title="Edit & resend"><Edit3 size={14}/></button>
                  )}
                </div>
              </div>
            </div>
          ))}
          {streamingText && (
            <div className="msg assistant">
              <div className="avatar"><span className="bot-avatar">A</span></div>
              <div className="msg-body">
                <div className="msg-content"><MessageContent content={streamingText} theme={theme}/><span className="cursor">|</span></div>
              </div>
            </div>
          )}
          {loading && !streamingText && (
            <div className="msg assistant">
              <div className="avatar"><span className="bot-avatar">A</span></div>
              <div className="msg-body"><div className="msg-content"><div className="typing-dots"><span></span><span></span><span></span></div></div></div>
            </div>
          )}
          <div ref={endRef}/>
        </div>
        {notification && <div className='toast'>{notification}</div>}
        <div className='input-wrapper'>
          <div className="input-area">
            <label className="upload-btn" title="Upload file or image (drag & drop also works)"><Upload size={18}/><input type="file" hidden onChange={uploadFile} accept=".txt,.md,.py,.json,.csv,.pdf,.docx,.png,.jpg,.jpeg,.gif,.webp"/></label>
            <textarea value={input} onChange={e=>setInput(e.target.value)}
                   onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}
                   placeholder="Message Acumen... (Shift+Enter for new line)" disabled={loading} rows={1}
                   onInput={e=>{e.target.style.height='auto';e.target.style.height=Math.min(e.target.scrollHeight,150)+'px'}}/>
            <button className="send-btn" onClick={send} disabled={loading||!input.trim()}><Send size={18}/></button>
          </div>
          <p className="input-hint">Drop files here to upload. Acumen runs locally — your data stays private.</p>
        </div>
      </main>
    </div>
  )
}