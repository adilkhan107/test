import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import RecentTable from "../components/RecentTable";
import TrendChart from "../components/TrendChart";
import { ErrorNote, HazardBar, Loading, TYPE_LABEL } from "../components/ui";
import { api, type Dashboard as Data } from "../services/api";

const RISKS = ["low", "medium", "high", "critical"] as const;

export default function Dashboard() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;
  if (!data) return <Loading />;

  if (data.total_analyses === 0) {
    return (
      <>
        <h1>Dashboard</h1>
        <p className="lede">Nothing analyzed yet. <Link to="/analyze">Upload your first site video</Link> to see PPE compliance here.</p>
      </>
    );
  }

  const riskTotal = RISKS.reduce((n, r) => n + (data.risk_distribution[r] ?? 0), 0);

  return (
    <>
      <h1>Dashboard</h1>

      <section className="hero">
        <div>
          <p className="muted">Average PPE compliance</p>
          <p className="big">{data.avg_compliance !== null ? `${data.avg_compliance}%` : "-"}</p>
        </div>
        <div className="hero-bar">
          <HazardBar value={data.avg_compliance ?? 0} label="Average PPE compliance" />
          <p className="facts">
            {data.completed} analyzed, {data.total_incidents} violations logged
            {data.in_progress > 0 && `, ${data.in_progress} running`}
            {data.failed > 0 && `, ${data.failed} failed`}
          </p>
        </div>
      </section>

      <div className="cols">
        <section>
          <h2>Compliance by video</h2>
          {data.trend.length ? <TrendChart data={data.trend} /> : <p className="muted">No completed videos yet.</p>}
        </section>

        <section>
          <h2>Risk levels</h2>
          {riskTotal === 0 ? <p className="muted">No scored videos yet.</p> : (
            <>
              <div className="stack" role="img" aria-label="Risk level distribution">
                {RISKS.map((r) => (data.risk_distribution[r] ?? 0) > 0 && (
                  <span key={r} className={`seg risk-${r}`} style={{ flex: data.risk_distribution[r] }} />
                ))}
              </div>
              <ul className="legend">
                {RISKS.map((r) => (
                  <li key={r}><span className={`dot risk-${r}`} />{r}: {data.risk_distribution[r] ?? 0}</li>
                ))}
              </ul>
            </>
          )}
          <h2>Violations by type</h2>
          {Object.keys(data.incidents_by_type).length === 0 ? <p className="muted">None recorded.</p> : (
            <table className="plain"><tbody>
              {Object.entries(data.incidents_by_type).map(([k, v]) => (
                <tr key={k}><td>{TYPE_LABEL[k] ?? k}</td><td className="num">{v}</td></tr>
              ))}
            </tbody></table>
          )}
        </section>
      </div>

      <h2>Recent videos</h2>
      <RecentTable rows={data.recent} />
    </>
  );
}
