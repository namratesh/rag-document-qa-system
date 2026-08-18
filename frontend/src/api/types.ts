export interface Citation {
  chunk_id: string;
  doc_id: string;
  filename: string;
  page_number: number;
  score: number;
  text: string;
}

export interface MessageResponse {
  conv_id: string;
  answer: string;
  citations: Citation[];
}

export type StreamEvent =
  | { type: "delta"; text: string }
  | {
      type: "done";
      answer: string;
      citations: Citation[];
    };

export interface ConversationSummary {
  conv_id: string;
  title: string;
  updated_at: string;
}

export interface CreateConversationResponse {
  conv_id: string;
}

export interface ThreadMessage {
  role: "user" | "assistant";
  content: string;
  citations: (Citation | string)[];
}

export interface ConversationThreadResponse {
  conv_id: string;
  messages: ThreadMessage[];
}

export interface UploadedDocument {
  filename: string;
  doc_id: string;
  pages: number;
  chunks_stored: number;
}

export interface UploadDocumentsResponse {
  documents: UploadedDocument[];
}

export interface DocumentSummary {
  doc_id: string;
  filename: string;
  chunk_count: number;
}

export interface DocumentsResponse {
  documents: DocumentSummary[];
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
