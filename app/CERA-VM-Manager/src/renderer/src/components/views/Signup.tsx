import Button from '../ui/Button'
import Input from '../ui/Input'
import { zodResolver } from '@hookform/resolvers/zod'
import { signupSchema, SignUpType } from '@renderer/schema/signup'
import { useForm } from 'react-hook-form'

export default function SignupForm(): React.JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<SignUpType>({
    resolver: zodResolver(signupSchema),
    mode: 'onBlur'
  })
  const onSubmit = (data: SignUpType): void => {
    console.log(data)
  }
  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <Input placeholder="johndoe" {...register('Username')} error={String(errors.Username)} />
      <Input placeholder="test@gmail.com" {...register('Email')} error={String(errors.Email)} />
      <Input placeholder="************" {...register('Password')} error={String(errors.Password)} />
      <Input
        placeholder="************"
        {...register('Repeat Password')}
        error={String(errors['Repeat Password'])}
      />
      <Button type="submit" disabled={isSubmitting}>
        Sign up
      </Button>
    </form>
  )
}
