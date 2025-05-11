import 'next-auth';
import { UserRole } from '../lib/interfaces/services/user.service';

declare module 'next-auth' {
  interface User {
    id: string;
    email: string;
    name: string;
    role: UserRole;
    token: string;
  }

  interface Session {
    user: User;
    accessToken: string;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id?: string | null;
    email?: string | null;
    name?: string | null;
    role?: UserRole | null;
    accessToken?: string | null;
  }
} 