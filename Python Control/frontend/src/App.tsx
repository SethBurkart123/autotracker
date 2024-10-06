import { useState, useEffect } from 'react'
import axios from 'axios'
import { ThemeToggle } from './components/ThemeToggle'
import { CameraConfig } from './components/CameraConfig'
import { Button } from "@/components/ui/button"
import { toast, Toaster } from 'react-hot-toast'

interface Camera {
  ip: string
  color: [number, number, number]
}

interface Config {
  cameras: Camera[]
}

function App() {
  const [config, setConfig] = useState<Config | null>(null)

  const fetchConfig = async () => {
    try {
      const response = await axios.get('http://localhost:9000/config')
      setConfig(response.data)
    } catch (error) {
      toast.error('Failed to fetch configuration')
    }
  }

  useEffect(() => {
    fetchConfig()
  }, [])

  const handleRefresh = () => {
    fetchConfig()
  }

  return (
    <div className="container p-4 mx-auto">
      <header className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Camera Configuration</h1>
        <div className="flex space-x-4">
          <Button onClick={handleRefresh}>Refresh</Button>
          <ThemeToggle />
        </div>
      </header>
      {config ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {config.cameras.map((camera, index) => (
            <CameraConfig key={index} index={index} camera={camera} onUpdate={fetchConfig} />
          ))}
        </div>
      ) : (
        <p>Loading configuration...</p>
      )}
      <Toaster />
    </div>
  )
}

export default App