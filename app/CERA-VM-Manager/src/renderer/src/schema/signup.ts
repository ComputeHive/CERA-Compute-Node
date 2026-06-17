import { z } from 'zod'

export const signupSchema = z.object({
  username: z.string(),
  password: z
    .string()
    .min(8, 'Password must be 8 characters long at least.')
    .refine(
      (password) => /[A-Z]/.test(password),
      'Password must contain at least one uppercase letter.'
    )
    .refine((password) => /[0-9]/.test(password), 'Password must contain at least one number.')
    .refine(
      (password) => /[^A-Z0-9a-z]/.test(password),
      'Password must contain at least one special character.'
    ),
  cpu_model: z.string(),
  total_cpu_cores: z.number().refine((num) => num > 0, 'Rented CPU Cores must be positive'),
  total_ram_mb: z.number().refine((num) => num > 0, 'Rented RAM must be positive'),
  total_disk_mb: z.number().refine((num) => num > 0, 'Rented DISK must be positive'),
  wallet_address: z
    .string()
    .refine((arg) => arg.match(/^0x[a-fA-F0-9]{40}$/), 'Wrong Etherum Wallet Address')
})

export type RegisterRequest = z.infer<typeof signupSchema>
