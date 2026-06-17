import { useSignupForm } from '@renderer/hooks/AuthView/useSignupView'
import Button from '../ui/Button'
import Input from '../ui/Input'
import Loader from '../ui/Loader'

export default function SignupForm(): React.JSX.Element {
  const { info, errors, isPending, onSubmit, register, watch } = useSignupForm()
  if (!info) return <Loader />
  return (
    <form
      className="flex flex-col items-start justify-center gap-4 w-full"
      onSubmit={onSubmit}
      noValidate
    >
      <article className="flex flex-col gap-2  justify-between items-center w-full">
        <Input placeholder="johndoe" {...register('username')} error={errors.username} />
        <Input
          placeholder="************"
          {...register('password')}
          type="password"
          error={errors.password}
        />
        <Input placeholder="************" {...register('cpu_model')} error={errors.cpu_model} />
        <Input
          placeholder="0x***************"
          {...register('wallet_address')}
          error={errors.wallet_address}
        />
      </article>
      <article className="flex flex-col justify-between items-center w-full gap-2">
        <Input
          {...register('total_cpu_cores', { valueAsNumber: true })}
          error={errors['total_cpu_cores']}
          type="range"
          min={1}
          max={Math.floor(info.cpu)}
          value={watch('total_cpu_cores')}
        />
        <Input
          {...register('total_ram_mb', { valueAsNumber: true })}
          error={errors['total_ram_mb']}
          type="range"
          min={1}
          max={Math.floor(info.ram)}
          step={256}
          value={watch('total_ram_mb')}
        />
        <Input
          {...register('total_disk_mb', { valueAsNumber: true })}
          error={errors['total_disk_mb']}
          type="range"
          min={1}
          max={Math.floor(info.disk)}
          step={256}
          value={watch('total_disk_mb')}
        />
      </article>
      <Button type="submit" disabled={isPending}>
        Sign up
      </Button>
    </form>
  )
}
