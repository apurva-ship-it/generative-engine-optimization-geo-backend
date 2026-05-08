import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function getUserById(id: string) {
  return prisma.user.findUnique({ where: { id } });
}

export async function updateUser(id: string, data: { name?: string; email?: string }) {
  return prisma.user.update({ where: { id }, data });
}

export async function deleteUser(id: string) {
  return prisma.user.delete({ where: { id } });
}
