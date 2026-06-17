/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_Coordinator_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface SystemInfo {
  cpu: number
  ram: number
  disk: number
}
interface Window {
  electron: any
  apiConfig: {
    port: number
    baseUrl: string
  }
  system: {
    info: () => Promise<SystemInfo>
  }
}
