import { zodResolver } from '@hookform/resolvers/zod'
import { InstanceResources, instanceResourcesSchema } from '@renderer/schema/instance'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'
import { useMutation } from '@tanstack/react-query'
import { BaseSyntheticEvent } from 'react'
import { FieldErrors, useForm, UseFormRegister, UseFormWatch } from 'react-hook-form'

type TuseResourceAllocationForm = {
  register: UseFormRegister<InstanceResources>
  watch: UseFormWatch<InstanceResources>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit: (e?: BaseSyntheticEvent<object, any, any> | undefined) => Promise<void>
  isPending: boolean
  errors: FieldErrors<InstanceResources>
}
export function useResourceAllocationForm(): TuseResourceAllocationForm {
  const resourceMutation = useMutation({
    mutationFn: (arg: InstanceResources) => {},
    mutationKey: ['resources']
  })
  const { setAppStatus } = useAppStore()

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
  return { register, onSubmit, errors, isPending: resourceMutation.isPending, watch }
}
