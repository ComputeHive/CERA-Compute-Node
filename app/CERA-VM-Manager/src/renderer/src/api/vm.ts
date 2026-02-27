import { InstanceResources } from '@renderer/schema/instance'
import { TEndVMResponse, TStartVMResponse, TvmResourcesResponse } from '@renderer/types'

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

export const stopVM = async (): Promise<TEndVMResponse> => {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/vm/stop`, { method: 'POST' })
  return (await res.json()) as TEndVMResponse
}
