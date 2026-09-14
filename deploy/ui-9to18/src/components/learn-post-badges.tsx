import {
  LEARN_KNOWLEDGE_MAP_TAG,
  hasKnowledgeMapTag,
  levelLabel,
  profileLabel,
  type LearnLevelId,
  type LearnProfileId,
} from '@/data/learn/labels'

type LearnPostBadgesProps = {
  profiles?: LearnProfileId[]
  level?: LearnLevelId | ''
  tags?: string[]
  durationMin?: number
  className?: string
}

export function LearnPostBadges({
  profiles = [],
  level = '',
  tags = [],
  durationMin = 0,
  className = '',
}: LearnPostBadgesProps) {
  const hasAnything =
    profiles.length > 0 || Boolean(level) || tags.length > 0 || durationMin > 0
  if (!hasAnything) {
    return null
  }

  const onMap = hasKnowledgeMapTag(tags)
  const otherTags = tags.filter(
    (tag) => tag.trim().toLowerCase() !== LEARN_KNOWLEDGE_MAP_TAG.toLowerCase(),
  )

  return (
    <div className={`learn-badges ${className}`.trim()} aria-label="Лейблы выпуска">
      {onMap ? (
        <span className="learn-badge learn-badge-map">{LEARN_KNOWLEDGE_MAP_TAG}</span>
      ) : null}
      {profiles.map((id) => (
        <span key={`p-${id}`} className="learn-badge learn-badge-track">
          Трек: {profileLabel(id)}
        </span>
      ))}
      {level ? (
        <span className="learn-badge learn-badge-level">Уровень: {levelLabel(level)}</span>
      ) : null}
      {durationMin > 0 ? (
        <span className="learn-badge learn-badge-duration">~{durationMin} мин</span>
      ) : null}
      {otherTags.map((tag) => (
        <span key={`t-${tag}`} className="learn-badge learn-badge-tag">
          {tag}
        </span>
      ))}
    </div>
  )
}
