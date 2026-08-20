import { ImageResponse } from "next/og";

export const alt =
  "DocSage document intelligence with evidence-backed answers";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "64px 72px",
        color: "#2d2d2d",
        backgroundColor: "#f9f4e8",
        fontFamily: "serif",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "2px solid #c9b99a",
          paddingBottom: "22px",
        }}
      >
        <div style={{ display: "flex", fontSize: 32, letterSpacing: "0.08em" }}>
          DOC<span style={{ color: "#5c3d1e" }}>SAGE</span>
        </div>
        <div
          style={{
            display: "flex",
            color: "#7a6e62",
            fontFamily: "monospace",
            fontSize: 17,
            letterSpacing: "0.12em",
          }}
        >
          DOCUMENT INTELLIGENCE
        </div>
      </div>

      <div style={{ display: "flex", gap: 52, alignItems: "stretch" }}>
        <div
          style={{
            display: "flex",
            flex: 1,
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              display: "flex",
              color: "#5c3d1e",
              fontFamily: "monospace",
              fontSize: 17,
              letterSpacing: "0.14em",
              marginBottom: 18,
            }}
          >
            EVIDENCE-FIRST ANSWERS
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              fontSize: 58,
              lineHeight: 1.06,
              letterSpacing: "-0.025em",
            }}
          >
            <span>Ask your documents.</span>
            <span>Verify every answer.</span>
          </div>
          <div
            style={{
              display: "flex",
              marginTop: 26,
              color: "#4e4039",
              fontFamily: "monospace",
              fontSize: 17,
              letterSpacing: "0.08em",
            }}
          >
            INGEST → RETRIEVE → ANALYZE → CITE
          </div>
        </div>

        <div
          style={{
            width: 340,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            border: "2px solid #a89070",
            backgroundColor: "#f2ead3",
            padding: "26px 28px",
            transform: "rotate(1deg)",
          }}
        >
          <div
            style={{
              display: "flex",
              color: "#2b5ea7",
              fontFamily: "monospace",
              fontSize: 15,
              letterSpacing: "0.12em",
            }}
          >
            RETRIEVED EVIDENCE · 01
          </div>
          <div
            style={{
              display: "flex",
              color: "#4e4039",
              fontSize: 24,
              lineHeight: 1.45,
            }}
          >
            “Every conclusion stays connected to the passage that supports it.”
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              color: "#7a6e62",
              fontFamily: "monospace",
              fontSize: 14,
            }}
          >
            <span>CITATION READY</span>
            <span>0.94 MATCH</span>
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          color: "#7a6e62",
          fontFamily: "monospace",
          fontSize: 15,
          letterSpacing: "0.08em",
        }}
      >
        <span>RAG · PGVECTOR · GPT-4O</span>
        <span>DOCSAGE.PHOENIX7.DEV</span>
      </div>
    </div>,
    size,
  );
}
