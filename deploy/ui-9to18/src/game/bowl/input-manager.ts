import type { InputVector } from './types'

type JoystickListener = (vector: InputVector) => void

export class InputManager {
  private keys = new Set<string>()
  private joystick: InputVector = { x: 0, y: 0 }
  private joystickListener: JoystickListener | null = null
  private actionQueued = false
  private sprintHeld = false

  attach(): () => void {
    const onKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase()
      this.keys.add(key)
      if (key === ' ' || key === 'e') {
        this.actionQueued = true
        event.preventDefault()
      }
    }
    const onKeyUp = (event: KeyboardEvent) => {
      this.keys.delete(event.key.toLowerCase())
    }
    const onBlur = () => {
      this.keys.clear()
      this.sprintHeld = false
    }

    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    window.addEventListener('blur', onBlur)

    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      window.removeEventListener('blur', onBlur)
      this.keys.clear()
      this.joystick = { x: 0, y: 0 }
      this.actionQueued = false
      this.sprintHeld = false
    }
  }

  setJoystickListener(listener: JoystickListener | null): void {
    this.joystickListener = listener
  }

  setJoystick(vector: InputVector): void {
    this.joystick = vector
    this.joystickListener?.(vector)
  }

  consumeAction(): boolean {
    if (!this.actionQueued) return false
    this.actionQueued = false
    return true
  }

  triggerAction(): void {
    this.actionQueued = true
  }

  setSprintHeld(held: boolean): void {
    this.sprintHeld = held
  }

  getVector(): InputVector {
    let x = this.joystick.x
    let y = this.joystick.y

    if (this.keys.has('a') || this.keys.has('arrowleft')) x -= 1
    if (this.keys.has('d') || this.keys.has('arrowright')) x += 1
    if (this.keys.has('w') || this.keys.has('arrowup')) y -= 1
    if (this.keys.has('s') || this.keys.has('arrowdown')) y += 1

    const length = Math.hypot(x, y)
    if (length > 1) {
      return { x: x / length, y: y / length }
    }
    return { x, y }
  }

  isSprinting(): boolean {
    return this.keys.has('shift') || this.sprintHeld
  }
}

export const inputManager = new InputManager()
