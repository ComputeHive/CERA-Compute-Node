import { InstanceResources } from '@renderer/schema/instance'
import {
  TEndVMResponse,
  TMetricsResponse,
  TStartVMResponse,
  TvmResourcesResponse
} from '@renderer/types'

export const startVM = async (body: InstanceResources): Promise<TStartVMResponse> => {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/vm/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  return (await res.json()) as TStartVMResponse
}
export const getVMResourcesStatus = async (): Promise<TvmResourcesResponse> => {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/vm/resources`, { method: 'GET' })
  return (await res.json()) as TvmResourcesResponse
}
export const getVMMetrics = async (): Promise<TMetricsResponse> => {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/vm/metrics`, { method: 'GET' })
  return (await res.json()) as TMetricsResponse
}
export const stopVM = async (): Promise<TEndVMResponse> => {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/vm/stop`, { method: 'POST' })
  return (await res.json()) as TEndVMResponse
}
