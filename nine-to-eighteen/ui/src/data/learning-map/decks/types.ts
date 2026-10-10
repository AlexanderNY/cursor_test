/** Карточка пула Anki (отдельно от structured.anki статьи). */
export type PoolCard = {
  id: string
  front: string
  back: string
  /** Slug Learn-статьи для ссылки «открыть статью». */
  learnSlug: string
  tags?: string[]
}

/** Колода по ветке карты (`##` в interview-prep.md). */
export type TopicDeck = {
  /** Точное название ветки на карте, напр. «Python». */
  branchTitle: string
  /** Короткая пометка об источнике формулировок (лицензия). */
  sourceNote?: string
  cards: PoolCard[]
}
