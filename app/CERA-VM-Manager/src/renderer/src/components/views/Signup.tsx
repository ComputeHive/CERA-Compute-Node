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
    <form
      className="flex flex-col items-start justify-center gap-4 w-full"
      onSubmit={handleSubmit(onSubmit)}
      noValidate
    >
      <article className="flex justify-between items-center w-full">
        <Input placeholder="johndoe" {...register('Username')} error={errors.Username} />
        <Input placeholder="test@gmail.com" {...register('Email')} error={errors.Email} />
      </article>
      <article className="flex justify-between items-center w-full">
        <Input placeholder="************" {...register('Password')} error={errors.Password} />
        <Input
          placeholder="************"
          {...register('Repeat Password')}
          error={errors['Repeat Password']}
        />
      </article>
      <Button type="submit" disabled={isSubmitting}>
        Sign up
      </Button>
    </form>
  )
}
