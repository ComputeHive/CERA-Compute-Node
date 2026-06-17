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
  SIGNUP = 'signup',
  SIGNIN = 'signin',
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
export type TMetricsResponse = {
  CPU: number
  RAM: number
  Disk: number
}
export type Task = {
  id: string
  price: number
  upTime: string
  status: JobStatusEnum
}
export type TTasksResponse = {
  tasks: Task[]
}
export type TEndVMResponse = TStartVMResponse
export type Tinstance = {
  node_index: string
  username: string
  token: string | null
  cpu: number
  ram: number
  disk: number
}
export type AuthMode = 'Login' | 'Sign up'
