import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ECRformer + PatchGAN | SAR-Guided Satellite Cloud Removal Showcase",
  description:
    "Interactive showcase of SAR-Guided Optical Satellite Cloud Removal using ECRformer and PatchGAN on the SEN12MS-CR dataset. Research project by Vaishnav T Prakash (M.Sc. CS AI, CUSAT).",
  keywords: [
    "ECRformer",
    "PatchGAN",
    "Satellite Cloud Removal",
    "Sentinel-1 SAR",
    "Sentinel-2 Optical",
    "SEN12MS-CR",
    "Deep Learning",
    "Remote Sensing",
  ],
  authors: [{ name: "Vaishnav T Prakash" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
