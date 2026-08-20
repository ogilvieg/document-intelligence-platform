import { describe, expect, it } from "vitest";

import OpenGraphImage, { contentType, size } from "./opengraph-image";

describe("Open Graph image", () => {
  it("serves the social-card PNG at 1200 by 630", () => {
    const response = OpenGraphImage();

    expect(size).toEqual({ width: 1200, height: 630 });
    expect(contentType).toBe("image/png");
    expect(response.headers.get("content-type")).toContain("image/png");
  });
});
