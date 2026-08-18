import { useRef, useState } from "react";
import { uploadDocuments } from "../../api/client";
import { ApiError, type DocumentSummary } from "../../api/types";
import { Button } from "../../components/Button/Button";
import styles from "./UploadPanel.module.css";

interface UploadPanelProps {
  documents: DocumentSummary[];
  onUploaded: () => void;
}

const MAX_DOCUMENTS = 3;

export function UploadPanel({ documents, onUploaded }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const atLimit = documents.length >= MAX_DOCUMENTS;

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const files = Array.from(fileList).slice(0, MAX_DOCUMENTS - documents.length);
    setError(null);
    setIsUploading(true);
    try {
      await uploadDocuments(files);
      onUploaded();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Upload failed. Check the backend is running.",
      );
    } finally {
      setIsUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.title}>Documents</div>
      {documents.length === 0 ? (
        <div className={styles.empty}>No documents uploaded yet.</div>
      ) : (
        <ul className={styles.list}>
          {documents.map((d) => (
            <li key={d.doc_id} className={styles.item}>
              <span className={styles.name}>{d.filename}</span>
              <span className={styles.count}>{d.chunk_count}</span>
            </li>
          ))}
        </ul>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        multiple
        hidden
        onChange={(e) => handleFiles(e.target.files)}
      />
      <Button
        variant="secondary"
        block
        disabled={isUploading || atLimit}
        onClick={() => inputRef.current?.click()}
      >
        {isUploading ? "Uploading…" : atLimit ? "Upload limit reached (3)" : "Upload PDF"}
      </Button>
      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}
