import { TgetInstalledTools, ToolStatusEnum } from '@renderer/types'
import { TOOLS } from '@renderer/constants'
import { useQuery } from '@tanstack/react-query'
import { getInstalledTools } from '@renderer/api/installer'
type TuseDependenciesView = {
  tools: TgetInstalledTools
  isPending: boolean
}
export function useDependenciesView(): TuseDependenciesView {
  const initialToolsStatus: TgetInstalledTools = Object.fromEntries(
    TOOLS.map((tool_name) => [tool_name, ToolStatusEnum.PENDING])
  ) as TgetInstalledTools
  const dependenciesQuery = useQuery({
    initialData: initialToolsStatus,
    queryKey: ['dependencies'],
    queryFn: () => getInstalledTools()
  })
  return {
    tools: dependenciesQuery.data,
    isPending: dependenciesQuery.isPending
  }
}
