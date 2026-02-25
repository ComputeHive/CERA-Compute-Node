/* eslint-disable @typescript-eslint/no-explicit-any */
import { useAppStore } from '@renderer/store'
import Loader from '../ui/Loader'
import { LogViewer } from '../ui/LogViewer'
import { getBuildImageStream } from '@renderer/api/installer'
import { AppStatusEnum } from '@renderer/types'
import { useState } from 'react'
import { Check } from 'lucide-react'
export function BuildImageView(): React.JSX.Element {
  const [finished, setFinished] = useState<boolean>(false)
  const { setAppStatus, installTool } = useAppStore()
  const handleClick = (): void => {
    setAppStatus(AppStatusEnum.READY)
  }
  console.log('BuildImage View is called')
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4  ">
        {finished ? <Loader /> : <Check className="text-green-600 size-8" />}
        <article className="flex flex-col items-start justify-center gap-2">
          <h1 className="text-3xl font-bold">Build Image</h1>
          <p className="text-xl text-on-seconary">Create Local Instance on PC</p>
        </article>
      </article>
      <LogViewer
        apiFn={getBuildImageStream}
        handleClick={handleClick}
        args={installTool as any}
        setIsPending={setFinished}
      />
    </section>
  )
}
