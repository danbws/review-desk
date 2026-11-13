import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ReviewSummary, Usage } from "../api";
import { useAuth } from "../auth";
import { buttonClass, Card, ErrorBox, UsageMeter } from "../components/ui";

export default function DashboardPage() {
  const { refresh } = useAuth();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [reviews, setReviews] = useState<ReviewSummary[] | null>(null);
  const [error, setError] = useState("");
  const [upgrading, setUpgrading] = useState(false);

  async function load() {
    try {
      const [u, r] = await Promise.all([api.usage(), api.reviews()]);
      setUsage(u);
      setReviews(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function upgrade() {
    setUpgrading(true);
    try {
      await api.upgrade("pro"); // fake payment provider: activates immediately
      await Promise.all([load(), refresh()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upgrade failed");
    } finally {
      setUpgrading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <Link to="/new" className={buttonClass}>
          New review
        </Link>
      </div>
      {error && <ErrorBox message={error} />}

      {usage && (
        <Card>
          <UsageMeter used={usage.used} limit={usage.limit} plan={usage.plan} />
          {usage.plan === "free" && (
            <div className="mt-4 flex items-center justify-between gap-4 text-sm">
              <p className="text-slate-600">
                Pro raises the limit to 200 reviews a month. Payments are simulated in this demo.
              </p>
              <button className={buttonClass} onClick={upgrade} disabled={upgrading}>
                Upgrade to Pro (demo)
              </button>
            </div>
          )}
        </Card>
      )}

      <Card className="p-0">
        <h2 className="border-b border-slate-200 px-5 py-3 font-semibold">Review history</h2>
        {reviews && reviews.length === 0 && (
          <p className="px-5 py-8 text-sm text-slate-500">
            No reviews yet.{" "}
            <Link to="/new" className="text-indigo-600 hover:underline">
              Paste some code
            </Link>{" "}
            to get your first one.
          </p>
        )}
        <ul className="divide-y divide-slate-100">
          {reviews?.map((r) => (
            <li key={r.id}>
              <Link
                to={`/reviews/${r.id}`}
                className="flex items-center justify-between px-5 py-3 hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium">{r.title}</p>
                  <p className="text-xs text-slate-500">
                    {r.language} · {new Date(r.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-right text-sm">
                  <span className={r.status === "failed" ? "text-red-600" : "text-slate-600"}>
                    {r.status === "done" ? `${r.finding_count} finding${r.finding_count === 1 ? "" : "s"}` : r.status}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
