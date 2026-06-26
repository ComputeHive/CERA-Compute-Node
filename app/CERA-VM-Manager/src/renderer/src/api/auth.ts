import { LoginRequest } from '@renderer/schema/login'
import { RegisterRequest } from '@renderer/schema/signup'
import { Tinstance } from '@renderer/types'

export const signupVM = async (node_cfg: Tinstance): Promise<{ status: string }> => {
  const res = await fetch(`${import.meta.env.VITE_COMPUTE_NODE_API_URL}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(node_cfg)
  })
  return (await res.json()) as { status: string; node_index: string }
}

export const signupCoordinator = async (data: RegisterRequest): Promise<{ node_id: string }> => {
  const res = await fetch(`${import.meta.env.VITE_Coordinator_API_URL}/compute-nodes/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return (await res.json()) as { node_id: string }
}

export const signinCoordinator = async (
  data: LoginRequest
): Promise<{ token: string; node_id: string }> => {
  const res = await fetch(`${import.meta.env.VITE_Coordinator_API_URL}/compute-nodes/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return (await res.json()) as { token: string; node_id: string }
}
