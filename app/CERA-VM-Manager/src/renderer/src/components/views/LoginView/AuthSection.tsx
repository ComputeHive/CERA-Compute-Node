import { useState } from 'react'
import LoginForm from '../Login'
import SignupForm from '../Signup'
import Button from '../../ui/Button'

type AuthMode = 'Login' | 'Sign up'
export default function AuthSection(): React.JSX.Element {
  const [mode, setMode] = useState<AuthMode>('Login')
  const headingContent = mode == 'Login' ? 'Welcome Back' : 'New at CERA'
  const authForm = mode === 'Login' ? <LoginForm /> : <SignupForm />
  const modeButtonContent =
    mode == 'Login' ? "You're new. Sign up here" : 'You have already account. Sign in here'
  const handleModeButtonClick = (): void => {
    setMode((prev) => (prev == 'Login' ? 'Sign up' : 'Login'))
  }
  return (
    <section className="flex flex-col items-start justify-start p-16 gap-16 w-full">
      <article className="flex flex-col items-start justify-center gap-4">
        <h1 className="text-3xl font-bold text-on-primary">{headingContent} !</h1>
        <p className="text-xl text-on-seconary">Enter your credentials to start your journey</p>
      </article>
      <article className="w-full">{authForm}</article>
      <Button name="mode" intent="link" size="sm" onClick={handleModeButtonClick}>
        {modeButtonContent}
      </Button>
    </section>
  )
}
