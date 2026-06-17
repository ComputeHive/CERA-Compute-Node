import { TEndVMResponse, Tinstance, TMetricsResponse, TTasksResponse } from '@renderer/types'

export const startVM = async (
  node_index: string,
  body: { token: string }
): Promise<{ status: string }> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/vm/nodes/${node_index}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: body.token, node_index })
  })
  return (await res.json()) as { status: string }
}

export const getVMMetrics = async (node_index: string): Promise<TMetricsResponse> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/vm/nodes/${node_index}/metrics`, {
    method: 'GET'
  })
  return (await res.json()) as TMetricsResponse
}
export const getVMTasks = async (node_index: string): Promise<TTasksResponse> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/vm/nodes/${node_index}/metrics`, {
    method: 'GET'
  })
  return (await res.json()) as TTasksResponse
}
export const stopVM = async (node_index: string): Promise<TEndVMResponse> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/vm/nodes/${node_index}/stop`, {
    method: 'POST'
  })
  return (await res.json()) as TEndVMResponse
}

export const getAllInstances = async (): Promise<{ nodes: Tinstance[] }> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/vm/nodes`, { method: 'GET' })
  return (await res.json()) as { nodes: Tinstance[] }
}
