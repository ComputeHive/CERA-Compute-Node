import { getInstalledTools } from '@renderer/api/installer'
import { TOOLS } from '@renderer/constants'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum, TgetInstalledTools, TInstallTool, ToolStatusEnum } from '@renderer/types'
import { useQuery } from '@tanstack/react-query'
type TuseDependenciesView = {
  tools: TgetInstalledTools
  isPending: boolean
  handleClick: (installTool?: TInstallTool) => void
}
export function useDependenciesView(): TuseDependenciesView {
  const { setAppStatus, setInstallTool } = useAppStore()
  const initialToolsStatus: TgetInstalledTools = Object.fromEntries(
    TOOLS.map((tool_name) => [tool_name, ToolStatusEnum.PENDING])
  ) as TgetInstalledTools
  const dependenciesQuery = useQuery({
    initialData: initialToolsStatus,
    queryKey: ['dependencies'],
    queryFn: () => getInstalledTools()
  })
  const handleClick = (installTool?: TInstallTool): void => {
    if (installTool == undefined) setAppStatus(AppStatusEnum.INSTALLING_DEP)
    else {
      setAppStatus(AppStatusEnum.BUILDING_IMG)
      setInstallTool(installTool)
    }
  }
  return {
    tools: dependenciesQuery.data,
    isPending: dependenciesQuery.isPending,
    handleClick
  }
}
