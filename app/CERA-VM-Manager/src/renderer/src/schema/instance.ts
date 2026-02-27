import { z } from 'zod'

export const instanceResourcesSchema = z.object({
  CPU: z.number().refine((num) => num > 0, 'Rented CPU Cores must be positive'),
  RAM: z.number().refine((num) => num > 0, 'Rented RAM must be positive'),
  Disk: z.number().refine((num) => num > 0, 'Rented DISK must be positive')
})

export type InstanceResources = z.infer<typeof instanceResourcesSchema>
