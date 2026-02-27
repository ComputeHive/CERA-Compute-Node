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
export type TInstallTool = 'docker' | 'debootstrap'
export type TgetInstalledTools = {
  [id in (typeof TOOLS)[number]]: Tool['status']
}

export type TgetAppState = {
  status: string
}

export enum AppStatusEnum {
  CHECK_DEP = 'checking_dep',
  INSTALLING_DEP = 'installing_dep',
  BUILDING_IMG = 'building_img',
  READY = 'ready',
  RUNNING = 'running'
}
export enum JobStatusEnum {
  RECEIVED = 'received',
  RUNNING = 'running',
  COMPLETED = 'completed'
}
export type TStartVMResponse = {
  status: string
}

export type TvmConfig = {
  cpu: number
  disk: number
  ram: number
}
export type TvmResourcesResponse = {}
export type TEndVMResponse = TStartVMResponse
export type TJob = {
  id: string
  price: number
  upTime: string
  status: JobStatusEnum
}
