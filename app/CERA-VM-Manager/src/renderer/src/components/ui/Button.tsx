import { cn } from '@renderer/lib/utils'
import { cva, VariantProps } from 'class-variance-authority'

const buttonVariants = cva(
  [
    'flex',
    'items-center',
    'justify-center',
    'py-4',
    'text-xl',
    'border',
    'rounded-xl',
    'mt-2',
    'cursor-pointer',
    'disabled:bg-gray-400 '
  ],
  {
    variants: {
      intent: {
        primary: ['bg-active', 'text-surface'],
        link: [
          'bg-transparent',
          'underline',
          'text-on-primary',
          'text-xl',
          'hover:text-on-secondary',
          'border-none'
        ],
        success: ['bg-success-back', 'text-sucess', 'border-success'],
        error: ['bg-error', 'text-surface']
      },
      size: {
        xl: ['px-8', 'gap-2'],
        sm: ['px-4', 'py-4', 'gap-1']
      }
    },
    defaultVariants: {
      intent: 'primary',
      size: 'xl'
    }
  }
)
type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    children?: React.JSX.Element | string
  }
export default function Button({
  intent,
  size,
  children,
  className,
  ...props
}: ButtonProps): React.JSX.Element {
  return (
    <button {...props} className={cn(buttonVariants({ intent, size }), className)}>
      {children}
    </button>
  )
}
