type DialogProps = {
  children: React.ReactNode
  open: boolean
  //   setOpen: (arg: boolean) => void
}
export function Dialog({ children, open }: DialogProps): React.JSX.Element | null {
  if (!open) return null
  return (
    <dialog
      open
      className="flex flex-col items-center gap-4 rounded-xl p-8 bg-elevated backdrop:bg-black/50 min-w-80"
    >
      {children}
    </dialog>
  )
}
