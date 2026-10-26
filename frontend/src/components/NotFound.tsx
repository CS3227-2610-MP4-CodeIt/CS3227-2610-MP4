import { Link } from "react-router";

export function NotFound() {
  return (
    <div className="card">
      <p className="mb-2 font-medium">Not found</p>
      <p className="text-sm text-slate-600">
        This page does not exist or you cannot see it. <Link to="/" className="link">Go home</Link>
      </p>
    </div>
  );
}
