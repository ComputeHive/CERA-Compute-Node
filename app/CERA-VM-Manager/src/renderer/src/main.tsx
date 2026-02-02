import './assets/main.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from '@tanstack/react-router'
import { createRouter } from '@tanstack/react-router'
import { createHashHistory } from '@tanstack/history'
import { routeTree } from './routeTree.gen'

export const router = createRouter({
  routeTree,
  history: createHashHistory()
})
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
)
