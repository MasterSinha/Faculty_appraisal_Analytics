import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const params = new URLSearchParams(window.location.search)
const tokenFromUrl = params.get('access_token')
const tokenFromRuntimeConfig = window.__RESEARCH_ANALYTICS_CONFIG__?.accessToken
const bootstrapToken = tokenFromUrl || tokenFromRuntimeConfig

if (bootstrapToken && !localStorage.getItem('access_token')) {
  localStorage.setItem('access_token', bootstrapToken)
}

if (tokenFromUrl) {
  params.delete('access_token')
  const cleanSearch = params.toString()
  const cleanUrl = `${window.location.pathname}${cleanSearch ? `?${cleanSearch}` : ''}${window.location.hash}`
  window.history.replaceState({}, document.title, cleanUrl)
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
