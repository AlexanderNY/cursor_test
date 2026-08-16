import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { ConditionsMode } from '@/types/smm'

export interface ConditionsEditorProps {
  conditions: string[]
  mode: ConditionsMode
  onConditionsChange: (conditions: string[]) => void
  onModeChange: (mode: ConditionsMode) => void
  disabled?: boolean
  maxItems?: number
  placeholder?: string
  showMode?: boolean
}

export function ConditionsEditor({
  conditions,
  mode,
  onConditionsChange,
  onModeChange,
  disabled = false,
  maxItems = 20,
  placeholder = 'Enter condition (e.g. keyword)',
  showMode = true,
}: ConditionsEditorProps) {
  const displayRows =
    conditions.length === 0 ? [''] : conditions.map((value) => value)

  function setAt(index: number, value: string) {
    if (conditions.length === 0 && index === 0) {
      onConditionsChange([value])
      return
    }
    const next = [...conditions]
    next[index] = value
    onConditionsChange(next)
  }

  function removeAt(index: number) {
    onConditionsChange(conditions.filter((_, i) => i !== index))
  }

  function addRow() {
    if (conditions.length >= maxItems) return
    if (conditions.length === 0) {
      onConditionsChange([''])
      return
    }
    onConditionsChange([...conditions, ''])
  }

  const canRemove =
    conditions.length > 1 || (conditions.length === 1 && Boolean(conditions[0]?.trim()))

  return (
    <div className="space-y-3">
      {showMode && (
        <label className="flex items-center gap-2 text-sm">
          <span className="text-[var(--text-secondary)]">Conditions mode</span>
          <select
            className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1 text-sm"
            value={mode}
            disabled={disabled}
            onChange={(e) => onModeChange(e.target.value as ConditionsMode)}
          >
            <option value="any_of">Any (OR)</option>
            <option value="all_of">All (AND)</option>
          </select>
        </label>
      )}
      <div className="space-y-2">
        {displayRows.map((value, index) => (
          <div key={`cond-${index}`} className="flex gap-2">
            <Input
              placeholder={placeholder}
              value={value}
              disabled={disabled}
              onChange={(e) => setAt(index, e.target.value)}
              className="flex-1"
            />
            {canRemove && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled={disabled}
                onClick={() => removeAt(index)}
                className="px-3 text-red-400 hover:text-red-300"
                aria-label="Remove condition"
              >
                ×
              </Button>
            )}
          </div>
        ))}
      </div>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={disabled || conditions.length >= maxItems}
        onClick={addRow}
      >
        Add condition
      </Button>
    </div>
  )
}
