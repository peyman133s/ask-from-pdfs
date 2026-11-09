import { useState } from 'react'
import { api, errorMessage, MAX_UPLOAD_FILES } from './api'
import type { Category, LibraryFile, Status } from './api'
import { CategoryOptions, FileLabel, Icon, NewCategory } from './components'
import { Upload } from './Upload'

const statusLabels: Record<Status, string> = {
  uploaded: 'Uploaded', ingesting: 'Ingesting', ready: 'Ready', failed: 'Failed',
}
const statuses = Object.keys(statusLabels) as Status[]
const eligible = (file: LibraryFile) => file.status === 'uploaded' || file.status === 'failed'

type LibraryProps = {
  files: LibraryFile[]
  categories: Category[]
  loading: boolean
  refreshFiles: () => Promise<void>
  onCreateCategory: (name: string) => Promise<void>
}

export function Library({ files, categories, loading, refreshFiles, onCreateCategory }: LibraryProps) {
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState<Status | ''>('')
  const [selected, setSelected] = useState<string[]>([])
  const [uploadOpen, setUploadOpen] = useState(false)
  const [pendingFile, setPendingFile] = useState('')
  const [queueing, setQueueing] = useState(false)
  const [error, setError] = useState('')

  const visible = files.filter(file => (!category || file.category_id === category) && (!status || file.status === status))
  const eligibleIds = visible.filter(eligible).map(file => file.id)
  const selectedIds = eligibleIds.filter(id => selected.includes(id))
  const selectableIds = eligibleIds.slice(0, MAX_UPLOAD_FILES)
  const allSelected = selectableIds.length > 0 && selectableIds.every(id => selectedIds.includes(id))
  const ready = files.filter(file => file.status === 'ready').length
  const active = files.filter(file => file.status === 'ingesting').length

  async function queue(ids: string[]) {
    setError('')
    setQueueing(true)
    try {
      await api.ingest(ids)
      setSelected(current => current.filter(id => !ids.includes(id)))
      await refreshFiles()
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setQueueing(false)
    }
  }

  async function assign(file: LibraryFile, categoryId: string) {
    setPendingFile(file.id)
    setError('')
    try {
      await api.assign(file.id, categoryId)
      await refreshFiles()
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setPendingFile('')
    }
  }

  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">Document workspace</p>
          <h1>File Library</h1>
          <p className="subtitle">Upload, organize, and ingest your files.</p>
        </div>
        <button className="button primary" onClick={() => setUploadOpen(true)} disabled={loading}>
          <Icon name="upload" /> Upload files
        </button>
      </header>

      <div className="library-controls">
        <div className="category-controls">
          <select aria-label="Filter by category" value={category} onChange={event => {
            setCategory(event.target.value)
            setSelected([])
          }}>
            <option value="">All categories</option>
            <CategoryOptions categories={categories} />
          </select>
          <NewCategory onCreate={onCreateCategory} />
        </div>
        <div className="status-filters" role="group" aria-label="Filter by status">
          {(['', ...statuses] as const).map(filter => (
            <button key={filter} aria-pressed={status === filter} onClick={() => { setStatus(filter); setSelected([]) }}>
              {filter ? statusLabels[filter] : 'All'}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="notice error" role="alert">{error}</p>}
      <section className="panel library-panel" aria-label="Files">
        {selectedIds.length > 0 && (
          <div className="selection-bar">
            <span>{selectedIds.length} selected</span>
            <button className="button primary small" disabled={queueing} onClick={() => void queue(selectedIds)}>
              {queueing ? 'Queuing…' : 'Ingest selected'}
            </button>
          </div>
        )}
        {visible.length === 0 ? (
          <div className="empty-library">
            <span className="empty-icon"><Icon name="library" size={25} /></span>
            <h2>{loading ? 'Loading files…' : files.length ? 'No matching files' : 'Your library is empty'}</h2>
            <p>{loading ? 'Opening the local workspace.' : files.length ? 'Try another category or status.' : 'Upload your first files to start building a searchable library.'}</p>
            {!loading && !files.length && (
              <button className="button" onClick={() => setUploadOpen(true)}><Icon name="upload" /> Upload files</button>
            )}
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th className="checkbox-cell">
                    <input type="checkbox" aria-label="Select up to 20 eligible files" checked={allSelected}
                      disabled={!eligibleIds.length || queueing}
                      onChange={event => setSelected(event.target.checked ? selectableIds : [])} />
                  </th>
                  <th scope="col">File</th>
                  <th scope="col">Category</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {visible.map(file => {
                  const checked = selectedIds.includes(file.id)
                  return (
                    <tr key={file.id} className={checked ? 'selected-row' : undefined}>
                      <td className="checkbox-cell">
                        <input type="checkbox" checked={checked} aria-label={`Select ${file.name}`}
                          disabled={!eligible(file) || queueing || (!checked && selectedIds.length >= MAX_UPLOAD_FILES)}
                          onChange={event => setSelected(event.target.checked ? [...selectedIds, file.id] : selectedIds.filter(id => id !== file.id))} />
                      </td>
                      <td className="file-cell"><FileLabel name={file.name} /></td>
                      <td>
                        <select className="category-select" value={file.category_id} aria-label={`Category for ${file.name}`}
                          disabled={!!pendingFile} onChange={event => void assign(file, event.target.value)}>
                          <CategoryOptions categories={categories} />
                        </select>
                      </td>
                      <td className="status-cell">
                        <div className="file-status">
                          <span className={`status status-${file.status}`}>{statusLabels[file.status]}</span>
                          {file.status === 'failed' && (
                            <button className="button text-button small" disabled={queueing} onClick={() => void queue([file.id])}
                              aria-label={`Retry ${file.name}`}>Retry</button>
                          )}
                        </div>
                        {file.error && <p className="file-error">{file.error}</p>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        <footer className="panel-footer" aria-live="polite">
          <span>{visible.length} {visible.length === 1 ? 'file' : 'files'}</span>
          <span>{active > 0 && `${active} ingesting · `}{ready} ready to ask</span>
        </footer>
      </section>

      {uploadOpen && (
        <Upload categories={categories} onCreateCategory={onCreateCategory} onClose={() => setUploadOpen(false)}
          onUploaded={() => {
            setUploadOpen(false)
            setCategory('')
            setStatus('')
            setSelected([])
            setError('')
            void refreshFiles().catch(cause => setError(errorMessage(cause)))
          }} />
      )}
    </>
  )
}
