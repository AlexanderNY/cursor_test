import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ContactForm } from '@/components/contact-form'
import { PageShell } from '@/components/page-shell'
import { PromoSpotlight } from '@/components/promo-spotlight'
import { SectionTile } from '@/components/section-tile'
import { siteGetPromo, siteListApps, type SiteApp } from '@/data/site/site-api'
import { DEFAULT_SITE_PROMO, normalizeSitePromo, type SitePromo } from '@/data/promo'
import { sections as fallbackSections, type Section } from '@/data/sections'

function appToSection(app: SiteApp): Section {
  return {
    slug: app.slug,
    title: app.title,
    subtitle: app.subtitle,
    description: app.description,
    accent: app.accent,
    emoji: app.emoji || undefined,
    href: app.externalHref || undefined,
    appPath: app.appPath || undefined,
  }
}

export function HomePage() {
  const location = useLocation()
  const [promo, setPromo] = useState<SitePromo>(DEFAULT_SITE_PROMO)
  const [tiles, setTiles] = useState<Section[]>(fallbackSections)

  useEffect(() => {
    if (!location.hash) {
      return
    }
    const id = location.hash.slice(1)
    const el = document.getElementById(id)
    if (!el) {
      return
    }
    // scroll-margin-top on the target keeps the sticky header from covering the block
    requestAnimationFrame(() => {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }, [location.hash])

  useEffect(() => {
    let cancelled = false
    void Promise.all([siteListApps(), siteGetPromo()])
      .then(([apps, rawPromo]) => {
        if (cancelled) return
        if (apps.length > 0) {
          setTiles(apps.map(appToSection))
        }
        setPromo(normalizeSitePromo(rawPromo as Partial<SitePromo>))
      })
      .catch(() => {
        if (!cancelled) {
          setTiles(fallbackSections)
          setPromo(DEFAULT_SITE_PROMO)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <PageShell showBrandLink={false}>
      <section id="about" className="info-section" aria-labelledby="about-title">
        <h2 id="about-title" className="section-block-title">
          О нас
        </h2>
        <div className="info-section-body">
          <p>
            <strong>9to18.ru</strong> — площадка взаимного продвижения и обучения. Роли:{' '}
            <em>пользователь</em> (чтение всех сервисов), <em>админ сервиса</em> (своя плашка,
            страница и блог), <em>супер-админ</em> (редактирование всего сайта и назначение
            админов).
          </p>
        </div>
      </section>

      <header className="home-header">
        <h1 className="home-title">Взаимное продвижение проектов</h1>
        <p className="home-subtitle">
          9to18 — площадка, где сервисы поддерживают друг друга. У каждого приложения свой блог;
          пользователи читают материалы и пишут разработчикам.
        </p>
      </header>

      <PromoSpotlight promo={promo} />

      <div className="sections-grid">
        {tiles.map((section) => (
          <SectionTile key={section.slug} section={section} />
        ))}
      </div>

      <section className="services-overview" aria-labelledby="services-overview-title">
        <h2 id="services-overview-title" className="section-block-title">
          О сервисах
        </h2>
        <p className="section-block-lead">
          Краткое описание разделов. Откройте плитку — попадёте в блог приложения.
        </p>
        <dl className="services-overview-list">
          {tiles.map((section) => (
            <div key={section.slug} className="services-overview-item">
              <dt className="services-overview-name">
                {section.emoji && (
                  <span className="services-overview-emoji" aria-hidden>
                    {section.emoji}
                  </span>
                )}
                {section.title}
              </dt>
              <dd className="services-overview-desc">{section.description}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section id="contacts" className="info-section" aria-labelledby="contacts-title">
        <h2 id="contacts-title" className="section-block-title">
          Контакты
        </h2>
        <div className="info-section-body">
          <p>Напишите разработчикам — форма доступна без входа.</p>
          <ul className="contacts-list">
            <li>
              <span className="contacts-label">Сайт</span>
              <a href="https://9to18.ru">9to18.ru</a>
            </li>
            <li>
              <span className="contacts-label">Лекции</span>
              <Link to="/game/learn">/game/learn</Link>
            </li>
          </ul>
          <ContactForm />
        </div>
      </section>
    </PageShell>
  )
}
