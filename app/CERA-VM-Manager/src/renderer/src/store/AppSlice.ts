import { AppStatusEnum, TInstallTool } from '@renderer/types'
import { StateCreator } from 'zustand'

export type AppSlice = {
  appStatus: null | AppStatusEnum
  installTool: null | TInstallTool
  setAppStatus: (status: AppSlice['appStatus']) => void
  setInstallTool: (tool: TInstallTool) => void
}
export const createAppSlice: StateCreator<AppSlice, [], [], AppSlice> = (set) => ({
  appStatus: null,
  installTool: null,
  setInstallTool: (tool) => set({ installTool: tool }),
  setAppStatus: (status) => set({ appStatus: status })
})
