import { FormEvent, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, Finding, streamReview } from "../api";
import { buttonClass, Card, ErrorBox, FindingCard, inputClass } from "../components/ui";

const SAMPLE = `import sqlite3

password = "hunter2"  # TODO: move to env

def find_user(db, name):
    q = "SELECT * FROM users WHERE name = '" + name + "'"
    try:
        return db.execute(q).fetchone()
    except:
        print("failed")

def calc(expr):
    return eval(expr)
`;

type Phase = "idle" | "review" | "verify" | "done";

export default function NewReviewPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [raw, setRaw] = useState("");
  const [drafts, setDrafts] = useState<Finding[]>([]);
  const [final, setFinal] = useState<Finding[] | null>(null);
  const [summary, setSummary] = useState("");
  const [reviewId, setReviewId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [upgradeHint, setUpgradeHint] = useState(false);
  const abort = useRef<AbortController | null>(null);

  const running = phase === "review" || phase === "verify";

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setUpgradeHint(false);
    setRaw("");
    setDrafts([]);
    setFinal(null);
    setSummary("");
    setReviewId(null);
    setPhase("review");
    abort.current = new AbortController();
    try {
      await streamReview(
        { title: title || "Untitled review", language, code },
        ({ event, data }) => {
          if (event === "review") setReviewId(data.id);
          else if (event === "token") setRaw((r) => r + data.text);
          else if (event === "pass") setPhase(data.name === "verify" ? "verify" : "review");
          else if (event === "draft") setDrafts((d) => [...d, data]);
          else if (event === "final") {
            setFinal(data.findings);
            setSummary(data.summary);
          } else if (event === "error") setError(data.message);
          else if (event === "done") setPhase("done");
        },
        abort.current.signal,
      );
      setPhase((p) => (p === "done" ? p : "idle"));
    } catch (err) {
      setPhase("idle");
      if (err instanceof ApiError) {
        setError(err.message);
        if (err.status === 402) setUpgradeHint(true);
      } else if ((err as Error).name !== "AbortError") {
        setError("Connection lost while streaming.");
      }
    }
  }

  const shown = final ?? drafts;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={submit} className="space-y-4">
        <h1 className="text-xl font-semibold">New review</h1>
        <div className="grid grid-cols-3 gap-3">
          <label className="col-span-2 block text-sm">
            Title
            <input
              className={`${inputClass} mt-1`}
              value={title}
              maxLength={200}
              placeholder="e.g. Login handler"
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            Language
            <select
              className={`${inputClass} mt-1`}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {["python", "typescript", "javascript", "java", "go", "sql", "diff", "other"].map(
                (l) => (
                  <option key={l}>{l}</option>
                ),
              )}
            </select>
          </label>
        </div>
        <label className="block text-sm">
          Diff or code
          <textarea
            className={`${inputClass} mt-1 h-72 font-mono text-xs`}
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Paste a diff or a snippet…"
          />
        </label>
        <div className="flex items-center gap-3">
          <button className={buttonClass} disabled={running || !code.trim()}>
            {running ? "Reviewing…" : "Run review"}
          </button>
          <button type="button" className="text-sm text-indigo-600 hover:underline" onClick={() => setCode(SAMPLE)}>
            Use sample code
          </button>
          {running && (
            <button type="button" className="text-sm text-slate-500 hover:underline" onClick={() => abort.current?.abort()}>
              Cancel
            </button>
          )}
        </div>
        {error && <ErrorBox message={error} />}
        {upgradeHint && (
          <p className="text-sm">
            <Link to="/" className="text-indigo-600 hover:underline">
              Go to the dashboard to upgrade
            </Link>
            .
          </p>
        )}
      </form>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Live review</h2>
          <span className="text-xs text-slate-500" aria-live="polite">
            {phase === "review" && "Pass 1/2: reviewing…"}
            {phase === "verify" && "Pass 2/2: verifying and deduplicating…"}
            {phase === "done" && "Done"}
          </span>
        </div>
        {phase === "idle" && !raw && !error && (
          <Card>
            <p className="text-sm text-slate-500">
              Findings stream in here while the model works, then a second pass verifies them.
            </p>
          </Card>
        )}
        {raw && (
          <pre className="max-h-40 overflow-auto rounded-lg bg-slate-900 p-3 font-mono text-xs text-emerald-300">
            {raw}
            {running && <span className="animate-pulse">▍</span>}
          </pre>
        )}
        <ul className="space-y-3">
          {shown.map((f, i) => (
            <FindingCard key={i} finding={f} dim={final === null && phase === "verify"} />
          ))}
        </ul>
        {summary && <p className="text-sm text-slate-600">{summary}</p>}
        {phase === "done" && reviewId && (
          <button className={buttonClass} onClick={() => navigate(`/reviews/${reviewId}`)}>
            Open saved review
          </button>
        )}
      </section>
    </div>
  );
}
