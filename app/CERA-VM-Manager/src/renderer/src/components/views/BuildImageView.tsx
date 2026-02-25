import { useInstallView } from '@renderer/hooks/useInstallView'
import Loader from '../ui/Loader'
import { LogViewer } from '../ui/LogViewer'
import { getBuildImageStream } from '@renderer/api/installer'
import { Dialog } from '../ui/dialog'
import Button from '../ui/Button'

export function BuildImageView(): React.JSX.Element {
  const { handleClick, handleOk, open, setInstallToolState } = useInstallView()
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4  ">
        <Loader />
        <article className="flex flex-col items-start justify-center gap-2">
          <h1 className="text-3xl font-bold">Build Image</h1>
          <p className="text-xl text-on-seconary">Create Local Instance on PC</p>
        </article>
      </article>
      <LogViewer apiFn={getBuildImageStream} handleClick={handleClick} />
      <Dialog open={open}>
        <>
          <h2 className="text-2xl font-medium mb-4">Choose Build Method</h2>
          <div className="flex gap-3 mb-6">
            <button className="" onClick={() => setInstallToolState('docker')}>
              docker
            </button>
            <button className="" onClick={() => setInstallToolState('debootstrap')}>
              debootstrap
            </button>
          </div>
          <div className="flex justify-end">
            <Button onClick={handleOk} className="bg-green-700 text-white">
              OK
            </Button>
          </div>
        </>
      </Dialog>
    </section>
  )
}
