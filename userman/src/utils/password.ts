import { hash } from 'bcrypt';

export const generateHash = async (password: string): Promise<string> => {
  return await hash(password, 12);
}; 