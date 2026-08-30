import { Link } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'

type Props = {
  visible: boolean
  className?: string
}

/** Баннер учебного контура S01: demo brand без своего connected-канала. */
export function LearnModeBanner({ visible, className = '' }: Props) {
  if (!visible) return null

  return (
    <Alert variant="info" className={`mb-4 ${className}`.trim()}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm">
          <p className="font-medium text-[var(--text-primary)]">Учебный контур (сезон S01)</p>
          <p className="text-[var(--text-secondary)] mt-1">
            Демо-бренд и примерные посты только для просмотра. Публикация в прод отключена.
            Подключите свой канал, чтобы выйти из учебного режима.
          </p>
        </div>
        <Link
          to="/onboarding"
          className="shrink-0 inline-flex items-center justify-center font-medium rounded-xl px-3 py-1.5 text-sm bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700"
        >
          Пройти онбординг
        </Link>
      </div>
    </Alert>
  )
}
