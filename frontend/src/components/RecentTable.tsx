import { Link } from "react-router-dom";
import type { AnalysisSummary } from "../services/api";
import { RiskBadge, StatusPill, when } from "./ui";

export default function RecentTable({ rows, onDelete }: { rows: AnalysisSummary[]; onDelete?: (id: number) => void }) {
  if (!rows.length) return <p className="muted">No videos yet.</p>;
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr><th>Video</th><th>Status</th><th className="num">Compliance</th><th>Risk</th><th>Uploaded</th>{onDelete && <th />}</tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td><Link to={`/analyses/${r.id}`}>{r.original_filename}</Link></td>
              <td><StatusPill status={r.status} /></td>
              <td className="num">{r.ppe_compliance !== null ? `${r.ppe_compliance}%` : "-"}</td>
              <td>{r.status === "completed" ? <RiskBadge level={r.risk_level} /> : <span className="muted">-</span>}</td>
              <td>{when(r.created_at)}</td>
              {onDelete && (
                <td>
                  {(r.status === "completed" || r.status === "failed") && (
                    <button className="link-danger" onClick={() => onDelete(r.id)}>Delete</button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
