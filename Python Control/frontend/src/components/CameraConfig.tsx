import { useState } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from 'react-hot-toast'

interface Camera {
  ip: string
  color: [number, number, number]
}

interface CameraConfigProps {
  index: number
  camera: Camera
  onUpdate: () => void
}

export function CameraConfig({ index, camera, onUpdate }: CameraConfigProps) {
  const [ip, setIp] = useState(camera.ip)
  const [color, setColor] = useState(camera.color.join(','))

  const handleUpdate = async () => {
    try {
      const updatedCamera = {
        ip,
        color: color.split(',').map(Number)
      }
      await axios.put(`http://localhost:9000/camera/${index}`, updatedCamera)
      toast.success('Camera updated successfully')
      onUpdate()
    } catch (error) {
      toast.error('Failed to update camera')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Camera {index + 1}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid items-center w-full gap-4">
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor={`ip-${index}`}>IP Address</Label>
            <Input id={`ip-${index}`} value={ip} onChange={(e) => setIp(e.target.value)} />
          </div>
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor={`color-${index}`}>Color (R,G,B)</Label>
            <Input id={`color-${index}`} value={color} onChange={(e) => setColor(e.target.value)} />
          </div>
          <Button onClick={handleUpdate}>Update Camera</Button>
        </div>
      </CardContent>
    </Card>
  )
}