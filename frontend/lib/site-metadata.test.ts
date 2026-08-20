import { describe, expect, it } from "vitest";

import { DOCSAGE_METADATA } from "./site-metadata";

describe("DocSage metadata", () => {
  it("configures the canonical production identity and social card", () => {
    expect(DOCSAGE_METADATA.metadataBase?.toString()).toBe(
      "https://docsage.phoenix7.dev/",
    );
    expect(DOCSAGE_METADATA.alternates?.canonical).toBe("/");
    expect(DOCSAGE_METADATA.title).toBeTruthy();
    expect(DOCSAGE_METADATA.description).toBeTruthy();
    expect(DOCSAGE_METADATA.openGraph).toMatchObject({
      type: "website",
      url: "/",
      images: [
        expect.objectContaining({
          url: "/opengraph-image",
          width: 1200,
          height: 630,
        }),
      ],
    });
    expect(DOCSAGE_METADATA.twitter).toMatchObject({
      card: "summary_large_image",
      images: ["/opengraph-image"],
    });
  });
});
