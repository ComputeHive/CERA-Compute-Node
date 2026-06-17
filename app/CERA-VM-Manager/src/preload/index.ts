import { electronAPI } from '@electron-toolkit/preload'
import { contextBridge, ipcRenderer } from 'electron'

// Custom APIs for renderer
const api = {}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    const apiPort =
      process.argv.find((arg) => arg.startsWith('--api-port='))?.split('=')[1] || '8000'

    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
    contextBridge.exposeInMainWorld('apiConfig', {
      port: parseInt(apiPort),
      baseUrl: `http://localhost:${apiPort}/api`
    })
    contextBridge.exposeInMainWorld('system', {
      info: () => ipcRenderer.invoke('system-info')
    })
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
