import { AuthMode } from '@renderer/types'
import AuthSection from './AuthSection'
import HeroSection from './HeroSection'

type LoginViewProps = {
  mode: AuthMode
}
export default function LoginView({ mode }: LoginViewProps): React.JSX.Element {
  return (
    <section className="flex w-3/4 min-h-fit h-160 bg-surface my-16 ">
      <HeroSection />
      <AuthSection mode={mode} />
    </section>
  )
}
