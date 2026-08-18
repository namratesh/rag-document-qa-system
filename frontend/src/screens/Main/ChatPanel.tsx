import { useEffect, useRef } from "react";
import { Message } from "./Message";
import { ChatInput } from "./ChatInput";
import type { UIMessage } from "./chatTypes";
import styles from "./ChatPanel.module.css";

interface ChatPanelProps {
  messages: UIMessage[];
  documentNames: string[];
  isThreadLoading: boolean;
  isSending: boolean;
  onSend: (text: string) => void;
}

function formatDocumentList(names: string[]): string {
  if (names.length === 0) return "";
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;
}

export function ChatPanel({
  messages,
  documentNames,
  isThreadLoading,
  isSending,
  onSend,
}: ChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <section className={styles.panel}>
      <div className={styles.scroll} ref={scrollRef}>
        {isThreadLoading ? (
          <div className={styles.empty}>
            <span className="mono">Loading thread…</span>
          </div>
        ) : messages.length === 0 ? (
          <div className={styles.empty}>
            <h2 className={styles.emptyTitle}>Hello!</h2>
            <p className={styles.emptyBody}>
              {documentNames.length > 0
                ? `Ask me anything about the documents you've uploaded: ${formatDocumentList(
                    documentNames,
                  )}.`
                : "No documents have been uploaded yet. Upload a PDF to get started."}
            </p>
          </div>
        ) : (
          <div className={styles.thread}>
            {messages.map((m) => (
              <Message key={m.id} message={m} />
            ))}
          </div>
        )}
      </div>
      <ChatInput onSend={onSend} disabled={isSending} />
    </section>
  );
}
