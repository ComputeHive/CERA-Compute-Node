import { zodResolver } from '@hookform/resolvers/zod'
import { startVM } from '@renderer/api/vm'
import { InstanceResources, instanceResourcesSchema } from '@renderer/schema/instance'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'
import { useMutation } from '@tanstack/react-query'
import { useState, useEffect, BaseSyntheticEvent } from 'react'
import { FieldErrors, useForm, UseFormRegister, UseFormWatch } from 'react-hook-form'

type TuseResourceAllocationForm = {
  info: SystemInfo | null
  register: UseFormRegister<InstanceResources>
  watch: UseFormWatch<InstanceResources>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit: (e?: BaseSyntheticEvent<object, any, any> | undefined) => Promise<void>
  isPending: boolean
  errors: FieldErrors<InstanceResources>
}
export function useResourceAllocationForm(): TuseResourceAllocationForm {
  const resourceMutation = useMutation({
    mutationFn: (arg: InstanceResources) => startVM(arg),
    mutationKey: ['resources']
  })
  const [info, setInfo] = useState<SystemInfo | null>(null)
  const { setAppStatus } = useAppStore()
  useEffect(() => {
    window.system.info().then(setInfo)
  }, [])
  const {
    register,
    watch,
    handleSubmit,
    formState: { errors }
  } = useForm<InstanceResources>({
    resolver: zodResolver(instanceResourcesSchema),
    mode: 'onBlur'
  })
  const onSubmit = handleSubmit(async (arg: InstanceResources) => {
    try {
      await resourceMutation.mutateAsync(arg)
      setAppStatus(AppStatusEnum.RUNNING)
    } catch (err) {
      console.error(err)
    }
  })
  return { info, register, onSubmit, errors, isPending: resourceMutation.isPending, watch }
}
