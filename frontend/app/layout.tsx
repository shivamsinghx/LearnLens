import type { Metadata } from "next";
import { Instrument_Serif, Inter, Geist } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-serif-display",
  weight: "400",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LearnLens",
  description: "Turn your notes into knowledge.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={cn("h-full", "antialiased", inter.variable, instrumentSerif.variable, "font-sans", geist.variable)}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-white font-sans text-foreground" suppressHydrationWarning>
        <a
          href="#content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-foreground"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
