import type { Metadata } from "next";
import { Special_Elite, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const specialElite = Special_Elite({
  variable: "--font-special-elite",
  subsets: ["latin"],
  weight: ["400"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-ibm-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "DocSage — Document Intelligence",
  description:
    "AI-powered document analysis with RAG and full retrieval traceability",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${specialElite.variable} ${ibmPlexMono.variable} ${ibmPlexSans.variable}`}
      >
        {/* Hidden SVG filter — hand-drawn displacement for borders */}
        <svg
          aria-hidden="true"
          style={{
            position: "absolute",
            width: 0,
            height: 0,
            overflow: "hidden",
          }}
        >
          <defs>
            <filter id="roughpaper" x="-5%" y="-5%" width="110%" height="110%">
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.05"
                numOctaves="4"
                seed="3"
                result="noise"
              />
              <feDisplacementMap
                in="SourceGraphic"
                in2="noise"
                scale="1.8"
                xChannelSelector="R"
                yChannelSelector="G"
              />
            </filter>
          </defs>
        </svg>
        {children}
      </body>
    </html>
  );
}
