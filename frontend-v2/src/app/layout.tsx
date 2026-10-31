import type { Metadata } from 'next';
import { Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const spaceGrotesk = Space_Grotesk({
  variable: '--font-display',
  subsets: ['latin'],
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'ECRformer + PatchGAN | SAR-Guided Satellite Cloud Removal Telemetry',
  description:
    'Mission-control telemetry console for SAR-guided optical satellite cloud removal utilizing ECRformer transformer architecture and PatchGAN discriminators on Sentinel-2 optical and Sentinel-1 SAR imagery.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} dark h-full overflow-hidden antialiased`}
    >
      <body className="h-full overflow-hidden bg-[#0b0f15] text-[#e2e8f0] font-sans selection:bg-[#00f0ff]/20 selection:text-[#00f0ff]">
        {children}
      </body>
    </html>
  );
}
