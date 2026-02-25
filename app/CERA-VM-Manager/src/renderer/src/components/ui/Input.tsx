import { type FieldError } from 'react-hook-form'

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  error?: FieldError
}

export default function Input({ error, ...props }: InputProps): React.JSX.Element {
  const isRange = props.type === 'range'

  return (
    <div className="flex flex-col items-start justify-center gap-1 my-4 w-full">
      <label htmlFor={props.name} className="text-xl font-normal text-disabled pl-2 capitalize">
        {props.name}
      </label>

      {isRange ? (
        <div className="w-full flex flex-col gap-1">
          <div className="flex items-center gap-4 w-full">
            <input
              {...props}
              className="w-full h-2 rounded-full appearance-none cursor-pointer
                bg-elevated
                [&::-webkit-slider-runnable-track]:rounded-full
                [&::-webkit-slider-runnable-track]:h-2
                [&::-webkit-slider-runnable-track]:bg-blue-300
                [&::-webkit-slider-thumb]:appearance-none
                [&::-webkit-slider-thumb]:w-5
                [&::-webkit-slider-thumb]:h-5
                [&::-webkit-slider-thumb]:-mt-1.5
                [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-primary
                [&::-webkit-slider-thumb]:shadow-md
                [&::-moz-range-thumb]:w-5
                [&::-moz-range-thumb]:h-5
                [&::-moz-range-thumb]:rounded-full
                [&::-moz-range-thumb]:bg-primary
                [&::-moz-range-thumb]:border-0"
              style={{
                background: `linear-gradient(to right, var(--color-primary) 0%, var(--color-primary) ${
                  ((Number(props.value ?? props.defaultValue ?? props.min ?? 0) -
                    Number(props.min ?? 0)) /
                    (Number(props.max ?? 100) - Number(props.min ?? 0))) *
                  100
                }%, var(--color-elevated) ${
                  ((Number(props.value ?? props.defaultValue ?? props.min ?? 0) -
                    Number(props.min ?? 0)) /
                    (Number(props.max ?? 100) - Number(props.min ?? 0))) *
                  100
                }%, var(--color-elevated) 100%)`
              }}
            />
            <span className="text-xl font-semibold text-disabled min-w-16 text-right">
              {props.value ?? props.defaultValue ?? props.min ?? 0}
            </span>
          </div>
          <div className="flex justify-between text-sm text-disabled px-1">
            <span>{props.min ?? 0}</span>
            <span>{Math.round(Number(props.max) / 3)}</span>
            <span>{Math.round((Number(props.max) / 3) * 2)}</span>
            <span>{props.max}</span>
          </div>
        </div>
      ) : (
        <input
          {...props}
          className="bg-elevated px-4 py-1 rounded-2xl placeholder:text-disabled text-disabled border-2 border-default"
        />
      )}

      {error && <p className="text-error text-xl">{error.message}</p>}
    </div>
  )
}
