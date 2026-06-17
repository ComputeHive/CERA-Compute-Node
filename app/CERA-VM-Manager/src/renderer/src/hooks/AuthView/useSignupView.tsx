import { zodResolver } from '@hookform/resolvers/zod'
import { signupCoordinator, signupVM } from '@renderer/api/auth'
import { RegisterRequest, signupSchema } from '@renderer/schema/signup'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum, Tinstance } from '@renderer/types'
import { useMutation } from '@tanstack/react-query'
import { BaseSyntheticEvent, useEffect, useState } from 'react'
import { FieldErrors, useForm, UseFormRegister, UseFormWatch } from 'react-hook-form'

type TuseSignupForm = {
  info: SystemInfo | null
  register: UseFormRegister<RegisterRequest>
  watch: UseFormWatch<RegisterRequest>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit: (e?: BaseSyntheticEvent<object, any, any> | undefined) => Promise<void>
  isPending: boolean
  errors: FieldErrors<RegisterRequest>
}
export function useSignupForm(): TuseSignupForm {
  const [info, setInfo] = useState<SystemInfo | null>(null)
  useEffect(() => {
    window.system.info().then(setInfo)
  }, [])
  const nodeRegistrationCoordinatorMutation = useMutation({
    mutationFn: (arg: RegisterRequest) => signupCoordinator(arg),
    mutationKey: ['coord-signup']
  })
  const nodecreationMutation = useMutation({
    mutationFn: (arg: Tinstance) => signupVM(arg),
    mutationKey: ['signup']
  })
  const { setAppStatus } = useAppStore()

  const {
    register,
    watch,
    handleSubmit,
    formState: { errors }
  } = useForm<RegisterRequest>({
    resolver: zodResolver(signupSchema),
    mode: 'onBlur'
  })
  const onSubmit = handleSubmit(async (arg: RegisterRequest) => {
    try {
      let config: Tinstance = {}
      const { node_id } = await nodeRegistrationCoordinatorMutation.mutateAsync(arg)
      console.log(node_id)
      config = {
        cpu: arg.total_cpu_cores,
        disk: arg.total_disk_mb,
        ram: arg.total_ram_mb,
        node_index: node_id,
        username: arg.username,
        token: null
      }
      console.log(config)
      const { status } = await nodecreationMutation.mutateAsync(config)
      console.log(status)
      setAppStatus(AppStatusEnum.READY)
    } catch (err) {
      console.error(err)
    }
  })
  return {
    info,
    register,
    onSubmit,
    errors,
    isPending: nodecreationMutation.isPending,
    watch
  }
}
