import { TgetAppState, TgetInstalledTools, TInstallTool } from '@renderer/types'
export const getAppState = async (): Promise<TgetAppState> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/prog-status`, {
    method: 'GET'
  })
  return (await res.json()) as TgetAppState
}

export const getInstalledTools = async (): Promise<TgetInstalledTools> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/check-deps`, {
    method: 'GET'
  })
  const json = await res.json()
  return json.data as TgetInstalledTools
}

export const getDependenciesInstallationStream = async (
  onLogChunk: (args: string[]) => void,
  signal: AbortSignal
): Promise<void> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/install-deps`, {
    method: 'GET',
    signal
  })
  if (!res.ok) {
    throw new Error('Network Error')
  }
  const reader = (res.body as ReadableStream<Uint8Array<ArrayBuffer>>).getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      if (lines.length > 0) {
        onLogChunk(lines)
      }
      if (buffer) {
        onLogChunk([buffer])
      }
    }
  } finally {
    reader.releaseLock()
  }
}
export const getBuildImageStream = async (
  onLogChunk: (args: string[]) => void,
  signal: AbortSignal,
  buildMethod?: TInstallTool
): Promise<void> => {
  const res = await fetch(`${window.apiConfig.baseUrl}/build-image`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    signal,
    body: JSON.stringify({
      build_tool: buildMethod
    })
  })
  if (!res.ok) {
    throw new Error('Network Error')
  }
  const reader = (res.body as ReadableStream<Uint8Array<ArrayBuffer>>).getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      if (lines.length > 0) {
        onLogChunk(lines)
      }
    }
    if (buffer) {
      onLogChunk([buffer])
    }
  } finally {
    reader.releaseLock()
  }
}
