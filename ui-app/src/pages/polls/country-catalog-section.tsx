import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type { GameCountry, GameMode } from '@/types/game'
import { MediaLibrarySection } from './media-library-section'

type CatalogFilter = 'all' | 'in_game' | 'off' | 'incomplete'
type ImageTarget = 'flag' | 'map'

interface CountryCatalogSectionProps {
  mode: GameMode
  onModeSaved: () => Promise<void>
}

function formatCount(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('ru-RU').format(value)
}

function statusLabel(country: GameCountry): string {
  if (!country.is_active) return 'выключена'
  if (!country.flag_image_url) return 'нет флага'
  if (!country.map_image_url) return 'нет карты'
  return 'в игре'
}

function compositionHint(mode: GameMode, readyCount: number): string {
  const ready = `Готовых стран: ${readyCount}.`
  if (mode.mode_type === 'country_training') {
    return `Тренировка листает карточки случайных стран из включённых, не больше ${mode.questions_per_game} за партию. ${ready}`
  }
  if (mode.mode_type === 'country_flags') {
    return `Флаги задают ${mode.questions_per_game} вопросов за партию по фото флага. ${ready}`
  }
  return `«Страна на карте» задаёт ${mode.questions_per_game} вопросов за партию по карте. ${ready}`
}

export function QuestionsPerGameEditor({
  mode,
  onSaved,
}: {
  mode: GameMode
  onSaved: () => Promise<void>
}) {
  const [value, setValue] = useState(String(mode.questions_per_game))
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    setValue(String(mode.questions_per_game))
  }, [mode.id, mode.questions_per_game])

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    const parsed = Number.parseInt(value, 10)
    if (!Number.isFinite(parsed) || parsed < 1 || parsed > 300) {
      setError('Укажите число от 1 до 300')
      setSuccess('')
      return
    }
    setIsSaving(true)
    setError('')
    setSuccess('')
    try {
      await gameService.updateMode(mode.id, { questions_per_game: parsed })
      await onSaved()
      setSuccess('Число вопросов за партию сохранено')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить число вопросов')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-2 rounded-xl border border-[var(--border-color)] p-4">
      <label className="text-sm font-medium text-[var(--text-primary)]" htmlFor="questions-per-game">
        Вопросов за партию
      </label>
      <div className="flex flex-wrap items-center gap-2">
        <Input
          id="questions-per-game"
          type="number"
          min={1}
          max={300}
          className="max-w-[140px]"
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
        <Button type="submit" isLoading={isSaving}>
          Сохранить
        </Button>
      </div>
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
    </form>
  )
}

