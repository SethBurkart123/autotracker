import { useState } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from 'react-hot-toast'
import { RgbColorPicker } from 'react-colorful'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { Plus } from 'lucide-react'

interface AddCameraProps {
  onAdd: () => void
}

export function AddCamera({ onAdd }: AddCameraProps) {
  const [ip, setIp] = useState('')
  const [color, setColor] = useState({ r: 255, g: 0, b: 0 })
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  const validateInputs = () => {
    if (!ip.trim()) {
      toast.error('IP address is required')
      return false
    }
    return true
  }

  const handleAdd = async () => {
    if (!validateInputs()) return

    setIsLoading(true)
    try {
      const newCamera = {
        ip: ip.trim(),
        color: [color.r, color.g, color.b]
      }
      await axios.post('/api/camera', newCamera)
      toast.success('Camera added successfully')
      onAdd()
      setIp('')
      setColor({ r: 255, g: 0, b: 0 })
      setIsOpen(false)
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        toast.error(`Failed to add camera: ${error.response.data.detail || error.message}`)
      } else {
        toast.error('Failed to add camera. Please try again.')
      }
      console.error('Error adding camera:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Plus className="w-4 h-4 mr-2" />
          Add Camera
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add New Camera</DialogTitle>
        </DialogHeader>
        <div className="grid items-center w-full gap-4">
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor="ip">IP Address</Label>
            <Input 
              id="ip" 
              value={ip} 
              onChange={(e) => setIp(e.target.value)}
              placeholder="e.g., 192.168.1.100"
            />
          </div>
          <div className="flex flex-col space-y-1.5">
            <Label>Color</Label>
            <RgbColorPicker color={color} onChange={setColor} />
            <div className="mt-2 text-sm">
              Selected color: rgb({color.r}, {color.g}, {color.b})
            </div>
          </div>
          <Button onClick={handleAdd} disabled={isLoading}>
            {isLoading ? 'Adding...' : 'Add Camera'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}