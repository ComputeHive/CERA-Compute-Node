import { TOOLS } from '@renderer/constants'

export enum ToolStatusEnum {
  NOT_INSTALLED = 'Not Installled',
  INSTALLED = 'Installed',
  PENDING = 'Pending'
}
export type Tool = {
  name: string
  status: ToolStatusEnum
}

export type TgetInstalledTools = {
  [id in (typeof TOOLS)[number]]: string
}

export type TgetAppState = {
  status: string
}

export enum AppStatusEnum {
  CHECK_DEP = 'check_dep',
  INSTALLING_DEP = 'installing_dep',
  BUILDING_IMG = 'building_img',
  READY = 'ready',
  RUNNING = 'running'
}
