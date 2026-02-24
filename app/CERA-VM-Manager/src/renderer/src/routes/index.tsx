import { getAppState } from '@renderer/api/installer'
import { BuildImageView } from '@renderer/components/views/BuildImageView'
import DependenciesView from '@renderer/components/views/DependenciesView'
import { InstallView } from '@renderer/components/views/InstallView'
import { queryClient } from '@renderer/lib/utils'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum, TgetAppState } from '@renderer/types'
import {
  dataTagErrorSymbol,
  dataTagSymbol,
  OmitKeyof,
  QueryFunction,
  queryOptions,
  UseQueryOptions,
  useSuspenseQuery
} from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
const statusQueryOptions = (): OmitKeyof<
  UseQueryOptions<TgetAppState, Error, TgetAppState, string[]>,
  'queryFn'
> & {
  queryFn?: QueryFunction<TgetAppState, string[], never> | undefined
} & {
  queryKey: string[] & {
    [dataTagSymbol]: TgetAppState
    [dataTagErrorSymbol]: Error
  }
} =>
  queryOptions({
    queryKey: ['app_status'],
    queryFn: () => getAppState(),
    retry: 20,
    retryDelay: 500
  })
export const Route = createFileRoute('/')({
  component: MainPage,
  loader: async () => {
    queryClient.prefetchQuery(statusQueryOptions())
    await queryClient.ensureQueryData(statusQueryOptions())
  }
})

function MainPage(): React.ReactElement {
  const { data } = useSuspenseQuery(statusQueryOptions())
  const { appStatus, setAppStatus } = useAppStore()
  const [displayedStatus, setDisplayedStatus] = useState<typeof appStatus>(appStatus)
  const [visible, setVisible] = useState<boolean>(true)
  useEffect(() => setAppStatus(data.status as AppStatusEnum), [data.status, setAppStatus])
  useEffect(() => {
    if (appStatus === displayedStatus) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setVisible(false)
    const timer = setTimeout(() => {
      setDisplayedStatus(appStatus)
      setVisible(true)
    }, 300)
    return () => clearTimeout(timer)
  }, [appStatus])
  const maincomponent =
    appStatus == AppStatusEnum.CHECK_DEP ? (
      <DependenciesView />
    ) : appStatus == AppStatusEnum.INSTALLING_DEP ? (
      <InstallView />
    ) : appStatus == AppStatusEnum.BUILDING_IMG ? (
      <BuildImageView />
    ) : appStatus == AppStatusEnum.READY ? (
      <></>
    ) : (
      <></>
    )
  return (
    <main className="bg-base w-screen h-screen flex items-center justify-center overflow-auto ">
      <div className="transition-opacity duration-300" style={{ opacity: visible ? 1 : 0 }}>
        {maincomponent}
      </div>
    </main>
  )
}
