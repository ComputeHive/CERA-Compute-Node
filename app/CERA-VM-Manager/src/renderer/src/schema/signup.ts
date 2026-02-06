import { z } from 'zod'

export const signupSchema = z
  .object({
    Username: z.string(),
    Email: z.email(),
    Password: z
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
    'Repeat Password': z.string()
  })
  .refine((data) => data['Password'] == data['Repeat Password'], {
    error: 'Passwords do not match',
    path: ['Repeat Password']
  })
export type SignUpType = z.infer<typeof signupSchema>
