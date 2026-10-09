export interface CgmReading {
  eventId: string
  observedAt: string
  glucoseMgDl: number
  source: string
}

export interface Patient {
  patientId: string
  displayName: string
  sex: 'female' | 'male'
  ageYears: number
  bmiKgM2: number
  diabetesDurationYears: number
  hba1cPercent: number | null
  fastingPlasmaGlucoseMgDl: number | null
  diagnoses: string[]
  medications: string[]
}

export interface Factor {
  feature: string
  displayName: string
  direction: 'higher' | 'lower'
  contribution: number
}

export interface Prediction {
  status: 'available' | 'insufficient_data' | 'unavailable'
  probability: number | null
  riskBand: 'low' | 'moderate' | 'high' | null
  predictionWindowMinutes: number
  predictionTime: string
  modelVersion: string
  topFactors: Factor[]
  warnings: string[]
}

export interface Twin {
  schemaVersion: '1.0'
  synthetic: boolean
  researchUseOnly: boolean
  patient: Patient
  cgmReadings: CgmReading[]
  latestCgm: CgmReading | null
  dataAgeSeconds: number
  prediction: Prediction | null
  predictionUpdatedAt: string | null
}
