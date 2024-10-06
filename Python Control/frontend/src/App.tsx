import { useState, useEffect } from 'react'
import axios from 'axios'
import { ThemeToggle } from './components/ThemeToggle'
import { CameraConfig } from './components/CameraConfig'
import { AddCamera } from './components/AddCamera'
import { Button } from "@/components/ui/button"
import { toast, Toaster } from 'react-hot-toast'
import { Loader2, Plus } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from "@/components/ui/dialog"

interface Camera {
  ip: string
  color: [number, number, number]
}

interface Config {
  cameras: Camera[]
}

function App() {
  const [config, setConfig] = useState<Config | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const fetchConfig = async () => {
    setIsLoading(true)
    try {
      const response = await axios.get('http://localhost:9000/config')
      setConfig(response.data)
    } catch (error) {
      toast.error('Failed to fetch configuration')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchConfig()
  }, [])

  const handleRefresh = () => {
    fetchConfig()
  }

  const handleRemoveCamera = async (index: number) => {
    try {
      await axios.delete(`http://localhost:9000/camera/${index}`)
      toast.success('Camera removed successfully')
      fetchConfig()
    } catch (error) {
      toast.error('Failed to remove camera')
    }
  }

  return (
    <div className="container max-w-6xl p-4 mx-auto">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Camera Configuration</h1>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm" onClick={fetchConfig} disabled={isLoading}>
            {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            Refresh
          </Button>
          <AddCamera onAdd={() => {
                fetchConfig()
              }} />
          <ThemeToggle />
        </div>
      </header>

      {config ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {config.cameras.map((camera, index) => (
            <CameraConfig 
              key={index} 
              index={index} 
              camera={camera} 
              onUpdate={fetchConfig}
              onRemove={() => handleRemoveCamera(index)}
            />
          ))}
        </div>
      ) : (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin" />
          <span className="ml-2 text-lg">Loading configuration...</span>
        </div>
      )}
      <Toaster />
    </div>
  )
}

export default App