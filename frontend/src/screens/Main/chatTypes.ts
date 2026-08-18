import type { Citation } from "../../api/types";

export interface UIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: (Citation | string)[];
  restricted?: boolean;
  pending?: boolean;
  streaming?: boolean;
}

export function isFullCitation(c: Citation | string): c is Citation {
  return typeof c !== "string";
}

export function citationLabel(c: Citation | string): string {
  if (!isFullCitation(c)) return c;
  return `${c.filename}, p. ${c.page_number}`;
}
