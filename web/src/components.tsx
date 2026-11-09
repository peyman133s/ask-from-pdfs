import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from './api'
import type { Category } from './api'

const paths = {
  brand: 'M8 4h10a2 2 0 0 1 2 2v10M5 8h10a2 2 0 0 1 2 2v9a1 1 0 0 1-1 1H5a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Zm2 4h6m-6 4h6',
  library: 'M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z',
  ask: 'M20 11a8 8 0 0 1-8 8H4l1.6-3.2A8 8 0 1 1 20 11Z M8 11h8',
  upload: 'M12 16V4m-5 5 5-5 5 5M4 16v4h16v-4',
  close: 'm6 6 12 12M6 18 18 6',
  plus: 'M12 5v14M5 12h14',
  send: 'M5 12h13m-6-6 6 6-6 6',
  sparkle: 'M12 2l2.3 7.7L22 12l-7.7 2.3L12 22l-2.3-7.7L2 12l7.7-2.3Z',
} as const

export function Icon({ name, size = 18 }: { name: keyof typeof paths; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  )
}

export function FileLabel({ name }: { name: string }) {
  const extension = name.slice(name.lastIndexOf('.') + 1).toLowerCase()
  return (
    <span className="file-label">
      <span className={`extension extension-${extension}`} aria-hidden="true">{extension.toUpperCase()}</span>
      <span className="filename" dir="auto">{name}</span>
    </span>
  )
}

export function CategoryOptions({ categories }: { categories: Category[] }) {
  return categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)
}

export function NewCategory({ onCreate }: { onCreate: (name: string) => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function cancel() {
    setOpen(false)
    setName('')
    setError('')
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!name.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      await onCreate(name.trim())
      cancel()
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return <button className="button text-button" onClick={() => setOpen(true)}><Icon name="plus" size={15} />New category</button>
  }

  return (
    <form className="category-form" onSubmit={submit}>
      <div className="inline-fields">
        <input aria-label="Category name" placeholder="Category name" autoFocus maxLength={60}
          value={name} onChange={event => setName(event.target.value)} disabled={busy} />
        <button className="button primary" disabled={!name.trim() || busy}>Add</button>
        <button className="button icon-button" type="button" disabled={busy} onClick={cancel} aria-label="Cancel new category">
          <Icon name="close" size={16} />
        </button>
      </div>
      {error && <p className="field-error" role="alert">{error}</p>}
    </form>
  )
}
