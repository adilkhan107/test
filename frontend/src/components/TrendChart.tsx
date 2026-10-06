import { Link } from "react-router-dom";
import type { Dashboard } from "../services/api";

/** Compliance of the latest analyses, oldest to newest. */
export default function TrendChart({ data }: { data: Dashboard["trend"] }) {
  const W = 640, H = 170, P = { l: 34, r: 10, t: 10, b: 20 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const x = (i: number) => P.l + (data.length === 1 ? iw / 2 : (i / (data.length - 1)) * iw);
  const y = (v: number) => P.t + ih - (v / 100) * ih;
  const line = data.map((d, i) => `${i ? "L" : "M"}${x(i)},${y(d.compliance)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="trend" role="img" aria-label="PPE compliance across recent analyses">
      {[0, 50, 100].map((g) => (
        <g key={g}>
          <line x1={P.l} x2={W - P.r} y1={y(g)} y2={y(g)} className="grid" />
          <text x={P.l - 6} y={y(g) + 4} textAnchor="end" className="axis">{g}%</text>
        </g>
      ))}
      {data.length > 1 && <path d={line} className="trend-line" />}
      {data.map((d, i) => (
        <Link key={d.id} to={`/analyses/${d.id}`}>
          <circle cx={x(i)} cy={y(d.compliance)} r={5} className="trend-dot">
            <title>{`${d.label}: ${d.compliance}%`}</title>
          </circle>
        </Link>
      ))}
    </svg>
  );
}
