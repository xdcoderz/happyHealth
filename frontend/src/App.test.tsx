import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { getTwin, refreshPrediction } from './api/client'
import type { Twin } from './types/twin'

vi.mock('./api/client', () => ({ getTwin: vi.fn(), refreshPrediction: vi.fn() }))

const fixture: Twin = {
  schemaVersion: '1.0', synthetic: true, researchUseOnly: true,
  patient: { patientId: 'DEMO-001', displayName: 'Synthetic Patient 001', sex: 'female', ageYears: 52,
    bmiKgM2: 27.4, diabetesDurationYears: 7, hba1cPercent: 7.6, fastingPlasmaGlucoseMgDl: 136,
    diagnoses: ['Type 2 diabetes mellitus'], medications: ['Metformin'] },
  cgmReadings: [
    { eventId: '1', observedAt: '2026-10-09T09:45:00Z', glucoseMgDl: 136, source: 'synthetic' },
    { eventId: '2', observedAt: '2026-10-09T10:00:00Z', glucoseMgDl: 142, source: 'synthetic' },
  ],
  latestCgm: { eventId: '2', observedAt: '2026-10-09T10:00:00Z', glucoseMgDl: 142, source: 'synthetic' },
  dataAgeSeconds: 60,
  prediction: { status: 'available', probability: 0.36, riskBand: 'moderate', predictionWindowMinutes: 120,
    predictionTime: '2026-10-09T10:00:00Z', modelVersion: 'shanghai-logistic-v1',
    topFactors: [{ feature: 'baseline', displayName: 'Current glucose', direction: 'higher', contribution: 0.4 }],
    warnings: ['Research prototype'] },
  predictionUpdatedAt: '2026-10-09T10:00:01Z',
}

describe('doctor dashboard', () => {
  beforeEach(() => {
    vi.mocked(getTwin).mockResolvedValue(fixture)
    vi.mocked(refreshPrediction).mockResolvedValue(fixture)
  })

  it('shows the synthetic patient and model result with units', async () => {
    render(<App />)
    expect(await screen.findByText('Synthetic Patient 001')).toBeInTheDocument()
    expect(screen.getByText('36%')).toBeInTheDocument()
    expect(screen.getByText(/Synthetic demonstration patient/i)).toBeInTheDocument()
    expect(screen.getAllByText(/mg\/dL/i).length).toBeGreaterThan(0)
  })

  it('requests a new prediction from Spring Boot', async () => {
    render(<App />)
    await screen.findByText('Synthetic Patient 001')
    await userEvent.click(screen.getByRole('button', { name: /refresh prediction/i }))
    await waitFor(() => expect(refreshPrediction).toHaveBeenCalledWith('DEMO-001'))
  })
})
