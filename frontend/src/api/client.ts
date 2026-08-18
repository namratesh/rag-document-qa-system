import { apiPath } from "./config";
import {
  ApiError,
  type ConversationSummary,
  type ConversationThreadResponse,
  type CreateConversationResponse,
  type DocumentsResponse,
  type MessageResponse,
  type StreamEvent,
  type UploadDocumentsResponse,
} from "./types";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { headers, ...rest } = options;

  const res = await fetch(apiPath(path), {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export function listConversations(signal?: AbortSignal): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>("/api/conversations", { signal });
}

export function createConversation(): Promise<CreateConversationResponse> {
  return request<CreateConversationResponse>("/api/conversations", { method: "POST" });
}

export function getConversation(
  convId: string,
  signal?: AbortSignal,
): Promise<ConversationThreadResponse> {
  return request<ConversationThreadResponse>(`/api/conversations/${convId}`, { signal });
}

export function sendMessage(convId: string, message: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/api/conversations/${convId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function listDocuments(signal?: AbortSignal): Promise<DocumentsResponse> {
  return request<DocumentsResponse>("/api/documents", { signal });
}

export async function uploadDocuments(files: File[]): Promise<UploadDocumentsResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const res = await fetch(apiPath("/api/documents"), {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<UploadDocumentsResponse>;
}

interface StreamHandlers {
  onDelta: (text: string) => void;
  onDone: (event: Extract<StreamEvent, { type: "done" }>) => void;
}

export async function sendMessageStream(
  convId: string,
  message: string,
  { onDelta, onDone }: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(apiPath(`/api/conversations/${convId}/messages/stream`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
    signal,
  });

  if (!res.ok || !res.body) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");

      const dataLine = frame.split("\n").find((l) => l.startsWith("data: "));
      if (!dataLine) continue;

      const event = JSON.parse(dataLine.slice("data: ".length)) as StreamEvent;
      if (event.type === "delta") {
        onDelta(event.text);
      } else {
        onDone(event);
      }
    }
  }
}
