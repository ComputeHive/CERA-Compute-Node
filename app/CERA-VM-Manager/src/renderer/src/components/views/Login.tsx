import { useSigninView } from '@renderer/hooks/AuthView/useSignInView'
import Button from '../ui/Button'
import Input from '../ui/Input'

export default function LoginForm(): React.JSX.Element {
  const { errors, isPending, onSubmit, register } = useSigninView()
  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="flex flex-col items-start justify-center gap-4 w-full"
    >
      <Input placeholder="johndoe" {...register('username')} error={errors['username']} />
      <Input
        placeholder="************"
        type="password"
        {...register('password')}
        error={errors['password']}
      />
      <Button type="submit" disabled={isPending}>
        Sign in
      </Button>
    </form>
  )
}
