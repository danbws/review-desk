import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { buttonClass, Card, ErrorBox, inputClass } from "../components/ui";

export default function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const { access_token } = await (mode === "signup" ? api.signup : api.login)(email, password);
      await signIn(access_token);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <h1 className="mb-1 text-2xl font-semibold tracking-tight">
        review<span className="text-indigo-600">-desk</span>
      </h1>
      <p className="mb-6 text-sm text-slate-600">AI code review, streamed live.</p>
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <h2 className="font-semibold">{mode === "signup" ? "Create your account" : "Sign in"}</h2>
          <label className="block text-sm">
            Email
            <input
              className={`${inputClass} mt-1`}
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            Password
            <input
              className={`${inputClass} mt-1`}
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error && <ErrorBox message={error} />}
          <button className={`${buttonClass} w-full`} disabled={busy}>
            {mode === "signup" ? "Sign up" : "Sign in"}
          </button>
        </form>
      </Card>
      <p className="mt-4 text-center text-sm text-slate-600">
        {mode === "signup" ? (
          <>
            Have an account?{" "}
            <Link className="text-indigo-600 hover:underline" to="/login">
              Sign in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link className="text-indigo-600 hover:underline" to="/signup">
              Create an account
            </Link>
          </>
        )}
      </p>
    </div>
  );
}
