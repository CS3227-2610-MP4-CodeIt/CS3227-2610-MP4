import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { DraftStatus, DraftGuidance } from "./DraftFeedback";

describe("draft feedback", () => {
  it("explains unavailable storage without promising a save", () => {
    const html = renderToStaticMarkup(
      <>
        <DraftStatus status="unavailable" />
        <DraftGuidance origin="Started with an empty editor." />
      </>,
    );
    expect(html).toContain("Draft could not be saved on this device");
    expect(html).toContain("when available");
    expect(html).not.toContain("Edits are saved on this device");
  });
  it("reports successful device-local saving", () => {
    const html = renderToStaticMarkup(
      <>
        <DraftStatus status="saved" />
        <DraftGuidance origin="Started from your device draft." />
      </>,
    );
    expect(html).toContain("Draft saved on this device");
    expect(html).toContain("submit to send your code");
  });
});
