import { Wordmark } from "../../components/Wordmark/Wordmark";
import { Stamp } from "../../components/Stamp/Stamp";
import styles from "./Header.module.css";

interface HeaderProps {
  documentCount: number;
}

export function Header({ documentCount }: HeaderProps) {
  return (
    <header className={styles.header}>
      <Wordmark onDark size="sm" />
      <div className={styles.right}>
        <Stamp
          tone="granted"
          size="sm"
          lines={[documentCount === 1 ? "1 document loaded" : `${documentCount} documents loaded`]}
        />
      </div>
    </header>
  );
}
