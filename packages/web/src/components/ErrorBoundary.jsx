import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', this.props.name || 'unknown', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', background: '#0a0a14',
          color: '#8888aa', fontFamily: "'JetBrains Mono', monospace", fontSize: 13,
          zIndex: 10,
        }}>
          <div style={{ fontSize: 16, color: '#ff6b6b', marginBottom: 8 }}>Something went wrong</div>
          <div style={{ opacity: 0.5, marginBottom: 16, maxWidth: 400, textAlign: 'center' }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <button
              onClick={this.handleReset}
              style={{
                padding: '8px 20px', background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6,
                color: '#ccc', cursor: 'pointer', fontSize: 13,
              }}
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '8px 20px', background: 'rgba(255,107,107,0.15)',
                border: '1px solid rgba(255,107,107,0.3)', borderRadius: 6,
                color: '#ff6b6b', cursor: 'pointer', fontSize: 13,
              }}
            >
              Reload
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
