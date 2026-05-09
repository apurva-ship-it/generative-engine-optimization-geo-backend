import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

export interface RegisterInput {
  fullName: string;
  email: string;
  mobile: string;
  age: number;
  sex: string;
  password: string;
}

export async function registerUser(input: RegisterInput) {
  const passwordHash = await bcrypt.hash(input.password, 10);
  const user = await prisma.user.create({
    data: {
      fullName: input.fullName,
      email: input.email,
      mobile: input.mobile,
      age: input.age,
      sex: input.sex,
      passwordHash,
    },
  });
  return { id: user.id, fullName: user.fullName, email: user.email };
}

export async function getUserByEmail(email: string) {
  return prisma.user.findUnique({ where: { email } });
}

export async function getUserById(id: string) {
  return prisma.user.findUnique({ where: { id } });
}
