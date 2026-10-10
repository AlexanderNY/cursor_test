import type { TopicDeck } from '@/data/learning-map/decks/types'
import { deckAnalytics } from '@/data/learning-map/decks/analytics'
import { deckData } from '@/data/learning-map/decks/data'
import { deckDev } from '@/data/learning-map/decks/dev'
import { deckDevops } from '@/data/learning-map/decks/devops'
import { deckJava } from '@/data/learning-map/decks/java'
import { deckJavascript } from '@/data/learning-map/decks/javascript'
import { deckProduct } from '@/data/learning-map/decks/product'
import { deckPython } from '@/data/learning-map/decks/python'
import { deckQa } from '@/data/learning-map/decks/qa'
import { deckRedis } from '@/data/learning-map/decks/redis'
import { deckSa } from '@/data/learning-map/decks/sa'
import { deckSecurity } from '@/data/learning-map/decks/security'
import { deckSoftSkills } from '@/data/learning-map/decks/soft-skills'
import { deckSql } from '@/data/learning-map/decks/sql'
import { deckTesting } from '@/data/learning-map/decks/testing'
import { deckTools } from '@/data/learning-map/decks/tools'

export type { PoolCard, TopicDeck } from '@/data/learning-map/decks/types'

/** Все тематические пулы Anki для карты. */
export const TOPIC_DECKS: TopicDeck[] = [
  deckDev,
  deckAnalytics,
  deckData,
  deckTools,
  deckDevops,
  deckSecurity,
  deckTesting,
  deckSoftSkills,
  deckPython,
  deckSql,
  deckJava,
  deckJavascript,
  deckQa,
  deckSa,
  deckRedis,
  deckProduct,
]
