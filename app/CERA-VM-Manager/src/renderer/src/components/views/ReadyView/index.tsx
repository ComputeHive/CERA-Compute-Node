import { ResourceAllocationForm } from './ResourceAllocationForm'

export function ReadyView(): React.JSX.Element {
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4  ">
        <article className="flex flex-col items-start justify-center gap-2">
          <h1 className="text-3xl font-bold">Virtual Images</h1>
          <p className="text-xl text-on-seconary">Allocate Resources to be rented in instance</p>
        </article>
      </article>
      <ResourceAllocationForm />
    </section>
  )
}
