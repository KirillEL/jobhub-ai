import { useNavigate } from 'react-router-dom'
import { useI18n } from '../../shared/i18n'
import Button from '../../shared/ui/Button'
import Card from '../../shared/ui/Card'
import PageHeader from '../../shared/ui/PageHeader'
import './styles.scss'

export default function ChatPage() {
  const navigate = useNavigate()
  const { t } = useI18n()

  const roadmap = [t('chat.roadmap1'), t('chat.roadmap2'), t('chat.roadmap3')]

  return (
    <main className="layout chat-page">
      <PageHeader title={t('chat.title')} subtitle={t('chat.subtitle')} />

      <section className="cards-grid cards-grid--wide">
        <Card className="chat-coming-card">
          <div className="chat-coming-card__hero">
            <span className="pill">{t('chat.status')}</span>
            <h2>{t('chat.headline')}</h2>
            <p>{t('chat.description')}</p>
            <p className="subtitle">{t('chat.hint')}</p>
          </div>

          <div className="chat-coming-card__actions">
            <Button onClick={() => navigate('/vacancies')}>{t('chat.primaryCta')}</Button>
            <Button variant="secondary" onClick={() => navigate('/jobs')}>
              {t('chat.secondaryCta')}
            </Button>
          </div>
        </Card>

        <Card>
          <h3>{t('chat.roadmapTitle')}</h3>
          <ul className="simple-list">
            {roadmap.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      </section>
    </main>
  )
}
