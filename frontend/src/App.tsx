import { Link, NavLink, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import NewReviewPage from "./pages/NewReviewPage";
import ReviewDetailPage from "./pages/ReviewDetailPage";

function Shell() {
  const { user, loading, signOut } = useAuth();
  if (loading) return <p className="p-8 text-slate-500">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  const nav = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-1.5 text-sm font-medium ${isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:text-slate-900"}`;
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-3">
          <Link to="/" className="font-semibold tracking-tight">
            review<span className="text-indigo-600">-desk</span>
          </Link>
          <nav className="flex gap-1">
            <NavLink to="/" end className={nav}>
              Dashboard
            </NavLink>
            <NavLink to="/new" className={nav}>
              New review
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm text-slate-600">
            <span className="hidden sm:inline">{user.email}</span>
            <button onClick={signOut} className="text-indigo-600 hover:underline">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/signup" element={<AuthPage mode="signup" />} />
      <Route element={<Shell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/new" element={<NewReviewPage />} />
        <Route path="/reviews/:id" element={<ReviewDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
