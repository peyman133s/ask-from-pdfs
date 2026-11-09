import { StrictMode, useCallback, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { api, errorMessage, UNCATEGORIZED } from './api'
import type { Category, LibraryFile } from './api'
import { Ask } from './Ask'
import { Icon } from './components'
import { Library } from './Library'
import './styles.css'

const currentView = () => window.location.hash === '#ask' ? 'ask' : 'library'

function App() {
  const [view, setView] = useState(currentView)
  const [files, setFiles] = useState<LibraryFile[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const fileRequest = useRef(0)
  const hasActiveJobs = files.some(file => file.status === 'ingesting')

  useEffect(() => {
    const navigate = () => setView(currentView())
    window.addEventListener('hashchange', navigate)
    return () => window.removeEventListener('hashchange', navigate)
  }, [])

  const refreshFiles = useCallback(async (signal?: AbortSignal) => {
    const requestNumber = ++fileRequest.current
    const next = await api.files(signal)
    if (!signal?.aborted && requestNumber === fileRequest.current) setFiles(next)
  }, [])

  const openWorkspace = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    setError('')
    try {
      const [next] = await Promise.all([api.categories(signal), refreshFiles(signal)])
      if (!signal?.aborted) setCategories(next)
    } catch (cause) {
      if (!signal?.aborted) setError(errorMessage(cause))
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [refreshFiles])

  useEffect(() => {
    const controller = new AbortController()
    void openWorkspace(controller.signal)
    return () => controller.abort()
  }, [openWorkspace])

  useEffect(() => {
    if (!hasActiveJobs) return
    const controller = new AbortController()
    let timer: number
    async function poll() {
      try {
        await refreshFiles(controller.signal)
        if (!controller.signal.aborted) setError('')
      } catch (cause) {
        if (!controller.signal.aborted) setError(errorMessage(cause))
      }
      if (!controller.signal.aborted) timer = window.setTimeout(poll, 1200)
    }
    timer = window.setTimeout(poll, 1200)
    return () => {
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [hasActiveJobs, refreshFiles])

  async function createCategory(name: string) {
    const category = await api.addCategory(name)
    setCategories(current => {
      if (current.some(item => item.id === category.id)) return current
      return [...current, category].sort((a, b) => {
        if (a.id === UNCATEGORIZED) return -1
        if (b.id === UNCATEGORIZED) return 1
        return a.name.localeCompare(b.name)
      })
    })
  }

  const page = view === 'ask' ? 'Ask a Question' : 'File Library'

  return (
    <div className="workspace">
      <aside className="sidebar">
        <a className="brand" href="#library"><span><Icon name="brand" size={21} /></span>Ask from Files</a>
        <nav aria-label="Workspace">
          <a href="#library" aria-current={view === 'library' ? 'page' : undefined}><Icon name="library" />File Library</a>
          <a href="#ask" aria-current={view === 'ask' ? 'page' : undefined}><Icon name="ask" />Ask a Question</a>
        </nav>
        <span className="local-label">Local workspace</span>
      </aside>
      <div className="content">
        <div className="topbar"><span>Workspace</span><span aria-hidden="true">/</span><strong>{page}</strong></div>
        <main>
          {error && (
            <div className="notice error workspace-error" role="alert">
              <span>{error}</span>
              <button className="button small" disabled={loading} onClick={() => void openWorkspace()}>Retry</button>
            </div>
          )}
          <div hidden={view !== 'library'}>
            <Library files={files} categories={categories} loading={loading}
              refreshFiles={refreshFiles} onCreateCategory={createCategory} />
          </div>
          <div hidden={view !== 'ask'}><Ask files={files} categories={categories} /></div>
        </main>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
