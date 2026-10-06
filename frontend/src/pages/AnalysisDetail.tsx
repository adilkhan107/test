import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ErrorNote, HazardBar, Loading, mmss, RiskBadge, StatusPill, TYPE_LABEL, when } from "../components/ui";
import { API_URL, api, type AnalysisDetail as Detail, type RiskReport } from "../services/api";

const PPE_ROWS = [
  { label: "Hardhat", ok: "hardhat", miss: "no_hardhat" },
  { label: "Safety vest", ok: "vest", miss: "no_vest" },
  { label: "Mask", ok: "mask", miss: "no_mask" },
];

export default function AnalysisDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [a, setA] = useState<Detail | null>(null);
  const [risk, setRisk] = useState<RiskReport | null>(null);
  const [error, setError] = useState("");

  // Poll while the job is running
  useEffect(() => {
    const n = Number(id);
    let timer: number | undefined;
    let stop = false;
    async function tick() {
      try {
        const d = await api.get(n);
        if (stop) return;
        setA(d);
        if (d.status === "queued" || d.status === "processing") timer = window.setTimeout(tick, 1500);
        else if (d.status === "completed") api.risk(n).then((r) => !stop && setRisk(r)).catch(() => {});
      } catch (e) {
        if (!stop) setError((e as Error).message);
      }
    }
    tick();
    return () => { stop = true; window.clearTimeout(timer); };
  }, [id]);

  async function remove() {
    if (!a || !confirm("Delete this analysis and its snapshots?")) return;
    try {
      await api.remove(a.id);
      nav("/analyses");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (error) return <ErrorNote message={error} />;
  if (!a) return <Loading />;

  const running = a.status === "queued" || a.status === "processing";

  return (
    <>
      <p className="crumb"><Link to="/analyses">History</Link></p>
      <div className="title-row">
        <h1>{a.original_filename}</h1>
        <StatusPill status={a.status} />
        {a.status === "completed" && <RiskBadge level={a.risk_level} />}
      </div>
      <p className="muted">Uploaded {when(a.created_at)}{a.duration_seconds !== null && `, ${mmss(a.duration_seconds)} long`}</p>

      {running && (
        <section>
          <p>{a.status === "queued" ? "Waiting for a free analysis slot." : `Analyzing frames: ${a.progress}%`}</p>
          <HazardBar value={a.progress} label="Analysis progress" />
          <p className="muted">You can leave this page. The result will be in History when it is done.</p>
        </section>
      )}

      {a.status === "failed" && <ErrorNote message={a.error ?? "The analysis failed."} />}

      {a.status === "completed" && (
        <>
          <section className="hero">
            <div>
              <p className="muted">PPE compliance</p>
              <p className="big">{a.ppe_compliance !== null ? `${a.ppe_compliance}%` : "-"}</p>
            </div>
            <div className="hero-bar">
              <HazardBar value={a.ppe_compliance ?? 0} label="PPE compliance" />
              <p className="facts">
                Up to {a.peak_people} workers in view at once, {a.avg_people} on average. {a.frames_sampled} frames
                checked, workers visible in {a.frames_with_people}.
              </p>
            </div>
          </section>

          {a.ppe_compliance === null && (
            <p className="lede">No workers were detected, so compliance could not be scored. Try a clip where people are clearly visible.</p>
          )}

          <div className="cols">
            <section>
              <h2>PPE detections</h2>
              <table className="plain">
                <thead><tr><th>Item</th><th className="num">Worn</th><th className="num">Missing</th></tr></thead>
                <tbody>
                  {PPE_ROWS.map((r) => (
                    <tr key={r.label}>
                      <td>{r.label}</td>
                      <td className="num">{a.detections[r.ok] ?? 0}</td>
                      <td className={`num${(a.detections[r.miss] ?? 0) > 0 ? " bad" : ""}`}>{a.detections[r.miss] ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="muted small">Counts add up across checked frames, so one worker seen in many frames is counted many times.</p>
            </section>

            {risk && (
              <section>
                <h2>What to do</h2>
                <ul className="plainlist">{risk.recommendations.map((r) => <li key={r}>{r}</li>)}</ul>
                <details>
                  <summary>Why this risk level</summary>
                  <ul className="plainlist">{risk.factors.map((f) => <li key={f}>{f}</li>)}</ul>
                  <p className="muted small">Risk score {risk.risk_score} of 100.</p>
                </details>
              </section>
            )}
          </div>

          {a.snapshots.length > 0 && (
            <section>
              <h2>Worst moments</h2>
              <div className="snaps">
                {a.snapshots.map((s) => (
                  <figure key={s.url}>
                    <a href={`${API_URL}${s.url}`} target="_blank" rel="noreferrer">
                      <img src={`${API_URL}${s.url}`} alt={`Frame at ${mmss(s.timestamp_seconds)} with ${s.violations} violations`} loading="lazy" />
                    </a>
                    <figcaption>{mmss(s.timestamp_seconds)}, {s.violations} violation{s.violations > 1 ? "s" : ""}</figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}

          <section>
            <h2>Violation log</h2>
            {a.incidents.length === 0 ? <p className="muted">No violations found.</p> : (
              <div className="scroll tall">
                <table>
                  <thead><tr><th>Time</th><th>Violation</th><th className="num">Workers</th><th className="num">In frame</th></tr></thead>
                  <tbody>
                    {a.incidents.map((i) => (
                      <tr key={i.id}>
                        <td>{mmss(i.timestamp_seconds)}</td>
                        <td>{TYPE_LABEL[i.type] ?? i.type}</td>
                        <td className="num">{i.count}</td>
                        <td className="num">{i.people_in_frame}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {!running && <button className="link-danger" onClick={remove}>Delete this analysis</button>}
    </>
  );
}
