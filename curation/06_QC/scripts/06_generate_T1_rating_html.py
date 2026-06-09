#!/usr/bin/env python3
"""
Generate a self-contained HTML page for T1 QC ratings from slice PNGs.

Features:
- Scan an image directory for `sub-<ID>_ses-<ID>_<VIEW>.png` images
- Group images by (subject, session) for expected views (default: S1, S3, A2, A3)
- Produce an HTML with a simple UI to rate each view per (sub, ses)
- Export ratings to CSV client-side (no backend required)
- Optional portability: copy referenced images next to the HTML (assets/) and rewrite paths

Example:
  python /cbica/projects/grmpy/code/curation/06_QC/scripts/06_generate_T1_rating_html.py \
    --root /cbica/projects/grmpy/data/T1_QC/slices \
    --out /cbica/projects/grmpy/code/curation/06_QC/scripts/07_T1_QC_ratings.html \
    --portable \
    --allow-missing

"""

import argparse
import base64
import glob
import os
import re
import shutil
from typing import Dict, List, Tuple
import json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate T1 QC rating HTML from slice images"
    )
    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Directory containing PNG images (sub-*_ses-*_VIEW.png). "
            "Required unless --generate-from-nifti is used; in that case, "
            "defaults to --png-outdir."
        ),
    )
    parser.add_argument("--out", required=True, help="Output HTML file path")
    parser.add_argument(
        "--views",
        nargs="+",
        default=["S1", "S3", "A2", "A3"],
        help="List of expected views per row",
    )
    parser.add_argument(
        "--pattern",
        default="sub-*_ses-*_*.png",
        help="Glob pattern (relative to --root) for candidate images",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Include rows even if not all expected views are present",
    )
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Copy used images into assets/ next to HTML and rewrite paths",
    )
    parser.add_argument(
        "--embed-small",
        type=int,
        default=0,
        help=(
            "If >0, embed images smaller than this many KB as base64 in HTML. "
            "Larger images will be linked/copied as files."
        ),
    )
    return parser.parse_args()


FilenameRegex = re.compile(r"^(sub-[^_]+)_(ses-[^_]+)_([^.]+)\.png$")


def natural_sort_key(sub: str, ses: str) -> Tuple:
    m_sub = re.search(r"sub-(\d+)$", sub)
    m_ses = re.search(r"ses-(\d+)$", ses)
    return (
        int(m_sub.group(1)) if m_sub else sub,
        int(m_ses.group(1)) if m_ses else ses,
    )


def collect_rows(
    root: str, pattern: str, views: List[str], allow_missing: bool
) -> Tuple[List[Tuple[str, str]], Dict[Tuple[str, str], Dict[str, str]]]:
    pairs: Dict[Tuple[str, str], Dict[str, str]] = {}
    for path in glob.glob(os.path.join(root, pattern)):
        fn = os.path.basename(path)
        m = FilenameRegex.match(fn)
        if not m:
            continue
        sub, ses, view = m.groups()
        if view not in views:
            continue
        pairs.setdefault((sub, ses), {})[view] = path

    keys = sorted(pairs.keys(), key=lambda k: natural_sort_key(k[0], k[1]))
    if not allow_missing:
        keys = [k for k in keys if all(v in pairs[k] for v in views)]
    return keys, pairs


