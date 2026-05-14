"use client";

import { useEffect, useState } from "react";

type Props = {
  warningAfterMs: number;
  resetAfterMs: number;
  onReset: () => void;
};

export default function InactivityGuard({
  warningAfterMs,
  resetAfterMs,
  onReset,
}: Props) {
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    let warningTimer: ReturnType<typeof setTimeout>;
    let resetTimer: ReturnType<typeof setTimeout>;

    const schedule = () => {
      setShowWarning(false);
      clearTimeout(warningTimer);
      clearTimeout(resetTimer);
      warningTimer = setTimeout(() => setShowWarning(true), warningAfterMs);
      resetTimer = setTimeout(() => {
        setShowWarning(false);
        onReset();
      }, resetAfterMs);
    };

    const onActivity = () => schedule();

    schedule();

    const events: (keyof DocumentEventMap)[] = [
      "pointerdown",
      "keydown",
      "touchstart",
    ];
    events.forEach((e) => document.addEventListener(e, onActivity));

    return () => {
      clearTimeout(warningTimer);
      clearTimeout(resetTimer);
      events.forEach((e) => document.removeEventListener(e, onActivity));
    };
  }, [warningAfterMs, resetAfterMs, onReset]);

  if (!showWarning) return null;

  return (
    <div
      role="alertdialog"
      aria-labelledby="inactivity-heading"
      className="inactivity-overlay"
    >
      <div className="card inactivity-card">
        <h2 id="inactivity-heading">Are you still there?</h2>
        <p>Tap the screen to keep going. Otherwise the form will reset.</p>
      </div>
    </div>
  );
}
