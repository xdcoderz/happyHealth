import axios from 'axios'
import type { Twin } from '../types/twin'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 10_000,
  headers: { Accept: 'application/json' },
})

export async function getTwin(patientId: string): Promise<Twin> {
  const response = await http.get<Twin>(`/patients/${patientId}/twin`)
  return response.data
}

export async function refreshPrediction(patientId: string): Promise<Twin> {
  const response = await http.post<Twin>(`/predictions/${patientId}/refresh`)
  return response.data
}
