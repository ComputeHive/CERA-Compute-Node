import { loginSchema, LoginType } from '@renderer/schema/login'
import Button from '../ui/Button'
import Input from '../ui/Input'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

export default function LoginForm(): React.JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginType>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur'
  })
  const onSubmit = (data: LoginType): void => {
    console.log(data)
  }
  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="flex flex-col items-start justify-center gap-4 w-full"
    >
      <Input placeholder="test@gmail.com" {...register('Email')} error={errors['Email']} />
      <Input placeholder="************" {...register('Password')} error={errors['Password']} />
      <Button type="submit" disabled={isSubmitting}>
        Sign in
      </Button>
    </form>
  )
}
