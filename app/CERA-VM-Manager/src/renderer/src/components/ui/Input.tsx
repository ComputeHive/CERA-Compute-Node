import { type FieldError } from 'react-hook-form'
type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  error?: FieldError
}
export default function Input({ error, ...props }: InputProps): React.JSX.Element {
  return (
    <div className="flex flex-col items-start justify-center gap-1 my-4">
      <label htmlFor={props.name} className="text-xl font-normal text-disabled pl-2">
        {props.name}
      </label>
      <input
        {...props}
        className="bg-elevated px-4 py-1 rounded-2xl placeholder:text-disabled text-disabled border-2 border-default"
      />
      {error && <p className="text-error text-xl">{error.message}</p>}
    </div>
  )
}
