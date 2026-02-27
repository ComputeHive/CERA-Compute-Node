import Button from '@renderer/components/ui/Button'
import Input from '@renderer/components/ui/Input'
import Loader from '@renderer/components/ui/Loader'
import { useResourceAllocationForm } from '@renderer/hooks/useResourceAllocationForm'

export function ResourceAllocationForm(): React.JSX.Element {
  const { info, errors, isPending, onSubmit, register, watch } = useResourceAllocationForm()
  if (!info) return <Loader />
  return (
    <article className="relative bg-elevated py-8 px-4 min-w-200 min-h-120  max-h-120  overflow-auto w-full h-full flex flex-col gap-1">
      <form
        onSubmit={onSubmit}
        noValidate
        className="flex flex-col items-start justify-center gap-4 w-full px-6"
      >
        <Input
          {...register('CPU', { valueAsNumber: true })}
          error={errors['CPU']}
          type="range"
          min={1}
          max={Math.floor(info.cpu)}
          value={watch('CPU')}
        />
        <Input
          {...register('RAM', { valueAsNumber: true })}
          error={errors['RAM']}
          type="range"
          min={1}
          max={Math.floor(info.ram)}
          step={256}
          value={watch('RAM')}
        />
        <Input
          {...register('Disk', { valueAsNumber: true })}
          error={errors['Disk']}
          type="range"
          min={1}
          max={Math.floor(info.disk)}
          step={256}
          value={watch('Disk')}
        />
        <div className="flex justify-end w-full mt-4">
          <Button type="submit" disabled={isPending} className="">
            Create Instance
          </Button>
        </div>
      </form>
    </article>
  )
}