export function CountryCatalogSection({ mode, onModeSaved }: CountryCatalogSectionProps) {
  const [countries, setCountries] = useState<GameCountry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<CatalogFilter>('all')
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [iso2, setIso2] = useState('')
  const [nameRu, setNameRu] = useState('')
  const [capitalRu, setCapitalRu] = useState('')
  const [areaKm2, setAreaKm2] = useState('')
  const [population, setPopulation] = useState('')
  const [flagUrl, setFlagUrl] = useState('')
  const [mapUrl, setMapUrl] = useState('')
  const [imageTarget, setImageTarget] = useState<ImageTarget>('flag')
  const [isSaving, setIsSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const loadCountries = useCallback(async () => {
    setError('')
    setIsLoading(true)
    try {
      const data = await gameService.listCountries()
      setCountries(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить страны')
      setCountries([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCountries()
  }, [loadCountries])

  const readyCount = useMemo(
    () => countries.filter((country) => country.is_ready).length,
    [countries],
  )

  const visibleCountries = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return countries.filter((country) => {
      if (filter === 'in_game' && !country.is_ready) return false
      if (filter === 'off' && country.is_active) return false
      if (filter === 'incomplete' && (country.is_ready || !country.is_active)) return false
      if (!needle) return true
      return (
        country.name_ru.toLowerCase().includes(needle) ||
        country.capital_ru.toLowerCase().includes(needle) ||
        country.iso2.toLowerCase().includes(needle)
      )
    })
  }, [countries, filter, query])

  function resetCountryForm() {
    setEditingId(null)
    setIsCreating(false)
    setIso2('')
    setNameRu('')
    setCapitalRu('')
    setAreaKm2('')
    setPopulation('')
    setFlagUrl('')
    setMapUrl('')
  }

  function openCreate() {
    resetCountryForm()
    setIsCreating(true)
    setImageTarget(mode.mode_type === 'country_map' ? 'map' : 'flag')
    setError('')
    setSuccess('')
  }

  function openEdit(country: GameCountry) {
    setIsCreating(false)
    setEditingId(country.id)
    setIso2(country.iso2)
    setNameRu(country.name_ru)
    setCapitalRu(country.capital_ru)
    setAreaKm2(country.area_km2 == null ? '' : String(country.area_km2))
    setPopulation(country.population == null ? '' : String(country.population))
    setFlagUrl(country.flag_image_url ?? '')
    setMapUrl(country.map_image_url ?? '')
    setImageTarget(mode.mode_type === 'country_map' ? 'map' : 'flag')
    setError('')
    setSuccess('')
  }

  function parseOptionalNumber(raw: string, label: string): number | null | 'invalid' {
    const trimmed = raw.trim()
    if (!trimmed) return null
    const parsed = Number(trimmed)
    if (!Number.isFinite(parsed) || parsed < 0) {
      setError(`${label}: укажите неотрицательное число`)
      return 'invalid'
    }
    return parsed
  }

  async function handleSaveCountry(event: FormEvent) {
    event.preventDefault()
    if (!editingId && !isCreating) return
    if (!nameRu.trim()) {
      setError('Введите название страны')
      return
    }
    if (isCreating && !/^[a-zA-Z]{2}$/.test(iso2.trim())) {
      setError('ISO-код — две латинские буквы, например FR')
      return
    }
    const area = parseOptionalNumber(areaKm2, 'Площадь')
    if (area === 'invalid') return
    const people = parseOptionalNumber(population, 'Население')
    if (people === 'invalid') return
    const populationValue = people == null ? null : Math.round(people)
    const payload = {
      name_ru: nameRu.trim(),
      capital_ru: capitalRu.trim(),
      area_km2: area,
      population: populationValue,
      flag_image_url: flagUrl.trim(),
      map_image_url: mapUrl.trim(),
    }

    setIsSaving(true)
    setError('')
    setSuccess('')
    try {
      if (editingId) {
        const updated = await gameService.updateCountry(editingId, payload)
        setCountries((prev) => prev.map((country) => (country.id === updated.id ? updated : country)))
        setSuccess(`«${updated.name_ru}» сохранена`)
      } else {
        const created = await gameService.createCountry({
          ...payload,
          iso2: iso2.trim().toUpperCase(),
          is_active: true,
        })
        setCountries((prev) =>
          [...prev, created].sort((left, right) => left.name_ru.localeCompare(right.name_ru, 'ru')),
        )
        setSuccess(`«${created.name_ru}» добавлена в состав`)
      }
      resetCountryForm()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить страну')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleDelete(country: GameCountry) {
    if (!window.confirm(`Удалить «${country.name_ru}» из состава вопросов?`)) return
    setDeletingId(country.id)
    setError('')
    setSuccess('')
    try {
      await gameService.deleteCountry(country.id)
      setCountries((prev) => prev.filter((item) => item.id !== country.id))
      if (editingId === country.id) resetCountryForm()
      setSuccess(`«${country.name_ru}» удалена`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить страну')
    } finally {
      setDeletingId(null)
    }
  }

  async function handleToggle(country: GameCountry) {
    setTogglingId(country.id)
    setError('')
    setSuccess('')
    try {
      const updated = await gameService.updateCountry(country.id, { is_active: !country.is_active })
      setCountries((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить состав')
    } finally {
      setTogglingId(null)
    }
  }

  const filters: { id: CatalogFilter; label: string }[] = [
    { id: 'all', label: 'Все' },
    { id: 'in_game', label: 'В игре' },
    { id: 'off', label: 'Выключены' },
    { id: 'incomplete', label: 'Без медиа' },
  ]

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <CardTitle className="text-lg">Состав вопросов: {mode.title}</CardTitle>
          <Button type="button" onClick={openCreate} disabled={isCreating}>
            Добавить страну
          </Button>
        </div>
        <CardDescription>
          {compositionHint(mode, readyCount)} Справочник общий для Тренировки, Флагов и Карты:
          выключенная страна пропадает из всех трёх режимов. В флаги и карту попадают только страны
          с обоими изображениями, минимум 6.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        {success && <Alert variant="success">{success}</Alert>}

        <QuestionsPerGameEditor mode={mode} onSaved={onModeSaved} />

        <div className="flex flex-wrap items-center gap-2">
          <Input
            className="min-w-[220px] flex-1"
            placeholder="Поиск по стране, столице или ISO"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          {filters.map((item) => (
            <Button
              key={item.id}
              type="button"
              size="sm"
              variant={filter === item.id ? 'primary' : 'secondary'}
              onClick={() => setFilter(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>

        {(editingId || isCreating) && (
          <form
            onSubmit={handleSaveCountry}
            className="space-y-3 rounded-xl border border-[var(--border-color)] p-4"
          >
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {isCreating ? 'Новая страна' : 'Карточка страны'}
            </h3>
            {isCreating && (
              <Input
                placeholder="ISO, две буквы (FR)"
                value={iso2}
                maxLength={2}
                onChange={(event) => setIso2(event.target.value.toUpperCase())}
              />
            )}
            <Input
              placeholder="Название"
              value={nameRu}
              onChange={(event) => setNameRu(event.target.value)}
            />
            <Input
              placeholder="Столица"
              value={capitalRu}
              onChange={(event) => setCapitalRu(event.target.value)}
            />
            <div className="grid gap-2 sm:grid-cols-2">
              <Input
                type="number"
                min={0}
                step="any"
                placeholder="Площадь, км²"
                value={areaKm2}
                onChange={(event) => setAreaKm2(event.target.value)}
              />
              <Input
                type="number"
                min={0}
                step={1}
                placeholder="Население"
                value={population}
                onChange={(event) => setPopulation(event.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[var(--text-secondary)]">Куда подставить изображение из медиатеки</label>
              <select
                className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                value={imageTarget}
                onChange={(event) => setImageTarget(event.target.value as ImageTarget)}
              >
                <option value="flag">Флаг</option>
                <option value="map">Карта</option>
              </select>
            </div>
            <Input
              placeholder="URL флага"
              value={flagUrl}
              onChange={(event) => setFlagUrl(event.target.value)}
            />
            <Input
              placeholder="URL карты"
              value={mapUrl}
              onChange={(event) => setMapUrl(event.target.value)}
            />
            <div className="flex flex-wrap gap-3">
              {flagUrl && (
                <img
                  src={flagUrl}
                  alt="Флаг"
                  className="h-16 rounded-lg border border-[var(--border-color)] object-contain"
                />
              )}
              {mapUrl && (
                <img
                  src={mapUrl}
                  alt="Карта"
                  className="h-16 rounded-lg border border-[var(--border-color)] object-contain"
                />
              )}
            </div>
            <MediaLibrarySection
              onSelectUrl={(url) => {
                if (imageTarget === 'map') {
                  setMapUrl(url)
                } else {
                  setFlagUrl(url)
                }
                setSuccess('URL изображения подставлен в карточку')
              }}
            />
            <div className="flex flex-wrap gap-2">
              <Button type="submit" isLoading={isSaving}>
                {isCreating ? 'Добавить в состав' : 'Сохранить страну'}
              </Button>
              <Button type="button" variant="secondary" onClick={resetCountryForm}>
                Отмена
              </Button>
            </div>
          </form>
        )}

        {isLoading ? (
          <TableSkeleton rows={6} />
        ) : countries.length === 0 ? (
          <EmptyState
            title="Состав пуст"
            description="Добавьте страны: они станут вопросами Тренировки, Флагов и Карты."
          />
        ) : visibleCountries.length === 0 ? (
          <EmptyState title="Ничего не найдено" description="Измените поиск или фильтр." />
        ) : (
          <div className="max-h-[32rem] overflow-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-[var(--bg-primary)]">
                <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                  <th className="pb-2 pr-3 font-medium">ISO</th>
                  <th className="pb-2 pr-3 font-medium">Страна</th>
                  <th className="pb-2 pr-3 font-medium">Столица</th>
                  <th className="pb-2 pr-3 font-medium">Площадь</th>
                  <th className="pb-2 pr-3 font-medium">Население</th>
                  <th className="pb-2 pr-3 font-medium">Состав</th>
                  <th className="pb-2 font-medium">Действия</th>
                </tr>
              </thead>
              <tbody>
                {visibleCountries.map((country) => (
                  <tr key={country.id} className="border-b border-[var(--border-color)]/60">
                    <td className="py-3 pr-3 text-[var(--text-secondary)]">{country.iso2}</td>
                    <td className="py-3 pr-3 text-[var(--text-primary)]">{country.name_ru}</td>
                    <td className="py-3 pr-3 text-[var(--text-secondary)]">{country.capital_ru || '—'}</td>
                    <td className="py-3 pr-3 text-[var(--text-secondary)]">{formatCount(country.area_km2)}</td>
                    <td className="py-3 pr-3 text-[var(--text-secondary)]">{formatCount(country.population)}</td>
                    <td className="py-3 pr-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          country.is_ready
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'
                        }`}
                      >
                        {statusLabel(country)}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={() => openEdit(country)}
                        >
                          Изменить
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          isLoading={togglingId === country.id}
                          onClick={() => handleToggle(country)}
                        >
                          {country.is_active ? 'Убрать' : 'Вернуть'}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="danger"
                          isLoading={deletingId === country.id}
                          onClick={() => handleDelete(country)}
                        >
                          Удалить
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
