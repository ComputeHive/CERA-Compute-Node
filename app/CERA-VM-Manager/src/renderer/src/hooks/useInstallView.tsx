import { useAppStore } from '@renderer/store'
import { AppStatusEnum, TInstallTool } from '@renderer/types'
import { useState } from 'react'
type TuseInstallView = {
  handleClick: () => void
  open: boolean
  handleOk: () => void
  setInstallToolState: (arg: TInstallTool) => void
  installTool: TInstallTool | null
}
export function useInstallView(): TuseInstallView {
  const { setAppStatus, setInstallTool } = useAppStore()
  const [open, setOpen] = useState<boolean>(false)
  const [installTool, setInstallToolState] = useState<TInstallTool | null>(null)
  const handleClick = (): void => {
    setOpen(true)
  }
  const handleOk = (): void => {
    setOpen(false)
    setInstallTool(installTool as TInstallTool)
    setAppStatus(AppStatusEnum.READY)
  }
  return {
    handleClick,
    open,
    handleOk,
    setInstallToolState,
    installTool
  }
}
