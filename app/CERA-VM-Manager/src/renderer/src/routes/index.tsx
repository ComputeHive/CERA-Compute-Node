import { getAppState } from '@renderer/api/installer'
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
import { useEffect } from 'react'
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
  useEffect(() => setAppStatus(data.status as AppStatusEnum), [data.status, setAppStatus])
  return (
    <main className="bg-base w-screen h-screen flex items-center justify-center overflow-auto "></main>
  )
}
