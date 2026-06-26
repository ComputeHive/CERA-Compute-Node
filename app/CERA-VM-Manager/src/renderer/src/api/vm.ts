import { TMetricsResponse, TTasksResponse } from '@renderer/types'

export const startServer = async (body: {
  token: string
  node_id: string
}): Promise<{ status: string }> => {
  const res = await fetch(`${import.meta.env.VITE_COMPUTE_NODE_API_URL}/auth/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  return (await res.json()) as { status: string }
}

export const getMetrics = async (): Promise<TMetricsResponse> => {
  const res = await fetch(`${import.meta.env.VITE_COMPUTE_NODE_API_URL}/vm/metrics`, {
    method: 'GET'
  })
  return (await res.json()) as TMetricsResponse
}
export const getTasks = async (): Promise<TTasksResponse> => {
  const res = await fetch(`${import.meta.env.VITE_COMPUTE_NODE_API_URL}/vm/tasks`, {
    method: 'GET'
  })
  return (await res.json()) as TTasksResponse
}
// export const stopVM = async (node_index: string): Promise<TEndVMResponse> => {
//   const res = await fetch(`${import.meta.env.VITE_COMPUTE_NODE_API_URL}/vm/nodes/${node_index}/stop`, {
//     method: 'POST'
//   })
//   return (await res.json()) as TEndVMResponse
// }

// export const getAllInstances = async (): Promise<{ nodes: Tinstance[] }> => {
//   const res = await fetch(`${import.meta.env.VITE_COMPUTE_NODE_API_URL}/vm/nodes`, { method: 'GET' })
//   return (await res.json()) as { nodes: Tinstance[] }
// }
