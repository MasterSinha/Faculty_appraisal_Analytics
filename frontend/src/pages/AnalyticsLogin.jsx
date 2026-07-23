import { useState } from 'react'

export default function AnalyticsLogin({ onLogin }) {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')

  function submitLogin(event) {
    event.preventDefault()
    const cleanToken = token.trim().replace(/^Bearer\s+/i, '')

    if (!cleanToken) {
      setError('Enter a valid admin JWT token.')
      return
    }

    localStorage.setItem('access_token', cleanToken)
    onLogin()
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div>
          <span className="eyebrow">Research Analytics</span>
          <h1>Admin Login</h1>
          <p>Paste your existing admin, director, dean, registrar, or VC JWT token to open live analytics.</p>
        </div>

        <form className="login-form" onSubmit={submitLogin}>
          <label>
            Access token
            <textarea
              value={token}
              onChange={(event) => {
                setToken(event.target.value)
                setError('')
              }}
              placeholder="Bearer eyJhbGciOi..."
              rows="5"
            />
          </label>

          {error && <span className="login-error">{error}</span>}

          <button className="primary-action" type="submit">
            Continue to Analytics
          </button>
        </form>
      </section>
    </main>
  )
}

