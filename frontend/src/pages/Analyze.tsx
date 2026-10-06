import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ErrorNote } from "../components/ui";
import { api } from "../services/api";

const EXT = [".mp4", ".mov", ".avi", ".mkv", ".webm"];
const mb = (n: number) => `${(n / 1024 / 1024).toFixed(1)} MB`;

export default function Analyze() {
  const nav = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function pick(f: File | undefined) {
    if (!f) return;
    if (!EXT.some((e) => f.name.toLowerCase().endsWith(e))) {
      setError(`Choose a video file (${EXT.join(", ")}).`);
      return;
    }
    setError("");
    setFile(f);
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const { id } = await api.upload(file);
      nav(`/analyses/${id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  return (
    <>
      <h1>New analysis</h1>
      <p className="lede">Upload a clip from the site. Every second of video is checked for hardhats, vests and masks.</p>

      <div
        className={`drop${drag ? " over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
      >
        <input ref={input} type="file" accept="video/*" hidden onChange={(e) => pick(e.target.files?.[0])} />
        {file ? (
          <p><strong>{file.name}</strong><br /><span className="muted">{mb(file.size)}</span></p>
        ) : (
          <p>Drop a video here</p>
        )}
        <button type="button" className="ghost" onClick={() => input.current?.click()} disabled={busy}>
          {file ? "Choose another video" : "Choose a video"}
        </button>
      </div>

      {error && <ErrorNote message={error} />}

      <button className="primary" onClick={submit} disabled={!file || busy}>
        {busy ? "Uploading..." : "Start analysis"}
      </button>
    </>
  );
}
