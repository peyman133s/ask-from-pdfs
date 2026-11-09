export const UNCATEGORIZED = 'uncategorized'
export const ACCEPTED_EXTENSIONS = ['.xls', '.xlsx', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg']
export const MAX_UPLOAD_FILES = 20
export const MAX_FILE_BYTES = 50 * 1024 * 1024

export type Status = 'uploaded' | 'ingesting' | 'ready' | 'failed'
export type Category = { id: string; name: string }
export type LibraryFile = {
  id: string
  name: string
  extension: string
  category_id: string
  size: number
  created_at: string
  status: Status
  error: string | null
}
export type Source = {
  number: number
  file_id: string
  filename: string
  location: string | null
  excerpt: string
}
export type Answer = { answer: string; sources: Source[] }
export type UploadItem = { id: number; file: File; categoryId: string }

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, options)
  } catch {
    throw new Error('Could not connect to the local workspace. Check that the server is running.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new Error(detail ?? `The workspace returned HTTP ${response.status}. Try again.`)
  }
  return response.json() as Promise<T>
}

function json(method: 'POST' | 'PATCH', body: object): RequestInit {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
}

export const api = {
  files: (signal?: AbortSignal) => request<LibraryFile[]>('/files', { signal }),
  categories: (signal?: AbortSignal) => request<Category[]>('/categories', { signal }),
  addCategory: (name: string) => request<Category>('/categories', json('POST', { name })),
  assign: (fileId: string, categoryId: string) =>
    request<LibraryFile>(`/files/${fileId}`, json('PATCH', { category_id: categoryId })),
  upload: (items: UploadItem[]) => {
    const form = new FormData()
    for (const item of items) {
      form.append('files', item.file)
      form.append('category_ids', item.categoryId)
    }
    return request<LibraryFile[]>('/files', { method: 'POST', body: form })
  },
  ingest: (fileIds: string[]) => request<{ file_ids: string[] }>('/ingest', json('POST', { file_ids: fileIds })),
  ask: (question: string, categoryId: string) =>
    request<Answer>('/ask', json('POST', { question, category_id: categoryId || null })),
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Try again.'
}
