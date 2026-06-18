import LoginView from '@renderer/components/views/LoginView'
import { RunningVMView } from '@renderer/components/views/RunningVmView'
import { AppStatusEnum } from '@renderer/types'

export const appStatusComponents = {
  [AppStatusEnum.SIGNIN]: <LoginView mode={'Login'} />,
  [AppStatusEnum.SIGNUP]: <LoginView mode={'Sign up'} />,
  [AppStatusEnum.RUNNING]: <RunningVMView />
}
