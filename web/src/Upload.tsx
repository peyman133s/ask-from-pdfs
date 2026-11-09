import { useEffect, useRef, useState } from 'react'
import {
  ACCEPTED_EXTENSIONS, api, errorMessage, MAX_FILE_BYTES, MAX_UPLOAD_FILES, UNCATEGORIZED,
} from './api'
import type { Category, UploadItem } from './api'
import { CategoryOptions, FileLabel, Icon, NewCategory } from './components'

type UploadProps = {
  categories: Category[]
  onCreateCategory: (name: string) => Promise<void>
  onUploaded: () => void
  onClose: () => void
}

export function Upload({ categories, onCreateCategory, onUploaded, onClose }: UploadProps) {
  const dialog = useRef<HTMLDialogElement>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const nextId = useRef(0)
  const [items, setItems] = useState<UploadItem[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    return () => element?.close()
  }, [])

  function addFiles(files: FileList | File[]) {
    if (busy) return
    const accepted: UploadItem[] = []
    const issues: string[] = []
    for (const file of files) {
      if (items.length + accepted.length >= MAX_UPLOAD_FILES) {
        issues.push(`Choose up to ${MAX_UPLOAD_FILES} files per upload.`)
        break
      }
      if (!ACCEPTED_EXTENSIONS.some(extension => file.name.toLowerCase().endsWith(extension))) {
        issues.push(`${file.name} is an unsupported file type.`)
      } else if (!file.size || file.size > MAX_FILE_BYTES) {
        issues.push(`${file.name} ${file.size ? 'exceeds the 50 MiB file limit' : 'is empty'}.`)
      } else {
        accepted.push({ id: nextId.current++, file, categoryId: UNCATEGORIZED })
      }
    }
    setErrors(issues)
    setItems(current => [...current, ...accepted])
  }

  async function upload() {
    if (!items.length || busy) return
    setBusy(true)
    setErrors([])
    try {
      await api.upload(items)
      onUploaded()
    } catch (cause) {
      setErrors([errorMessage(cause)])
      setBusy(false)
    }
  }

  return (
    <dialog ref={dialog} className="upload-dialog" aria-labelledby="upload-title"
      onCancel={event => { event.preventDefault(); if (!busy) onClose() }}>
      <div className="dialog-header">
        <div>
          <h2 id="upload-title">Upload files</h2>
          <p>Add files and choose a category for each one.</p>
        </div>
        <button className="button icon-button" aria-label="Close upload" disabled={busy} onClick={onClose}>
          <Icon name="close" />
        </button>
      </div>
      <div className={`drop-zone${dragging ? ' dragging' : ''}`}
        onDragOver={event => { event.preventDefault(); setDragging(!busy) }}
        onDragLeave={event => {
          if (!(event.relatedTarget instanceof Node) || !event.currentTarget.contains(event.relatedTarget)) setDragging(false)
        }}
        onDrop={event => {
          event.preventDefault()
          setDragging(false)
          addFiles(event.dataTransfer.files)
        }}>
        <span className="drop-icon"><Icon name="upload" size={20} /></span>
        <strong>Drag and drop files here</strong>
        <input ref={fileInput} type="file" multiple hidden disabled={busy} accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={event => {
            if (event.target.files) addFiles(event.target.files)
            event.target.value = ''
          }} />
        <button className="button small" onClick={() => fileInput.current?.click()} disabled={busy}>Browse files</button>
        <p>XLS, XLSX, PDF, DOC, DOCX, PNG, JPG, JPEG · Up to 50 MiB each</p>
      </div>
      <div className="queue">
        <div className="queue-header">
          <h3>Selected files {items.length > 0 && <span className="count">{items.length}</span>}</h3>
          {!busy && <NewCategory onCreate={onCreateCategory} />}
        </div>
        {items.length === 0 && <p className="muted">Choose files to add them to the list.</p>}
        <ul className="upload-list">
          {items.map(item => (
            <li key={item.id} className="upload-row">
              <FileLabel name={item.file.name} />
              <div className="inline-fields">
                <select className="category-select" aria-label={`Category for ${item.file.name}`}
                  value={item.categoryId} disabled={busy}
                  onChange={event => {
                    const categoryId = event.target.value
                    setItems(current => current.map(file => file.id === item.id ? { ...file, categoryId } : file))
                  }}>
                  <CategoryOptions categories={categories} />
                </select>
                <button className="button icon-button" aria-label={`Remove ${item.file.name}`} disabled={busy}
                  onClick={() => setItems(current => current.filter(file => file.id !== item.id))}>
                  <Icon name="close" size={15} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
      {errors.length > 0 && <ul className="upload-errors field-error" role="alert">{errors.map((error, index) => <li key={index}>{error}</li>)}</ul>}
      <div className="dialog-footer">
        <p>Ingest files from the library after upload.</p>
        <div className="inline-fields">
          <button className="button" onClick={onClose} disabled={busy}>Cancel</button>
          <button className="button primary" onClick={upload} disabled={busy || !items.length}>
            {busy ? 'Uploading…' : items.length ? `Upload ${items.length} ${items.length === 1 ? 'file' : 'files'}` : 'Upload files'}
          </button>
        </div>
      </div>
    </dialog>
  )
}
