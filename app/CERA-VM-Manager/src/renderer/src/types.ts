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
