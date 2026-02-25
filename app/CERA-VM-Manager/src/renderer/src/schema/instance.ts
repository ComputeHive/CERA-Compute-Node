import { z } from 'zod'

export const instanceResourcesSchema = z.object({
  cpu: z.number().refine((num) => num > 0, 'Rented CPU Cores must be positive'),
  ram: z.number().refine((num) => num > 0, 'Rented RAM must be positive'),
  disk: z.number().refine((num) => num > 0, 'Rented DISK must be positive')
})

export type InstanceResources = z.infer<typeof instanceResourcesSchema>
