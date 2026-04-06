import { useState } from 'react'

export default function YoyakuLogin({ onClose }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [session, setSession] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.message || 'Login failed')
      }

      const data = await res.json()
      localStorage.setItem('yoyaku-session', JSON.stringify(data))
      setSession(data)
    } catch (err) {
      // Network error or API unavailable — show user-friendly message
      if (err instanceof TypeError || err.message === 'Failed to fetch') {
        setError('Login service is currently unavailable')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  if (session) {
    const initials = (session.name || session.email || '?').charAt(0).toUpperCase()
    return (
      <div className="yoyaku-login-panel">
        <button className="yoyaku-login-close" onClick={onClose}>&times;</button>
        <div className="yoyaku-login-success">
          <div className="yoyaku-login-avatar">{initials}</div>
          <h3>{session.name || session.email}</h3>
          {session.tier && <div className="yoyaku-login-tier">{session.tier}</div>}
          {(session.orders != null || session.collection != null) && (
            <div className="yoyaku-login-stats">
              {session.orders != null && <span>{session.orders} orders</span>}
              {session.collection != null && <span>{session.collection} collected</span>}
            </div>
          )}
          {session.genres && session.genres.length > 0 && (
            <div className="yoyaku-login-genres">
              {session.genres.map((g) => (
                <span key={g} className="yoyaku-genre-tag">{g}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="yoyaku-login-panel">
      <button className="yoyaku-login-close" onClick={onClose}>&times;</button>
      <h2 className="yoyaku-login-title">Connect</h2>
      <p className="yoyaku-login-subtitle">Sign in with your YOYAKU account</p>
      <form className="yoyaku-login-form" onSubmit={handleSubmit}>
        <input
          className="yoyaku-login-input"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus
        />
        <input
          className="yoyaku-login-input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <div className="yoyaku-login-error">{error}</div>}
        <button className="yoyaku-login-submit" type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <div className="yoyaku-login-footer">
        <a href="https://yoyaku.io/my-account/" target="_blank" rel="noopener noreferrer">
          Create account
        </a>
      </div>
    </div>
  )
}
