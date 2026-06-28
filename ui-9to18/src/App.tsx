export default function App() {
  return (
    <div className="page">
      <div className="glow glow-a" aria-hidden />
      <div className="glow glow-b" aria-hidden />

      <main className="card">
        <div className="brand">
          <span className="brand-mark">9–18</span>
          <span className="brand-domain">9to18.ru</span>
        </div>

        <h1 className="title">Сайт в разработке</h1>
        <p className="subtitle">
          Мы готовим новый проект. Скоро здесь появится полноценный сайт.
        </p>

        <div className="status" role="status">
          <span className="status-dot" />
          <span>Работаем над запуском</span>
        </div>
      </main>
    </div>
  )
}
