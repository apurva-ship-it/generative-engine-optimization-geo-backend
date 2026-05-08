import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

export interface CreateUserInput {
  email: string;
  name: string;
  password: string;
  fullName?: string;
  phone?: string;
  age?: number;
  sex?: string;
}

export async function createUser(input: CreateUserInput) {
  const { email, name, password, fullName, phone, age, sex } = input;
  const saltRounds = 10;
  const passwordHash = await bcrypt.hash(password, saltRounds);
  const user = await prisma.user.create({
    data: {
      email,
      name,
      passwordHash,
      fullName,
      phone,
      age,
      sex,
    },
  });
  return {
    status: 201,
    id: user.id,
    data: user,
  };
}

export async function findByMobile(phone: string | undefined) {
  if (!phone) return null;
  return prisma.user.findFirst({ where: { phone } });
}
