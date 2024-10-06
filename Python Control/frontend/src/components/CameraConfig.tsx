import { useState } from 'react'
import axios from 'axios'
import { RgbColorPicker } from 'react-colorful'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from 'react-hot-toast'
import { Minus } from 'lucide-react'

interface Camera {
  ip: string
  color: [number, number, number]
}

interface CameraConfigProps {
  index: number
  camera: Camera
  onUpdate: () => void
  onRemove: () => void
}

export function CameraConfig({ index, camera, onUpdate, onRemove }: CameraConfigProps) {
  const [ip, setIp] = useState(camera.ip)
  const [color, setColor] = useState({ r: camera.color[0], g: camera.color[1], b: camera.color[2] })

  const handleUpdate = async () => {
    try {
      const updatedCamera = {
        ip,
        color: [color.r, color.g, color.b]
      }
      await axios.put(`http://localhost:9000/camera/${index}`, updatedCamera)
      toast.success('Camera updated successfully')
      onUpdate()
    } catch (error) {
      toast.error('Failed to update camera')
    }
  }

  return (
    <Card className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="absolute text-gray-500 top-2 right-2 hover:text-red-500"
        onClick={onRemove}
      >
        <Minus size={20} />
      </Button>
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Camera {index + 1}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div>
            <Label htmlFor={`ip-${index}`} className="text-sm font-medium">IP Address</Label>
            <Input
              id={`ip-${index}`}
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm font-medium">Color</Label>
            <div className="mt-2">
              <RgbColorPicker color={color} onChange={setColor} className="w-full max-w-[200px]" />
            </div>
          </div>
          <Button onClick={handleUpdate} className="w-full">Update Camera</Button>
        </div>
      </CardContent>
    </Card>
  )
}