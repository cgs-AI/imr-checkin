"use client";

import { useEffect } from "react";

type Props = {
  message: string;
  onDone: () => void;
};

export default function ConfirmationStep({ message, onDone }: Props) {
  useEffect(() => {
    const handle = setTimeout(onDone, 30_000);
    return () => clearTimeout(handle);
  }, [onDone]);

  return (
    <section className="card" aria-labelledby="confirmation-heading">
      <h1 id="confirmation-heading" className="success">
        You&apos;re checked in
      </h1>
      <p>{message}</p>
      <p className="muted">
        This screen will reset for the next visitor shortly.
      </p>
      <button onClick={onDone}>Done</button>
    </section>
  );
}
