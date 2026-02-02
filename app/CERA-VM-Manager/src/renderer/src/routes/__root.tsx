import { createRootRoute, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: RootLayout
})

function RootLayout(): React.JSX.Element {
  return (
    <div className="flex flex-col justify-center items-center h-screen w-screen">
      <Outlet />
    </div>
  )
}
