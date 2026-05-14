import Link from "next/link";

export default function HomePage() {
  return (
    <section className="card kiosk-welcome">
      <h1>Welcome to IMR</h1>
      <p>Irish Manufacturing Research</p>
      <p className="muted">
        Tap below to let us know you&apos;re here.
      </p>
      <Link href="/checkin" aria-label="Start check-in">
        <button className="primary-action">Start check-in</button>
      </Link>
    </section>
  );
}
