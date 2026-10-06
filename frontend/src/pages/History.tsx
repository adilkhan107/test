import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import RecentTable from "../components/RecentTable";
import { ErrorNote, Loading } from "../components/ui";
import { api, type AnalysisSummary } from "../services/api";

export default function History() {
  const [rows, setRows] = useState<AnalysisSummary[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api.list().then((r) => setRows(r.items)).catch((e: Error) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  async function remove(id: number) {
    if (!confirm("Delete this analysis and its snapshots? This cannot be undone.")) return;
    try {
      await api.remove(id);
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <h1>History</h1>
      {error && <ErrorNote message={error} />}
      {!rows ? <Loading /> : rows.length === 0 ? (
        <p className="lede">No analyses yet. <Link to="/analyze">Upload a video</Link> to start.</p>
      ) : (
        <RecentTable rows={rows} onDelete={remove} />
      )}
    </>
  );
}
