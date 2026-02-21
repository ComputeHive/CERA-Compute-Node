import { create } from 'zustand'
import { AppSlice, createAppSlice } from './AppSlice'

export type StoreState = AppSlice
export const useAppStore = create<StoreState>()((...a) => ({
  ...createAppSlice(...a)
}))
