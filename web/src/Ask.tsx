import { useState } from 'react'
import type { FormEvent } from 'react'
import { api, errorMessage } from './api'
import type { Answer, Category, LibraryFile } from './api'
import { CategoryOptions, FileLabel, Icon } from './components'

export function Ask({ files, categories }: { files: LibraryFile[]; categories: Category[] }) {
  const [scope, setScope] = useState('')
  const [question, setQuestion] = useState('')
  const [asked, setAsked] = useState('')
  const [result, setResult] = useState<Answer | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const ready = files.filter(file => file.status === 'ready' && (!scope || file.category_id === scope)).length
  const scopeName = categories.find(category => category.id === scope)?.name ?? 'all categories'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const input = question.trim()
    if (!input || !ready || busy) return
    setBusy(true)
    setAsked(input)
    setResult(null)
    setError('')
    try {
      setResult(await api.ask(input, scope))
      setQuestion('')
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">Document workspace</p>
          <h1>Ask a Question</h1>
          <p className="subtitle">Ask about files that are ready and review the sources.</p>
        </div>
      </header>
      <label className="search-scope">
        Search in
        <select value={scope} disabled={busy} onChange={event => {
          setScope(event.target.value)
          setAsked('')
          setResult(null)
          setError('')
        }}>
          <option value="">All categories</option>
          <CategoryOptions categories={categories} />
        </select>
      </label>
      <div className="ask-layout">
        <section className="panel answer-panel" aria-label="Question and answer">
          <div className="answer-content" aria-live="polite" aria-busy={busy}>
            {asked && <p className="question-bubble" dir="auto">{asked}</p>}
            <h2 className="answer-heading"><span><Icon name="sparkle" size={15} /></span>Answer</h2>
            {error ? <p className="notice error" role="alert">{error}</p> : result ? (
              <p className="answer-text" dir="auto">
                {result.answer.split(/(\[\d+\])/).map((part, index) => {
                  const source = result.sources.find(item => part === `[${item.number}]`)
                  return source ? (
                    <button type="button" className="citation" key={index}
                      aria-label={`Source ${source.number}, ${source.filename}`}
                      onClick={() => document.getElementById(`source-${source.number}`)?.focus()}>{part}</button>
                  ) : part
                })}
              </p>
            ) : (
              <p className="muted">{busy ? 'Searching your files and asking AvalAI…' : ready
                ? 'Your answer will appear here.'
                : 'Ingest files or choose a category with ready files to ask a question.'}</p>
            )}
          </div>
          <form className="question-form" onSubmit={submit}>
            <input aria-label="Question" placeholder="Ask about your files…" value={question} dir="auto"
              maxLength={4000} disabled={busy || !ready} onChange={event => setQuestion(event.target.value)} />
            <button className="button primary" disabled={busy || !ready || !question.trim()}>
              {busy ? 'Asking…' : 'Ask'} <Icon name="send" size={16} />
            </button>
          </form>
        </section>
        <aside className="panel source-panel" aria-label="Sources">
          <h2>Sources</h2>
          {result?.sources.length ? (
            <ol className="sources">
              {result.sources.map(source => (
                <li key={source.number} id={`source-${source.number}`} tabIndex={-1}>
                  <div className="source-title">
                    <span className="citation">[{source.number}]</span><FileLabel name={source.filename} />
                  </div>
                  {source.location && <p className="source-location" dir="auto">{source.location}</p>}
                  <p className="source-excerpt" dir="auto">{source.excerpt}</p>
                </li>
              ))}
            </ol>
          ) : <p className="muted">Retrieved excerpts will appear here.</p>}
        </aside>
      </div>
      <p className="scope-note">{ready} ready {ready === 1 ? 'file' : 'files'} in {scopeName}</p>
    </>
  )
}
