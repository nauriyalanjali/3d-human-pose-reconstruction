import React from 'react'
import api from '../lib/api'

export default function ResultsPanel({ imageSrc, landmarks, annotatedBlobUrl }) {
  async function downloadAnnotated() {
    try {
      if (annotatedBlobUrl) {
        const a = document.createElement('a')
        a.href = annotatedBlobUrl
        a.download = 'annotated_image.jpg'
        document.body.appendChild(a)
        a.click()
        a.remove()
        return
      }

      // Fallback: request visualization from backend
      const resp = await api.post('/api/v1/visualize', { image_url: imageSrc }, { responseType: 'blob' })
      const blob = resp.data
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'annotated_image.jpg'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
      alert('Failed to download annotated image')
    }
  }

  return (
    <div className="mt-4">
      <h3 className="font-medium">Results</h3>
      {!landmarks && <p className="text-sm text-gray-500">No landmarks yet — upload an image and click "Upload & Detect".</p>}

      {landmarks && (
        <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-3 rounded h-48 overflow-auto">
            <h4 className="font-semibold">Landmarks</h4>
            <ol className="text-sm list-decimal pl-4">
              {landmarks.map((lm, i) => (
                <li key={i} className="py-1">
                  <span className="font-medium">{i}</span>: x={lm.x.toFixed(3)}, y={lm.y.toFixed(3)} {lm.z !== undefined ? `, z=${lm.z.toFixed(3)}` : ''} {lm.score ? `, conf=${lm.score.toFixed(2)}` : ''}
                </li>
              ))}
            </ol>
          </div>

          <div className="bg-gray-50 p-3 rounded">
            <h4 className="font-semibold">Actions</h4>
            <p className="text-sm text-gray-600">You can download an annotated image (overlay + watermark) produced by the backend.</p>
            <div className="mt-3">
              <button onClick={downloadAnnotated} className="px-3 py-2 bg-green-600 text-white rounded">Download annotated image</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
