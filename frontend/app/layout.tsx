import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// Fonts load panrom
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Browser tab-la theriyara title + description
export const metadata: Metadata = {
  title: "Face QR Studio",
  description: "Turn your face into a scannable QR code",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning: theme class maarum bodhu warning varaama irukka
    <html lang="en" suppressHydrationWarning>
      <body
  className={`${geistSans.variable} ${geistMono.variable} antialiased`}
  suppressHydrationWarning
>
  {children}
</body>
    </html>
  );
}