import { zodResolver } from '@hookform/resolvers/zod'
import { signupCoordinator } from '@renderer/api/auth'
import { RegisterRequest, signupSchema } from '@renderer/schema/signup'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'
import { useMutation } from '@tanstack/react-query'
import { BaseSyntheticEvent, useEffect, useState } from 'react'
import { FieldErrors, useForm, UseFormRegister } from 'react-hook-form'

type TuseSignupForm = {
  info: SystemInfo | null
  register: UseFormRegister<RegisterRequest>
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
      const { node_id } = await nodeRegistrationCoordinatorMutation.mutateAsync(arg)
      console.log(node_id)
      setAppStatus(AppStatusEnum.SIGNIN)
    } catch (err) {
      console.error(err)
    }
  })
  return {
    info,
    register,
    onSubmit,
    errors,
    isPending: nodeRegistrationCoordinatorMutation.isPending,
    watch
  }
}
