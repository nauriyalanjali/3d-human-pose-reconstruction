import React, { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import PoseVisualizer from './components/PoseVisualizer'
import ResultsPanel from './components/ResultsPanel'

export default function App() {
  const [landmarks, setLandmarks] = useState(null)
  const [imageSrc, setImageSrc] = useState(null)
  const [annotatedBlobUrl, setAnnotatedBlobUrl] = useState(null)

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-semibold">3D Human Pose Reconstruction — Demo</h1>
        <p className="mt-2 text-sm text-gray-600">Upload an image or choose an example to detect pose landmarks. Download an annotated image after detection.</p>
      </header>

      <main className="max-w-4xl mx-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <section className="md:col-span-1">
          <ImageUploader
            onDetect={(imgSrc, lm) => {
              setImageSrc(imgSrc)
              setLandmarks(lm)
            }}
            onAnnotated={(blobUrl) => setAnnotatedBlobUrl(blobUrl)}
          />
        </section>

        <section className="md:col-span-2">
          <div className="bg-white rounded shadow p-4">
            <h2 className="text-lg font-medium mb-2">Visualizer</h2>
            <div className="h-96">
              <PoseVisualizer imageSrc={imageSrc} landmarks={landmarks} />
            </div>
            <ResultsPanel
              imageSrc={imageSrc}
              landmarks={landmarks}
              annotatedBlobUrl={annotatedBlobUrl}
            />
          </div>
        </section>
      </main>

      <footer className="max-w-4xl mx-auto p-6 text-sm text-gray-500">
        Built with ❤️ — demo for your portfolio
      </footer>
    </div>
  )
}
