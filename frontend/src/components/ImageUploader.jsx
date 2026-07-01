import React, { useState } from 'react'
import api from '../lib/api'

const EXAMPLES = [
  'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800',
  'https://picsum.photos/800/600?random=2'
]

export default function ImageUploader({ onDetect, onAnnotated }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)

  function onFileChange(e) {
    const f = e.target.files[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  async function upload() {
    if (!file) return alert('Choose a file first')
    const form = new FormData()
    form.append('file', file)
    setLoading(true)
    try {
      const resp = await api.post('/api/v1/detect', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      const { landmarks } = resp.data
      onDetect(preview, landmarks)
    } catch (err) {
      console.error(err)
      alert('Upload failed')
    } finally {
      setLoading(false)
    }
  }

  async function downloadAnnotated() {
    if (!preview) return alert('Run detection first')
    setLoading(true)
    try {
      // send the original image url or nothing; backend should accept either stored upload id or image bytes
      const resp = await api.post('/api/v1/visualize', { image_url: preview }, { responseType: 'blob' })
      const blob = resp.data
      const url = URL.createObjectURL(blob)
      onAnnotated(url)
      const a = document.createElement('a')
      a.href = url
      a.download = 'annotated_image.jpg'
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (err) {
      console.error(err)
      alert('Annotated download failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded shadow p-4">
      <h3 className="font-medium mb-2">Image</h3>

      <div>
        <input type="file" accept="image/*" onChange={onFileChange} />
      </div>

      <div className="mt-3">
        <div className="grid grid-cols-2 gap-2">
          {EXAMPLES.map((u) => (
            <img key={u} src={u} alt="example" className="h-24 w-full object-cover cursor-pointer rounded" onClick={() => { setPreview(u); setFile(null) }} />
          ))}
        </div>
      </div>

      <div className="mt-3">
        {preview && <img src={preview} alt="preview" className="rounded w-full object-contain" />}
      </div>

      <div className="mt-3 flex gap-2">
        <button onClick={upload} disabled={loading} className="px-3 py-2 bg-blue-600 text-white rounded">{loading ? 'Uploading...' : 'Upload & Detect'}</button>
        <button onClick={downloadAnnotated} disabled={loading} className="px-3 py-2 bg-green-600 text-white rounded">{loading ? 'Processing...' : 'Download annotated image'}</button>
      </div>
    </div>
  )
}
