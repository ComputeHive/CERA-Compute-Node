import { BuildImageView } from '@renderer/components/views/BuildImageView'
import DependenciesView from '@renderer/components/views/DependenciesView'
import { InstallView } from '@renderer/components/views/InstallView'
import LoginView from '@renderer/components/views/LoginView'
import { ReadyView } from '@renderer/components/views/ReadyView'
import { RunningVMView } from '@renderer/components/views/RunningVmView'
import { AppStatusEnum } from '@renderer/types'

export const appStatusComponents = {
  [AppStatusEnum.CHECK_DEP]: <DependenciesView />,
  [AppStatusEnum.INSTALLING_DEP]: <InstallView />,
  [AppStatusEnum.BUILDING_IMG]: <BuildImageView />,
  [AppStatusEnum.SIGNIN]: <LoginView mode={'Login'} />,
  [AppStatusEnum.SIGNUP]: <LoginView mode={'Sign up'} />,
  [AppStatusEnum.READY]: <ReadyView />,
  [AppStatusEnum.RUNNING]: <RunningVMView /> // TODO: Replace this with its correct enum
}
