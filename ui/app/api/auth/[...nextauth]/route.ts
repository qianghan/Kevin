import CredentialsProvider from 'next-auth/providers/credentials';
import NextAuth, { NextAuthOptions } from 'next-auth';

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Missing credentials');
        }

        try {
          // Replace with your actual backend API endpoint
          const response = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password
            })
          });

          if (!response.ok) {
            throw new Error('Invalid credentials');
          }

          const { user, token } = await response.json();

          return {
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role,
            token
          };
        } catch (error) {
          console.error('Authentication error:', error);
          return null;
        }
      }
    })
  ],
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token = {
          ...token,
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
          accessToken: user.token
        };
      }
      return token;
    },
    async session({ session, token }) {
      return {
        ...session,
        user: {
          ...session.user,
          id: token.id || '',
          email: token.email || '',
          name: token.name || '',
          role: token.role || 'guest'
        },
        accessToken: token.accessToken || ''
      };
    }
  },
  pages: {
    signIn: '/login',
    error: '/login',
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST }; 