def ensure_portable_assets(
    keys: List[Tuple[str, str]],
    pairs: Dict[Tuple[str, str], Dict[str, str]],
    out_html: str,
    embed_small_kb: int,
) -> Tuple[Dict[Tuple[str, str], Dict[str, str]], List[str]]:
    """
    Prepare image references for portability:
    - Create assets/ next to HTML
    - Copy images there and rewrite paths relative to HTML
    - For small images (<= embed_small_kb), embed as data URIs
    Returns updated mapping and list of copied file paths
    """
    copied: List[str] = []
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(out_html)), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    updated: Dict[Tuple[str, str], Dict[str, str]] = {}
    for key in keys:
        updated[key] = {}
        for view, src in pairs[key].items():
            try:
                size_kb = os.path.getsize(src) / 1024.0
            except OSError:
                size_kb = float("inf")

            if embed_small_kb > 0 and size_kb <= embed_small_kb:
                try:
                    with open(src, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("ascii")
                    updated[key][view] = f"data:image/png;base64,{b64}"
                except Exception:
                    # Fallback to copying
                    dst = os.path.join(assets_dir, os.path.basename(src))
                    shutil.copy2(src, dst)
                    copied.append(dst)
                    updated[key][view] = os.path.relpath(dst, os.path.dirname(out_html))
            else:
                dst = os.path.join(assets_dir, os.path.basename(src))
                shutil.copy2(src, dst)
                copied.append(dst)
                updated[key][view] = os.path.relpath(dst, os.path.dirname(out_html))

    return updated, copied


def make_relative_refs(
    keys: List[Tuple[str, str]],
    pairs: Dict[Tuple[str, str], Dict[str, str]],
    out_html: str,
) -> Dict[Tuple[str, str], Dict[str, str]]:
    updated: Dict[Tuple[str, str], Dict[str, str]] = {}
    out_dir = os.path.dirname(os.path.abspath(out_html))
    for key in keys:
        updated[key] = {}
        for view, src in pairs[key].items():
            updated[key][view] = os.path.relpath(os.path.abspath(src), out_dir)
    return updated


def render_html(
    keys: List[Tuple[str, str]],
    pairs: Dict[Tuple[str, str], Dict[str, str]],
    views: List[str],
    out_path: str,
):
    # Minimal CSS + JS for table layout and CSV export
    css = """
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 16px; }
    h1 { font-size: 20px; margin: 0 0 12px 0; }
    .controls { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 8px; background: #fff; }
    .header { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
    .views { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    .view { display: flex; flex-direction: column; gap: 6px; }
    .view img { width: 100%; height: auto; display: block; border: 1px solid #eee; border-radius: 4px; }
    .rating { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
    .muted { color: #666; font-size: 12px; }
    .search { padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; min-width: 260px; }
    button { padding: 6px 10px; border: 1px solid #aaa; border-radius: 6px; background: #f7f7f7; cursor: pointer; }
    button.primary { background: #0b5; color: #fff; border-color: #0a4; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .initials { padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; width: 80px; }
    .consensus-panel { display: none; border: 1px solid #bbb; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: #fafafa; }
    .consensus-panel.active { display: block; }
    .consensus-panel .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
    .consensus-panel .row:last-child { margin-bottom: 0; }
    .consensus-panel label { font-size: 13px; font-weight: 600; min-width: 80px; }
    .view.discrepancy { background: #fff3e0; border: 2px solid #e8a735; border-radius: 6px; padding: 4px; }
    .view.agreed-lock select { opacity: 0.7; }
    .rater-context { font-size: 11px; color: #b45309; margin-top: 2px; }
    """

    # Data for client-side JS
    # Build rows: [{sub, ses, images: {view: src}}]
    data_rows = []
    for sub, ses in keys:
        images = {v: pairs[(sub, ses)].get(v, "") for v in views}
        data_rows.append(
            {
                "sub": sub,
                "ses": ses,
                "images": images,
            }
        )

    # Serialize minimal JSON safely
    json_data = json.dumps(data_rows)
    json_views = json.dumps(views)

    js = f"""
    const DATA = {json_data};
    const VIEWS = {json_views};
    let PREFILL = {{}}; // key: `${{sub}}|${{ses}}` -> {{ view: score }}
    let RATINGS = {{}}; // live user selections, same keying as PREFILL
    let RATER1 = {{}}, RATER2 = {{}};
    let AGREED = {{}};        // key -> {{ view: score }} for views where raters match
    let DISCREPANCIES = {{}}; // key -> {{ view: {{ r1: score, r2: score }} }}
    let CONSENSUS_RATINGS = {{}};
    let consensusMode = false;

    const makeKey = (sub, ses) => sub + '|' + ses;

    function escapeCsv(val) {{
      if (val == null) return '';
      const s = String(val);
      if (s.includes('"') || s.includes(',') || s.includes('\\n')) {{
        return '"' + s.replace(/"/g, '""') + '"';
      }}
      return s;
    }}

    function toCSV() {{
      const headers = ['subid','sesid', ...VIEWS.map(v => v + '_score')];
      const lines = [headers.join(',')];
      for (const row of DATA) {{
        const key = makeKey(row.sub, row.ses);
        const scores = VIEWS.map(v => {{
          if (RATINGS[key] && RATINGS[key][v] !== undefined) return RATINGS[key][v];
          if (PREFILL[key] && PREFILL[key][v] !== undefined) return PREFILL[key][v];
          return '';
        }});
        const line = [row.sub, row.ses, ...scores].map(escapeCsv).join(',');
        lines.push(line);
      }}
      return lines.join('\\n');
    }}

    function getInitials() {{
      const el = document.getElementById('initials');
      return el ? el.value.trim() : '';
    }}

    function makeFilename(base, ext) {{
      const ini = getInitials();
      return ini ? `${{base}}_${{ini}}.${{ext}}` : `${{base}}.${{ext}}`;
    }}

    function triggerDownload(csv, filename) {{
      const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

    function downloadCSV() {{
      triggerDownload(toCSV(), makeFilename('T1-ratings', 'csv'));
    }}

    function parseCSV(text) {{
      const rows = [];
      let i = 0, field = '', inQuotes = false, row = [];
      while (i < text.length) {{
        const c = text[i++];
        if (inQuotes) {{
          if (c === '"') {{
            if (text[i] === '"') {{ field += '"'; i++; }} else {{ inQuotes = false; }}
          }} else {{
            field += c;
          }}
        }} else {{
          if (c === '"') {{ inQuotes = true; }}
          else if (c === ',') {{ row.push(field); field=''; }}
          else if (c === '\\n' || c === '\\r') {{
            if (c === '\\r' && text[i] === '\\n') i++;
            row.push(field); rows.push(row); row = []; field='';
          }} else {{ field += c; }}
        }}
      }}
      if (field.length || row.length) {{ row.push(field); rows.push(row); }}
      return rows.filter(r => r.length && r.some(x => x !== ''));
    }}

    function buildPrefillFromCSV(rows) {{
      if (!rows || rows.length < 2) return {{}};
      const header = rows[0];
      const subIdx = header.indexOf('subid');
      const sesIdx = header.indexOf('sesid');
      const viewIdx = Object.fromEntries(VIEWS.map(v => [v, header.indexOf(v + '_score')]));
      const map = {{}};
      for (let r = 1; r < rows.length; r++) {{
        const row = rows[r];
        const sub = row[subIdx];
        const ses = row[sesIdx];
        if (!sub || !ses) continue;
        const key = `${{sub}}|${{ses}}`;
        map[key] = map[key] || {{}};
        for (const v of VIEWS) {{
          const idx = viewIdx[v];
          if (idx >= 0 && row[idx] !== undefined && row[idx] !== '') {{
            map[key][v] = String(row[idx]);
          }}
        }}
      }}
      return map;
    }}

    function applyPrefill(prefill) {{
      const cards = document.querySelectorAll('[data-card]');
      let applied = 0;
      for (const card of cards) {{
        const sub = card.getAttribute('data-sub');
        const ses = card.getAttribute('data-ses');
        const key = `${{sub}}|${{ses}}`;
        const views = prefill[key];
        if (!views) continue;
        for (const v of VIEWS) {{
          const val = views[v];
          if (val === undefined) continue;
          const sel = card.querySelector(`[data-score="${{v}}"]`);
          if (sel) {{ sel.value = val; applied++; }}
        }}
      }}
      return applied;
    }}

    function onCsvSelected(file) {{
      const reader = new FileReader();
      reader.onload = (e) => {{
        const text = e.target.result;
        const rows = parseCSV(text);
        PREFILL = buildPrefillFromCSV(rows);
        const n = applyPrefill(PREFILL);
        const msg = document.getElementById('resumeMsg');
        if (msg) msg.textContent = `Applied ${{n}} ratings from CSV`;
      }};
      reader.readAsText(file);
    }}

    function readFileAsText(file) {{
      return new Promise((resolve, reject) => {{
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(file);
      }});
    }}

    function toggleConsensusMode() {{
      const cb = document.getElementById('consensusToggle');
      consensusMode = cb.checked;
      document.getElementById('consensusPanel').classList.toggle('active', consensusMode);
      document.getElementById('individualControls').style.display = consensusMode ? 'none' : '';
      if (!consensusMode) {{
        RATER1 = {{}}; RATER2 = {{}}; AGREED = {{}}; DISCREPANCIES = {{}}; CONSENSUS_RATINGS = {{}};
        document.getElementById('consensusMsg').textContent = '';
        render(document.getElementById('search').value);
      }}
    }}

    async function compareRaters() {{
      const f1 = document.getElementById('rater1Upload').files[0];
      const f2 = document.getElementById('rater2Upload').files[0];
      if (!f1 || !f2) {{
        document.getElementById('consensusMsg').textContent = 'Please select both Rater 1 and Rater 2 CSV files.';
        return;
      }}
      const [text1, text2] = await Promise.all([readFileAsText(f1), readFileAsText(f2)]);
      RATER1 = buildPrefillFromCSV(parseCSV(text1));
      RATER2 = buildPrefillFromCSV(parseCSV(text2));
      AGREED = {{}};
      DISCREPANCIES = {{}};
      CONSENSUS_RATINGS = {{}};
      let agreeCount = 0, discrepCount = 0, totalSubs = 0;
      for (const row of DATA) {{
        const key = makeKey(row.sub, row.ses);
        const r1 = RATER1[key] || {{}};
        const r2 = RATER2[key] || {{}};
        let hasDiscrep = false;
        for (const v of VIEWS) {{
          const v1 = r1[v] !== undefined ? String(r1[v]) : '';
          const v2 = r2[v] !== undefined ? String(r2[v]) : '';
          if (v1 === v2 && v1 !== '') {{
            AGREED[key] = AGREED[key] || {{}};
            AGREED[key][v] = v1;
          }} else {{
            DISCREPANCIES[key] = DISCREPANCIES[key] || {{}};
            DISCREPANCIES[key][v] = {{ r1: v1, r2: v2 }};
            hasDiscrep = true;
          }}
        }}
        totalSubs++;
        if (hasDiscrep) discrepCount++; else agreeCount++;
      }}
      document.getElementById('consensusMsg').textContent =
        `${{agreeCount}} of ${{totalSubs}} subjects fully agree; ${{discrepCount}} subjects have discrepancies`;
      render(document.getElementById('search').value);
    }}

    function toConsensusCSV() {{
      const headers = ['subid','sesid', ...VIEWS.map(v => v + '_score'), 'average_rating', 'classification'];
      const lines = [headers.join(',')];
      for (const row of DATA) {{
        const key = makeKey(row.sub, row.ses);
        const scores = VIEWS.map(v => {{
          if (AGREED[key] && AGREED[key][v] !== undefined) return AGREED[key][v];
          if (CONSENSUS_RATINGS[key] && CONSENSUS_RATINGS[key][v] !== undefined) return CONSENSUS_RATINGS[key][v];
          return '';
        }});
        const numericScores = scores.filter(s => s !== '').map(Number);
        let avg = '', classification = '';
        if (numericScores.length === VIEWS.length) {{
          avg = numericScores.reduce((a, b) => a + b, 0) / numericScores.length;
          if (avg === 0) classification = 'Fail';
          else if (avg === 1) classification = 'Pass';
          else classification = 'Artifact';
          avg = String(avg);
        }}
        const line = [row.sub, row.ses, ...scores, avg, classification].map(escapeCsv).join(',');
        lines.push(line);
      }}
      return lines.join('\\n');
    }}

    function downloadConsensusCSV() {{
      triggerDownload(toConsensusCSV(), makeFilename('T1-consensus', 'csv'));
    }}

    function render(filter='') {{
      const root = document.getElementById('root');
      root.innerHTML = '';
      const q = filter.trim().toLowerCase();
      let rows = DATA.filter(r => (r.sub + ' ' + r.ses).toLowerCase().includes(q));
      const inConsensus = consensusMode && Object.keys(DISCREPANCIES).length > 0;
      if (inConsensus) {{
        rows = rows.filter(r => DISCREPANCIES[makeKey(r.sub, r.ses)]);
      }}
      for (const row of rows) {{
        const key = makeKey(row.sub, row.ses);
        const card = document.createElement('div');
        card.className = 'card';
        card.setAttribute('data-card', '');
        card.setAttribute('data-sub', row.sub);
        card.setAttribute('data-ses', row.ses);

        const header = document.createElement('div');
        header.className = 'header';
        const title = document.createElement('div');
        title.innerHTML = `<strong>${{row.sub}}</strong> &nbsp; <span class="muted">${{row.ses}}</span>`;
        const hint = document.createElement('div');
        hint.className = 'muted';
        hint.textContent = inConsensus ? 'Rate discrepancies (highlighted)' : 'Rate each view: 0=Fail, 1=Pass';
        header.appendChild(title);
        header.appendChild(hint);
        card.appendChild(header);

        const views = document.createElement('div');
        views.className = 'views';
        for (const v of VIEWS) {{
          const isDiscrep = inConsensus && DISCREPANCIES[key] && DISCREPANCIES[key][v];
          const isAgreed = inConsensus && AGREED[key] && AGREED[key][v] !== undefined;
          const box = document.createElement('div');
          box.className = 'view' + (isDiscrep ? ' discrepancy' : '') + (isAgreed ? ' agreed-lock' : '');
          const img = document.createElement('img');
          const src = row.images[v] || '';
          if (src) img.src = src;
          img.alt = `${{row.sub}} ${{row.ses}} ${{v}}`;
          const label = document.createElement('label');
          label.textContent = v;
          const select = document.createElement('select');
          select.setAttribute('data-score', v);
          for (const [val, name] of [['', ''], ['0','Fail'], ['1','Pass']]) {{
            const opt = document.createElement('option');
            opt.value = val; opt.textContent = name;
            select.appendChild(opt);
          }}
          if (inConsensus) {{
            if (isAgreed) {{
              select.value = AGREED[key][v];
              select.disabled = true;
            }} else if (isDiscrep) {{
              let initVal = '';
              if (CONSENSUS_RATINGS[key] && CONSENSUS_RATINGS[key][v] !== undefined) {{
                initVal = CONSENSUS_RATINGS[key][v];
              }}
              select.value = initVal;
              select.addEventListener('change', () => {{
                CONSENSUS_RATINGS[key] = CONSENSUS_RATINGS[key] || {{}};
                CONSENSUS_RATINGS[key][v] = select.value;
              }});
            }}
          }} else {{
            let initVal = '';
            if (RATINGS[key] && RATINGS[key][v] !== undefined) {{ initVal = RATINGS[key][v]; }}
            else if (PREFILL[key] && PREFILL[key][v] !== undefined) {{ initVal = PREFILL[key][v]; }}
            select.value = initVal;
            select.addEventListener('change', () => {{
              RATINGS[key] = RATINGS[key] || {{}};
              RATINGS[key][v] = select.value;
            }});
          }}
          const rating = document.createElement('div');
          rating.className = 'rating';
          rating.appendChild(label);
          rating.appendChild(select);
          box.appendChild(img);
          box.appendChild(rating);
          if (isDiscrep) {{
            const ctx = document.createElement('div');
            ctx.className = 'rater-context';
            const d = DISCREPANCIES[key][v];
            const r1Label = d.r1 === '' ? '(blank)' : (d.r1 === '0' ? 'Fail' : 'Pass');
            const r2Label = d.r2 === '' ? '(blank)' : (d.r2 === '0' ? 'Fail' : 'Pass');
            ctx.textContent = `R1: ${{r1Label}}  |  R2: ${{r2Label}}`;
            box.appendChild(ctx);
          }}
          views.appendChild(box);
        }}
        card.appendChild(views);
        root.appendChild(card);
      }}
      document.getElementById('count').textContent = rows.length + ' rows';
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      const search = document.getElementById('search');
      search.addEventListener('input', () => render(search.value));
      const csv = document.getElementById('csvUpload');
      csv.addEventListener('change', () => {{ if (csv.files && csv.files[0]) onCsvSelected(csv.files[0]); }});
      render('');
    }});
    """

    html_doc = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>T1 QC Ratings</title>
  <style>{css}</style>
  <script>{js}</script>
</head>
<body>
  <h1>T1 QC Ratings</h1>
  <div class="controls">
    <input id="search" class="search" type="search" placeholder="Filter by subject/session (e.g., sub-123 ses-1)" />
    <input id="initials" class="initials" type="text" placeholder="Initials" maxlength="10" />
    <span id="individualControls">
      <button class="primary" onclick="downloadCSV()">Download CSV</button>
      <input id="csvUpload" type="file" accept=".csv,text/csv" />
      <span id="resumeMsg" class="muted"></span>
    </span>
    <label style="margin-left:12px;font-size:13px;cursor:pointer;">
      <input id="consensusToggle" type="checkbox" onchange="toggleConsensusMode()" /> Consensus Mode
    </label>
    <span id="count" class="muted"></span>
  </div>
  <div id="consensusPanel" class="consensus-panel">
    <div class="row">
      <label>Rater 1 CSV:</label>
      <input id="rater1Upload" type="file" accept=".csv,text/csv" />
      <label>Rater 2 CSV:</label>
      <input id="rater2Upload" type="file" accept=".csv,text/csv" />
      <button onclick="compareRaters()">Compare</button>
    </div>
    <div class="row">
      <span id="consensusMsg" class="muted"></span>
      <button class="primary" onclick="downloadConsensusCSV()">Download Consensus CSV</button>
    </div>
  </div>
  <div id="root" class="grid"></div>
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)


def main() -> None:
    args = parse_args()

    keys, pairs = collect_rows(args.root, args.pattern, args.views, args.allow_missing)

    if not keys:
        raise SystemExit(
            "No rows found. Check --root and --pattern, and ensure filenames match 'sub-*_ses-*_VIEW.png'."
        )

    # Rewrite image references according to portability settings
    if args.portable:
        pairs, copied = ensure_portable_assets(keys, pairs, args.out, args.embed_small)
        print(
            f"Prepared portable assets in 'assets/' next to HTML. Files copied: {len(copied)}"
        )
    else:
        pairs = make_relative_refs(keys, pairs, args.out)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    render_html(keys, pairs, args.views, args.out)
    print(f"Wrote HTML: {args.out}")
    print(f"Rows: {len(keys)} | Views per row: {len(args.views)}")
    if args.portable:
        print(
            "Note: For sharing, distribute the HTML and the 'assets/' folder together."
        )
    else:
        print(
            "Note: HTML references images by relative paths; receivers need the same directory structure."
        )


if __name__ == "__main__":
    main()
