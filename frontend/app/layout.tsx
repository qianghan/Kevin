import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";
import { StagewiseToolbar } from '@stagewise/toolbar-next';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Kai",
  description: "Kai - Your AI Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const stagewiseConfig = { plugins: [] };
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        {process.env.NODE_ENV === 'development' && (
          <StagewiseToolbar config={stagewiseConfig} />
        )}
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
