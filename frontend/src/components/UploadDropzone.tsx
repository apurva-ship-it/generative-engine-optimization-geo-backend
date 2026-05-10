import React, { useState, DragEvent } from 'react'

interface UploadDropzoneProps {
  /**
   * Callback invoked with the accepted files. The array length will be <=5 and each file will be <=50MB.
   */
  onFilesAccepted: (files: File[]) => void
}

const MAX_FILES = 5
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 // 50 MB

const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onFilesAccepted }) => {
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()

    const droppedFiles = Array.from(e.dataTransfer.files)
    const filtered = droppedFiles.filter(file => {
      if (file.size > MAX_FILE_SIZE_BYTES) {
        setError(`File ${file.name} exceeds 50 MB size limit.`)
        return false
      }
      return true
    })

    if (filtered.length + files.length > MAX_FILES) {
      setError(`Cannot upload more than ${MAX_FILES} files at a time.`)
      return
    }

    const newFiles = [...files, ...filtered]
    setFiles(newFiles)
    setError(null)
    onFilesAccepted(newFiles)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  return (
    <div
      className="border-2 border-dashed border-gray-300 rounded-md p-6 text-center"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      role="region"
      aria-label="File upload dropzone"
    >
      <p className="mb-2">Drag & drop files here, or click to select.</p>
      <input
        type="file"
        multiple
        accept="*/*"
        className="hidden"
        onChange={e => {
          const inputFiles = Array.from(e.target.files ?? [])
          const filtered = inputFiles.filter(file => file.size <= MAX_FILE_SIZE_BYTES)
          if (filtered.length + files.length > MAX_FILES) {
            setError(`Cannot upload more than ${MAX_FILES} files at a time.`)
            return
          }
          const newFiles = [...files, ...filtered]
          setFiles(newFiles)
          setError(null)
          onFilesAccepted(newFiles)
        }}
        aria-label="File selector"
      />
      {error && <p className="text-red-500">{error}</p>}
      <ul className="mt-4 text-left max-h-40 overflow-y-auto">
        {files.map((file, i) => (
          <li key={i} className="text-sm">
            {file.name} – {Math.round(file.size / 1024)} KB
          </li>
        ))}
      </ul>
    </div>
  )
}

export default UploadDropzone
