import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Use the specific fonts requested
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/700.css";
import "@fontsource/outfit/300.css";
import "@fontsource/outfit/500.css";
import "@fontsource/outfit/700.css";
import "@fontsource/work-sans/400.css";

export const metadata: Metadata = {
  title: "Deriverse | Analytics Terminal",
  description: "Production-grade trading analytics for the Memory Parasite Protocol.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
