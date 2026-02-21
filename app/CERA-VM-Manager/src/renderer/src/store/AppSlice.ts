import { AppStatusEnum } from '@renderer/types'
import { StateCreator } from 'zustand'

export type AppSlice = {
  appStatus: null | AppStatusEnum
  setAppStatus: (status: AppSlice['appStatus']) => void
}
export const createAppSlice: StateCreator<AppSlice, [], [], AppSlice> = (set) => ({
  appStatus: null,
  setAppStatus: (status) => set({ appStatus: status })
})
