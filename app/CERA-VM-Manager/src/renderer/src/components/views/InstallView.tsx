import { getDependenciesInstallationStream } from '@renderer/api/installer'

import Loader from '../ui/Loader'
import { LogViewer } from '../ui/LogViewer'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'

export function InstallView(): React.JSX.Element {
  const { setAppStatus } = useAppStore()
  const handleClick = (): void => {
    setAppStatus(AppStatusEnum.BUILDING_IMG)
    /**
     * TODO: Handle the Dialog and Style it well...
     */
  }
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-start gap-4  ">
        <Loader />
        <article className="flex flex-col items-start justify-center gap-2">
          <h1 className="text-3xl font-bold">Installing</h1>
          <p className="text-xl text-on-seconary">Setup Dependencies for Instance on PC</p>
        </article>
      </article>
      <LogViewer apiFn={getDependenciesInstallationStream} handleClick={handleClick} />
    </section>
  )
}
