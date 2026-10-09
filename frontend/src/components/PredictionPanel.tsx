import { AlertTriangle, ArrowDownRight, ArrowUpRight, BrainCircuit } from 'lucide-react'
import type { Prediction } from '../types/twin'

function percentage(value: number) {
  return `${Math.round(value * 100)}%`
}

export function PredictionPanel({ prediction }: { prediction: Prediction | null }) {
  if (!prediction) {
    return (
      <div className="prediction-empty">
        <BrainCircuit size={28} />
        <h3>No prediction yet</h3>
        <p>Refresh the model after enough CGM history has arrived.</p>
      </div>
    )
  }

  if (prediction.status !== 'available' || prediction.probability === null) {
    return (
      <div className="prediction-empty warning-state">
        <AlertTriangle size={28} />
        <h3>{prediction.status === 'insufficient_data' ? 'More sensor history needed' : 'Prediction unavailable'}</h3>
        <p>{prediction.warnings[0] ?? 'Try again when the model service is available.'}</p>
      </div>
    )
  }

  return (
    <div className="prediction-content">
      <div className="risk-summary">
        <div className={`risk-ring ${prediction.riskBand}`}>
          <strong>{percentage(prediction.probability)}</strong>
          <span>probability</span>
        </div>
        <div>
          <span className={`risk-pill ${prediction.riskBand}`}>{prediction.riskBand} risk</span>
          <h3>Glucose spike in the next {prediction.predictionWindowMinutes / 60} hours</h3>
          <p>Estimated chance that glucose rises by at least 40 mg/dL after the current meal.</p>
        </div>
      </div>
      <div className="factors">
        <div className="section-kicker">What influenced this estimate</div>
        {prediction.topFactors.slice(0, 4).map((factor) => (
          <div className="factor" key={factor.feature}>
            <span className={`factor-icon ${factor.direction}`}>
              {factor.direction === 'higher' ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}
            </span>
            <span>{factor.displayName}</span>
            <small>{factor.direction} estimated risk</small>
          </div>
        ))}
      </div>
      <div className="model-note">Model {prediction.modelVersion} · research prototype, not medical advice</div>
    </div>
  )
}
