import { createFileRoute } from '@tanstack/react-router'
// import Versions from '../components/Versions'
import electronLogo from '../assets/electron.svg'
import Loader from '@renderer/components/ui/Loader'
import Input from '@renderer/components/ui/Input'

export const Route = createFileRoute('/')({
  component: MainPage
})

function MainPage(): React.ReactElement {
  const ipcHandle = (): void => window.electron.ipcRenderer.send('ping')

  return (
    <>
      <img alt="logo" className="logo" src={electronLogo} />
      <div className="creator">Powered by electron-vite</div>
      <div className="text">
        <div className="flex items-center gap-4">
          <Loader />
          Build an Electron app with <span className="react">React</span>
          &nbsp;and <span className="ts">TypeScript</span>
        </div>
      </div>
      <p className="tip ">
        Please try pressing <code>F12</code> to open the devTool
      </p>
      <div className="actions">
        <div className="action">
          <a href="https://electron-vite.org/" target="_blank" rel="noreferrer">
            Documentation
          </a>
        </div>
        <div className="action">
          <a target="_blank" rel="noreferrer" onClick={ipcHandle}>
            Send IPC
          </a>
        </div>
      </div>
      <Input placeholder="Ahmed@gmail.com" name="Email" />
    </>
  )
}
