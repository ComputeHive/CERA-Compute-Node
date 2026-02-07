import AuthSection from './AuthSection'
import HeroSection from './HeroSection'

export default function LoginView(): React.JSX.Element {
  return (
    <section className="flex w-3/4 min-h-fit h-160 bg-surface my-16">
      <HeroSection />
      <AuthSection />
    </section>
  )
}
