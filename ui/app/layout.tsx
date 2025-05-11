import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/components/auth/SessionProvider";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { I18nProvider } from "@/components/I18nProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Kevin.AI - Your University Assistant",
  description: "A powerful AI assistant for university students and parents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className} suppressHydrationWarning={true}>
        <SessionProvider>
          <AuthProvider>
            <I18nProvider>
              {children}
            </I18nProvider>
          </AuthProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
