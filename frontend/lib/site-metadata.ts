import type { Metadata } from "next";

const title = "DocSage — Ask Documents, Verify Answers";
const description =
  "Ask focused questions of your documents and verify every answer against retrieved passages and citations.";

export const DOCSAGE_METADATA: Metadata = {
  metadataBase: new URL("https://docsage.phoenix7.dev"),
  title,
  description,
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    url: "/",
    siteName: "DocSage",
    title,
    description,
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "DocSage document intelligence with evidence-backed answers",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/opengraph-image"],
  },
};
