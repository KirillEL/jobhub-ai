import { useNavigate } from 'react-router-dom'
import { useI18n } from '../../shared/i18n'
import Card from '../../shared/ui/Card'
import Button from '../../shared/ui/Button'
import PageHeader from '../../shared/ui/PageHeader'
import './styles.scss'

export default function OnboardingPage() {
  const navigate = useNavigate()
  const { t } = useI18n()
  const steps = [
    { title: t('onboarding.step1Title'), text: t('onboarding.step1Text') },
    { title: t('onboarding.step2Title'), text: t('onboarding.step2Text') },
    { title: t('onboarding.step3Title'), text: t('onboarding.step3Text') },
  ]

  return (
    <main className="layout onboarding-page">
      <PageHeader
        title={t('onboarding.title')}
        subtitle={t('onboarding.subtitle')}
        actions={
          <Button onClick={() => navigate('/jobs')}>
            {t('onboarding.cta')}
          </Button>
        }
      />

      <section className="cards-grid">
        {steps.map((step) => (
          <Card key={step.title}>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </Card>
        ))}
      </section>
    </main>
  )
}
