import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ReviewDetail } from "../api";
import { Card, ErrorBox, FindingCard } from "../components/ui";

export default function ReviewDetailPage() {
  const { id } = useParams();
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .review(Number(id))
      .then(setReview)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, [id]);

  if (error)
    return (
      <div className="space-y-3">
        <ErrorBox message={error} />
        <Link to="/" className="text-sm text-indigo-600 hover:underline">
          Back to dashboard
        </Link>
      </div>
    );
  if (!review) return <p className="text-slate-500">Loading…</p>;

  const lines = review.code.split("\n");
  const flagged = new Set(review.findings.map((f) => f.line).filter((l): l is number => l != null));

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-sm text-indigo-600 hover:underline">
          ← Dashboard
        </Link>
        <h1 className="mt-1 text-xl font-semibold">{review.title}</h1>
        <p className="text-sm text-slate-500">
          {review.language} · {new Date(review.created_at).toLocaleString()} · provider:{" "}
          {review.provider} · {review.status}
        </p>
        {review.summary && <p className="mt-2 text-sm text-slate-700">{review.summary}</p>}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="overflow-hidden p-0">
          <h2 className="border-b border-slate-200 px-4 py-2 text-sm font-semibold">Code</h2>
          <pre className="max-h-[32rem] overflow-auto py-2 font-mono text-xs">
            {lines.map((l, i) => (
              <div key={i} className={`flex px-2 ${flagged.has(i + 1) ? "bg-red-50" : ""}`}>
                <span className="w-8 shrink-0 select-none pr-2 text-right text-slate-400">{i + 1}</span>
                <span className="whitespace-pre-wrap break-all">{l}</span>
              </div>
            ))}
          </pre>
        </Card>
        <div>
          <h2 className="mb-3 font-semibold">Findings ({review.findings.length})</h2>
          {review.findings.length === 0 && (
            <p className="text-sm text-slate-500">No findings recorded.</p>
          )}
          <ul className="space-y-3">
            {review.findings.map((f, i) => (
              <FindingCard key={i} finding={f} />
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
