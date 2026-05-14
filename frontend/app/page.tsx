import Link from "next/link";

export default function HomePage() {
  return (
    <section className="card">
      <h1>IMR visitor check-in</h1>
      <p>Welcome to Irish Manufacturing Research.</p>
      <p className="muted">
        Please use this form on your own phone to check in for your visit.
      </p>
      <Link href="/checkin" aria-label="Start check-in">
        <button>Start check-in</button>
      </Link>
    </section>
  );
}
