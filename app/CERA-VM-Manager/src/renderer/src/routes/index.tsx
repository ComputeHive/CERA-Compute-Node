import Loader from '@renderer/components/ui/Loader'
import { appStatusComponents } from '@renderer/constants'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'
import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/')({
  component: MainPage
})

function MainPage(): React.ReactElement {
  const { appStatus, setAppStatus } = useAppStore()
  const [displayedStatus, setDisplayedStatus] = useState<typeof appStatus>(appStatus)
  const [visible, setVisible] = useState<boolean>(true)
  useEffect(() => {
    const token = localStorage.getItem('token')

    setAppStatus(token ? AppStatusEnum.RUNNING : AppStatusEnum.SIGNIN)
  }, [setAppStatus])
  useEffect(() => {
    if (appStatus === displayedStatus) return
    setVisible(false)
    const timer = setTimeout(() => {
      setDisplayedStatus(appStatus)
      setVisible(true)
    }, 300)
    return () => clearTimeout(timer)
  }, [appStatus, displayedStatus])
  if (!appStatus) return <Loader />
  const maincomponent = appStatusComponents[appStatus]

  return (
    <main className="bg-base w-screen h-screen flex items-center justify-center overflow-auto ">
      <div className="transition-opacity duration-300" style={{ opacity: visible ? 1 : 0 }}>
        {maincomponent}
      </div>
    </main>
  )
}
