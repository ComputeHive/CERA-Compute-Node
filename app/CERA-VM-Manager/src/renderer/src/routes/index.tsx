import LoginView from '@renderer/components/views/LoginView'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: MainPage
})

function MainPage(): React.ReactElement {
  // const ipcHandle = (): void => window.electron.ipcRenderer.send('ping')

  return (
    <main className="bg-base w-screen h-screen flex items-center justify-center overflow-auto ">
      <LoginView />
    </main>
  )
}
