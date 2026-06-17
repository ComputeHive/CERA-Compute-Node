import { AppStatusEnum, TInstallTool } from '@renderer/types'
import { StateCreator } from 'zustand'

export type AppSlice = {
  appStatus: null | AppStatusEnum
  installTool: null | TInstallTool
  node_index: string | null
  setAppStatus: (status: AppSlice['appStatus']) => void
  setInstallTool: (tool: TInstallTool) => void
  setRunningNode: (node_index: string) => void
}
export const createAppSlice: StateCreator<AppSlice, [], [], AppSlice> = (set) => ({
  appStatus: null,
  installTool: null,
  node_index: null,
  token: null,
  setInstallTool: (tool) => set({ installTool: tool }),
  setAppStatus: (status) => set({ appStatus: status }),
  setRunningNode: (node_index) => set({ node_index })
})
