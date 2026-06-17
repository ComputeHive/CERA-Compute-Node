import { AuthMode } from '@renderer/types'
import LoginForm from '../Login'
import SignupForm from '../Signup'

type AuthSectionProps = {
  mode: AuthMode
}
export default function AuthSection({ mode }: AuthSectionProps): React.JSX.Element {
  const headingContent = mode == 'Login' ? 'Welcome Back' : 'New at CERA'
  const authForm = mode === 'Login' ? <LoginForm /> : <SignupForm />
  // const modeButtonContent =
  //   mode == 'Login' ? "You're new. Sign up here" : 'You have already account. Sign in here'

  return (
    <section className="flex flex-col items-start justify-start p-8 pl-16 gap-8 w-full overflow-y-auto">
      <article className="flex flex-col items-start justify-center gap-4">
        <h1 className="text-3xl font-bold text-on-primary">{headingContent} !</h1>
        <p className="text-xl text-on-seconary">Enter your credentials to start your journey</p>
      </article>
      <article className="w-full">{authForm}</article>
    </section>
  )
}
