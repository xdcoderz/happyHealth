import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  Clock3,
  FlaskConical,
  HeartPulse,
  RefreshCcw,
  ShieldCheck,
  UserRound,
  Wifi,
} from 'lucide-react'
import { getTwin, refreshPrediction } from './api/client'
import { GlucoseChart } from './components/GlucoseChart'
import { PredictionPanel } from './components/PredictionPanel'
import type { Twin } from './types/twin'

const PATIENT_ID = 'DEMO-001'

function valueOrDash(value: number | null, suffix: string) {
  return value === null ? '—' : `${value} ${suffix}`
}

function shortTime(value: string | null) {
  if (!value) return 'Not generated'
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

export default function App() {
  const [twin, setTwin] = useState<Twin | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    try {
      setTwin(await getTwin(PATIENT_ID))
      setError(null)
    } catch {
      setError('The digital twin service could not be reached. Check that the backend is running.')
    } finally {
      if (!quiet) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    const poll = window.setInterval(() => void load(true), 15_000)
    return () => window.clearInterval(poll)
  }, [load])

  async function refresh() {
    setRefreshing(true)
    try {
      setTwin(await refreshPrediction(PATIENT_ID))
      setError(null)
    } catch (cause) {
      console.error('Prediction refresh failed', cause)
      setError('Prediction refresh failed. The previous result, if shown, has been kept.')
    } finally {
      setRefreshing(false)
    }
  }

  const trend = useMemo(() => {
    if (!twin || twin.cgmReadings.length < 2) return null
    const last = twin.cgmReadings.at(-1)!
    const prior = twin.cgmReadings.at(-2)!
    return last.glucoseMgDl - prior.glucoseMgDl
  }, [twin])

  if (loading && !twin) {
    return <main className="center-state"><div className="spinner" /><p>Building the patient twin…</p></main>
  }

  if (!twin) {
    return (
      <main className="center-state">
        <AlertCircle size={34} />
        <h1>Dashboard unavailable</h1>
        <p>{error}</p>
        <button className="primary-button" onClick={() => void load()}>Try again</button>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <aside className="side-rail" aria-label="Application identity">
        <div className="logo-mark"><HeartPulse size={23} /></div>
        <div className="rail-line" />
        <div className="rail-icon active"><Activity size={20} /></div>
        <div className="rail-icon"><UserRound size={20} /></div>
        <div className="rail-spacer" />
        <div className="rail-icon"><ShieldCheck size={20} /></div>
      </aside>

      <main className="dashboard">
        <header className="topbar">
          <div>
            <div className="eyebrow">HappyHealth clinical workspace</div>
            <h1>Virtual Patient Monitor</h1>
          </div>
          <div className="topbar-actions">
            <span className="status-chip"><span className="live-dot" /> Twin online</span>
            <button className="primary-button" onClick={() => void refresh()} disabled={refreshing}>
              <RefreshCcw size={16} className={refreshing ? 'spinning' : ''} />
              {refreshing ? 'Calculating…' : 'Refresh prediction'}
            </button>
          </div>
        </header>

        <div className="safety-banner">
          <FlaskConical size={17} />
          <strong>Synthetic demonstration patient</strong>
          <span>No real patient data · Research use only · Not for diagnosis or treatment</span>
        </div>

        {error && <div className="error-banner"><AlertCircle size={17} /> {error}</div>}

        <section className="patient-strip">
          <div className="avatar">SP</div>
          <div className="patient-name">
            <span>Active digital twin</span>
            <h2>{twin.patient.displayName}</h2>
            <small>{twin.patient.patientId}</small>
          </div>
          <div className="patient-fact"><span>Age</span><strong>{twin.patient.ageYears} years</strong></div>
          <div className="patient-fact"><span>Sex</span><strong>{twin.patient.sex}</strong></div>
          <div className="patient-fact"><span>Primary condition</span><strong>{twin.patient.diagnoses[0] ?? '—'}</strong></div>
          <div className="freshness"><Wifi size={15} /><span>CGM updated</span><strong>{Math.max(0, Math.round(twin.dataAgeSeconds / 60))} min ago</strong></div>
        </section>

        <section className="metric-grid">
          <article className="metric-card current-glucose">
            <div className="metric-icon"><Activity size={19} /></div>
            <span>Current glucose</span>
            <strong>{twin.latestCgm ? Math.round(twin.latestCgm.glucoseMgDl) : '—'} <small>mg/dL</small></strong>
            <p className={trend !== null && trend > 0 ? 'up' : ''}>{trend === null ? 'Trend unavailable' : `${trend > 0 ? '+' : ''}${trend.toFixed(0)} mg/dL in 15 min`}</p>
          </article>
          <article className="metric-card"><span>HbA1c</span><strong>{valueOrDash(twin.patient.hba1cPercent, '%')}</strong><p>Historical lab value</p></article>
          <article className="metric-card"><span>Body mass index</span><strong>{valueOrDash(twin.patient.bmiKgM2, 'kg/m²')}</strong><p>Static health record</p></article>
          <article className="metric-card"><span>Fasting glucose</span><strong>{valueOrDash(twin.patient.fastingPlasmaGlucoseMgDl, 'mg/dL')}</strong><p>Historical lab value</p></article>
        </section>

        <section className="main-grid">
          <article className="panel chart-panel">
            <div className="panel-header">
              <div><div className="section-kicker">Dynamic stream</div><h2>Continuous glucose history</h2></div>
              <div className="legend"><span /> CGM reading <i /> Reference 180 mg/dL</div>
            </div>
            <GlucoseChart readings={twin.cgmReadings} />
            <div className="chart-footer"><Clock3 size={14} /> Latest {twin.cgmReadings.length} readings · values ordered by observation time</div>
          </article>

          <article className="panel prediction-panel">
            <div className="panel-header">
              <div><div className="section-kicker">Algorithmic forecast</div><h2>Post-meal spike risk</h2></div>
              <span className="generated">Updated {shortTime(twin.predictionUpdatedAt)}</span>
            </div>
            <PredictionPanel prediction={twin.prediction} />
          </article>
        </section>

        <section className="lower-grid">
          <article className="panel compact-panel"><div className="section-kicker">Clinical history</div><h3>Diagnoses</h3><div className="tag-list">{twin.patient.diagnoses.map((item) => <span key={item}>{item}</span>)}</div></article>
          <article className="panel compact-panel"><div className="section-kicker">Medication context</div><h3>Recorded medications</h3><div className="tag-list">{twin.patient.medications.map((item) => <span key={item}>{item}</span>)}</div></article>
          <article className="panel compact-panel provenance"><ShieldCheck size={24} /><div><div className="section-kicker">Data provenance</div><h3>Safe for public demo</h3><p>Synthetic EHR + simulated CGM; no identifiable person.</p></div></article>
        </section>
      </main>
    </div>
  )
}
