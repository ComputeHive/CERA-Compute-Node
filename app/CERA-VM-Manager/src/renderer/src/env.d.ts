/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
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
  system: {
    info: () => Promise<SystemInfo>
  }
}
