import Button from '@renderer/components/ui/Button'
import Loader from '@renderer/components/ui/Loader'

export default function DependenciesView(): React.JSX.Element {
  return (
    <section className="relative flex w-3/4 h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4  ">
        <Loader />
        <h1 className="text-3xl font-bold">Check System Prerequisites</h1>
      </article>
      <article> {/** This 'll contain the component of Checked dependencies */}</article>
      <article className="absolute bottom-8 right-8">
        <Button>Next</Button>
      </article>
    </section>
  )
}
