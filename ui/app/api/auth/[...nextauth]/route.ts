import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";

// Enhanced logging for NextAuth initialization
console.log("NextAuth handler initializing...");

// Log auth options (omitting secrets)
console.log("Auth options:", {
  session: authOptions.session,
  providers: authOptions.providers.map(p => p.id),
  debug: authOptions.debug,
  pages: authOptions.pages,
  cookies: !!authOptions.cookies,
});

// Create the NextAuth handler
const handler = NextAuth(authOptions);

// Add debugging output during development
if (process.env.NODE_ENV !== 'production') {
  console.log('NextAuth handler loaded in development mode with extra logging');
}

// Export handler as GET and POST functions
export { handler as GET, handler as POST }; 