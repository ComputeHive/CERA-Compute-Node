export default function HeroSection(): React.JSX.Element {
  return (
    <section className="flex flex-col items-center justify-center py-12 gap-12 server-background w-full">
      <img src="/src/assets/logo.png" alt="logo" width={288} height={288} />
      <article className="flex flex-col items-start justify-start px-8 gap-4">
        <h2 className="text-3xl text-surface font-bold">Rent Your PC. Earn while it works</h2>
        <p className="text-lg text-gray-200">
          Turn your idle computing power into income by hosting secure job-running instances on
          CERA.
        </p>
      </article>
    </section>
  )
}
