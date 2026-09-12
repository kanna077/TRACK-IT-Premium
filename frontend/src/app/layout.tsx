import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TRACK-IT | Smart Campus Lost & Found",
  description:
    "AI-assisted campus lost and found with secure ownership claims and QR handover.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
