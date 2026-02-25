import { zodResolver } from '@hookform/resolvers/zod'
import { InstanceResources, instanceResourcesSchema } from '@renderer/schema/instance'
import { useState, useEffect, BaseSyntheticEvent } from 'react'
import { FieldErrors, useForm, UseFormRegister, UseFormWatch } from 'react-hook-form'

export type SystemInfo = {
  cpu: number
  ram: number
  disk: number
}
type TuseResourceAllocationForm = {
  info: SystemInfo | null
  register: UseFormRegister<InstanceResources>
  watch: UseFormWatch<InstanceResources>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit: (e?: BaseSyntheticEvent<object, any, any> | undefined) => Promise<void>
  isSubmitting: boolean
  errors: FieldErrors<InstanceResources>
}
export function useResourceAllocationForm(): TuseResourceAllocationForm {
  const [info, setInfo] = useState<SystemInfo | null>(null)
  useEffect(() => {
    window.system.info().then(setInfo)
  }, [])
  const {
    register,
    watch,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<InstanceResources>({
    resolver: zodResolver(instanceResourcesSchema),
    mode: 'onBlur'
  })
  const onSubmit = handleSubmit(() => {})
  return { info, register, onSubmit, errors, isSubmitting, watch }
}
