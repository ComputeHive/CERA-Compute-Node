import { zodResolver } from '@hookform/resolvers/zod'
import { signinCoordinator } from '@renderer/api/auth'
import { startServer } from '@renderer/api/vm'
import { LoginRequest, loginSchema } from '@renderer/schema/login'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'
import { useMutation } from '@tanstack/react-query'
import { BaseSyntheticEvent } from 'react'
import { FieldErrors, useForm, UseFormRegister } from 'react-hook-form'

type TuseSigninView = {
  register: UseFormRegister<LoginRequest>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit: (e?: BaseSyntheticEvent<object, any, any> | undefined) => Promise<void>
  isPending: boolean
  errors: FieldErrors<LoginRequest>
}
export function useSigninView(): TuseSigninView {
  const { setAppStatus } = useAppStore()
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<LoginRequest>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur'
  })
  const signinCoordinatorMutation = useMutation({
    mutationFn: (arg: LoginRequest) => signinCoordinator(arg),
    mutationKey: ['coord-signin']
  })
  const startServerMutation = useMutation({
    mutationFn: (arg: { token: string; node_id: string }) => startServer(arg),
    mutationKey: ['signin']
  })
  const onSubmit = handleSubmit(async (arg: LoginRequest) => {
    try {
      const res = await signinCoordinatorMutation.mutateAsync(arg)
      console.log(res)
      const res2 = await startServerMutation.mutateAsync({ token: res.token, node_id: res.node_id })
      console.log(res2)
      setAppStatus(AppStatusEnum.RUNNING)
    } catch (err) {
      console.error(err)
    }
  })
  return {
    register,
    onSubmit,
    errors,
    isPending: startServerMutation.isPending
  }
}
