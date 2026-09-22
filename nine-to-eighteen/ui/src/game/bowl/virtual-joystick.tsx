import { useCallback, useRef } from 'react'
import type { InputVector } from './types'

interface VirtualJoystickProps {
  onChange: (vector: InputVector) => void
}

const MAX_RADIUS = 52

export function VirtualJoystick({ onChange }: VirtualJoystickProps) {
  const baseRef = useRef<HTMLDivElement>(null)
  const stickRef = useRef<HTMLDivElement>(null)
  const pointerIdRef = useRef<number | null>(null)

  const resetStick = useCallback(() => {
    if (stickRef.current) {
      stickRef.current.style.transform = 'translate(-50%, -50%)'
    }
    onChange({ x: 0, y: 0 })
  }, [onChange])

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (pointerIdRef.current !== null) return
    pointerIdRef.current = event.pointerId
    event.currentTarget.setPointerCapture(event.pointerId)
    updateStick(event)
  }

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (pointerIdRef.current !== event.pointerId) return
    updateStick(event)
  }

  const handlePointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
    if (pointerIdRef.current !== event.pointerId) return
    pointerIdRef.current = null
    event.currentTarget.releasePointerCapture(event.pointerId)
    resetStick()
  }

  const updateStick = (event: React.PointerEvent<HTMLDivElement>) => {
    const base = baseRef.current
    const stick = stickRef.current
    if (!base || !stick) return

    const rect = base.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const dx = event.clientX - centerX
    const dy = event.clientY - centerY
    const distance = Math.hypot(dx, dy)
    const clampedDistance = Math.min(distance, MAX_RADIUS)
    const angle = Math.atan2(dy, dx)
    const offsetX = Math.cos(angle) * clampedDistance
    const offsetY = Math.sin(angle) * clampedDistance

    stick.style.transform = `translate(calc(-50% + ${offsetX}px), calc(-50% + ${offsetY}px))`

    if (clampedDistance === 0) {
      onChange({ x: 0, y: 0 })
      return
    }

    onChange({
      x: offsetX / MAX_RADIUS,
      y: offsetY / MAX_RADIUS,
    })
  }

  return (
    <div
      ref={baseRef}
      className="bowl-joystick"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <div ref={stickRef} className="bowl-joystick-stick" />
    </div>
  )
}
