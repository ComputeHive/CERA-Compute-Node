import { QueryClient } from '@tanstack/react-query'
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
export const queryClient = new QueryClient()

export function saveToLocalStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch (error) {
    console.error(`Error saving key "${key}" to localStorage:`, error)
  }
}
export function loadFromLocalStorage(key: string): string | null {
  try {
    const value = localStorage.getItem(key)
    return value
  } catch (error) {
    console.error(`Error loading key "${key}" from localStorage:`, error)
    return null
  }
}
