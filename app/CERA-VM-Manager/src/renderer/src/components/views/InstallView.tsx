import { getDependenciesInstallationStream } from '@renderer/api/installer'

import Loader from '../ui/Loader'
import { LogViewer } from '../ui/LogViewer'
import { Dialog } from '../ui/dialog'
import { cn } from '@renderer/lib/utils'
import Button from '../ui/Button'
import { useInstallView } from '@renderer/hooks/useInstallView'
import { Check } from 'lucide-react'

export function InstallView(): React.JSX.Element {
  const { handleClick, handleOk, open, setInstallToolState, installTool, finished, setFinished } =
    useInstallView()
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-start gap-4  ">
        {finished ? <Loader /> : <Check className="text-green-600 size-8" />}
        <article className="flex flex-col items-start justify-center gap-2">
          <h1 className="text-3xl font-bold">Installing</h1>
          <p className="text-xl text-on-seconary">Setup Dependencies for Instance on PC</p>
        </article>
      </article>
      <LogViewer
        apiFn={getDependenciesInstallationStream}
        handleClick={handleClick}
        setIsPending={setFinished}
      />
      <Dialog open={open}>
        <h2 className="text-2xl font-medium mb-4">Choose Build Method</h2>
        <div className="flex gap-3 m-6">
          <button
            className={cn(
              'border border-active/45 p-4 bg-surface rounded-lg  ',
              `${installTool == 'docker' && 'text-white bg-active/25'}`
            )}
            onClick={() => setInstallToolState('docker')}
          >
            docker
          </button>
          <button
            className={cn(
              'border border-active/45 p-4 bg-surface rounded-lg  ',
              `${installTool == 'debootstrap' && 'text-white bg-active/25'}`
            )}
            onClick={() => setInstallToolState('debootstrap')}
          >
            debootstrap
          </button>
        </div>
        {installTool && (
          <div className="flex justify-end w-full">
            <Button className="bg-green-700 text-white py-2" size="sm" onClick={handleOk}>
              OK
            </Button>
          </div>
        )}
      </Dialog>
    </section>
  )
}
