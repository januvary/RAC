#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render an AggregateStats into a self-contained HTML dashboard.

Output is a single static file (no server, no external assets): the merged
data is baked in as HTML, styled with inline CSS, with a tiny inline JS hook
for the medications search filter. Open it directly in any browser.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from src.constants import TIPO_HEX, TIPO_LABELS
from src.sync.merger import AggregateStats

_CSS = """
  :root {
    --bg: #18181B;
    --card: #27272A;
    --border: #3F3F46;
    --text: #F4F4F5;
    --muted: #A1A1AA;
    --alt: #2D2D31;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Geist", -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 32px;
    max-width: 960px;
  }
  h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 26px; }
  .row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 22px; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    min-width: 124px;
  }
  .card .v { font-size: 24px; font-weight: 700; }
  .card .l {
    font-size: 11px; font-weight: 600; color: var(--muted);
    margin-top: 2px; text-transform: uppercase; letter-spacing: .04em;
  }
  .section {
    font-size: 12px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: .05em; margin: 6px 0 10px;
  }
  .wrap {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; margin-bottom: 24px; overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 9px 14px; border-bottom: 1px solid var(--border); }
  th {
    color: var(--muted); font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: .04em;
  }
  td.num, th.num { text-align: right; }
  tbody tr:nth-child(even) { background: var(--alt); }
  .pad { padding: 10px 14px 0; }
  input {
    width: 100%; padding: 9px 12px;
    border-radius: 6px; border: 1px solid var(--border);
    background: var(--bg); color: var(--text); font-size: 13px;
  }
  .empty td { text-align: center; color: var(--muted); }
  .lock { max-width: 340px; margin: 80px auto; text-align: center; }
  .lock input { text-align: center; margin-bottom: 12px; }
  .lock button {
    padding: 9px 24px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--card); color: var(--text); font-size: 14px; cursor: pointer;
  }
  .lock .err { color: #F87171; font-size: 13px; margin-top: 10px; min-height: 18px; }
"""

_PAGE = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gestao - RAC</title>
<style>{_CSS}</style>
</head>
<body>
__BODY__
<script>
var s = document.getElementById('meds-search');
if (s) s.addEventListener('input', function () {{
  var q = s.value.toLowerCase();
  document.querySelectorAll('#meds-table tbody tr').forEach(function (tr) {{
    tr.style.display = tr.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
  }});
}});
</script>
</body>
</html>"""


def _card(value: str, label: str, accent: str | None = None) -> str:
    color = f" color: {escape(accent)};" if accent else ""
    return (
        f'<div class="card">'
        f'<div class="v" style="{color}">{escape(value)}</div>'
        f'<div class="l">{escape(label)}</div>'
        f"</div>"
    )


def _format_synced(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return iso


def _usafa_table(agg: AggregateStats) -> str:
    head = (
        '<tr><th>USAFA</th><th class="num">Registros</th>'
        '<th class="num">Pacientes</th><th class="num">Malotes</th>'
        '<th class="num">Sincronizado</th></tr>'
    )
    if not agg.usafas:
        body = '<tr class="empty"><td colspan="5">Sem dados</td></tr>'
    else:
        rows = []
        for u in agg.usafas:
            rows.append(
                f"<tr><td>{escape(u.usafa_name)}</td>"
                f'<td class="num">{u.registros}</td>'
                f'<td class="num">{u.pacientes}</td>'
                f'<td class="num">{u.malotes}</td>'
                f'<td class="num">{escape(_format_synced(u.exported_at))}</td></tr>'
            )
        body = "".join(rows)
    return f"<table><thead>{head}</thead><tbody>{body}</tbody></table>"


def _meds_table(agg: AggregateStats) -> str:
    head = (
        '<tr><th>Medicamento</th><th class="num">Registros</th>'
        '<th class="num">%</th></tr>'
    )
    items: list[dict[str, Any]] = agg.top_items
    total = sum(i["registros"] for i in items) or 1
    if not items:
        body = '<tr class="empty"><td colspan="3">Sem dados</td></tr>'
    else:
        rows = []
        for item in items:
            pct = item["registros"] / total * 100
            rows.append(
                f"<tr><td>{escape(str(item['medicamento']))}</td>"
                f'<td class="num">{item["registros"]}</td>'
                f'<td class="num">{pct:.1f}%</td></tr>'
            )
        body = "".join(rows)
    return f'<table id="meds-table"><thead>{head}</thead><tbody>{body}</tbody></table>'


def render_html(agg: AggregateStats) -> str:
    parts: list[str] = []
    parts.append("<h1>Gestao</h1>")
    parts.append(
        f'<div class="sub">Gerado em '
        f'{escape(datetime.now().strftime("%d/%m/%Y %H:%M"))} '
        f"· {agg.total_usafas} USAFA(s)</div>"
    )

    parts.append('<div class="row">')
    parts.append(_card(str(agg.total_usafas), "USAFAs"))
    parts.append(_card(str(agg.total_registros), "Registros"))
    parts.append(_card(str(agg.total_pacientes), "Pacientes"))
    parts.append("</div>")

    parts.append('<div class="section">Por tipo</div>')
    parts.append('<div class="row">')
    for tipo in TIPO_LABELS:
        parts.append(
            _card(
                str(agg.by_tipo.get(tipo, 0)),
                TIPO_LABELS[tipo],
                accent=TIPO_HEX.get(tipo),
            )
        )
    parts.append("</div>")

    parts.append('<div class="section">Por USAFA</div>')
    parts.append(f'<div class="wrap">{_usafa_table(agg)}</div>')

    parts.append('<div class="section">Medicamentos</div>')
    parts.append(
        f'<div class="wrap"><div class="pad">'
        f'<input id="meds-search" placeholder="Buscar medicamento...">'
        f"</div>{_meds_table(agg)}</div>"
    )

    return _PAGE.replace("__BODY__", "\n".join(parts))


def render_locked_html(enc_blob: dict) -> str:
    import json

    meta = {"labels": dict(TIPO_LABELS), "hex": dict(TIPO_HEX)}
    blob_json = json.dumps(enc_blob)
    meta_json = json.dumps(meta)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gestao - RAC</title>
<style>{_CSS}</style>
</head>
<body>
<div class="lock" id="lock">
  <h1>Gestao</h1>
  <p class="sub">Digite a senha para visualizar o painel.</p>
  <input id="pw" type="password" placeholder="Senha" autofocus>
  <br>
  <button id="go">Entrar</button>
  <div class="err" id="err"></div>
</div>
<div id="dash" hidden></div>

<script>
window.RAC_ENC = {blob_json};
window.RAC_META = {meta_json};

function b64(s) {{
  return Uint8Array.from(atob(s), function (c) {{ return c.charCodeAt(0); }});
}}
function esc(s) {{
  var d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
}}
function card(v, label, accent) {{
  var c = accent ? ' style="color:' + esc(accent) + '"' : '';
  return '<div class="card"><div class="v"' + c + '>' + esc(v) + '</div>'
    + '<div class="l">' + esc(label) + '</div></div>';
}}
function fmtSynced(iso) {{
  try {{
    var d = new Date(iso);
    if (isNaN(d)) return iso;
    var p = function (n) {{ return String(n).padStart(2, '0'); }};
    return p(d.getDate()) + '/' + p(d.getMonth()+1) + '/' + d.getFullYear()
      + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }} catch (e) {{ return iso; }}
}}
function render(d) {{
  var m = window.RAC_META;
  var h = '<h1>Gestao</h1>';
  h += '<div class="sub">' + d.total_usafas + ' USAFA(s)</div>';
  h += '<div class="row">';
  h += card(d.total_usafas, 'USAFAs');
  h += card(d.total_registros, 'Registros');
  h += card(d.total_pacientes, 'Pacientes');
  h += '</div>';
  h += '<div class="section">Por tipo</div><div class="row">';
  Object.keys(m.labels).forEach(function (tipo) {{
    h += card(d.by_tipo[tipo] || 0, m.labels[tipo], m.hex[tipo]);
  }});
  h += '</div>';
  h += '<div class="section">Por USAFA</div><div class="wrap"><table><thead>';
  h += '<tr><th>USAFA</th><th class="num">Registros</th><th class="num">Pacientes</th>'
    + '<th class="num">Malotes</th><th class="num">Sincronizado</th></tr></thead><tbody>';
  if (!d.usafas.length) {{
    h += '<tr class="empty"><td colspan="5">Sem dados</td></tr>';
  }} else {{
    d.usafas.forEach(function (u) {{
      h += '<tr><td>' + esc(u.usafa_name) + '</td>'
        + '<td class="num">' + u.registros + '</td>'
        + '<td class="num">' + u.pacientes + '</td>'
        + '<td class="num">' + u.malotes + '</td>'
        + '<td class="num">' + esc(fmtSynced(u.exported_at)) + '</td></tr>';
    }});
  }}
  h += '</tbody></table></div>';
  h += '<div class="section">Medicamentos</div>';
  h += '<div class="wrap"><div class="pad">'
    + '<input id="meds-search" placeholder="Buscar medicamento..."></div>';
  h += '<table id="meds-table"><thead>';
  h += '<tr><th>Medicamento</th><th class="num">Registros</th><th class="num">%</th></tr>';
  h += '</thead><tbody>';
  var total = d.top_items.reduce(function (a, i) {{ return a + i.registros; }}, 0) || 1;
  if (!d.top_items.length) {{
    h += '<tr class="empty"><td colspan="3">Sem dados</td></tr>';
  }} else {{
    d.top_items.forEach(function (it) {{
      h += '<tr><td>' + esc(it.medicamento) + '</td>'
        + '<td class="num">' + it.registros + '</td>'
        + '<td class="num">' + (it.registros / total * 100).toFixed(1) + '%</td></tr>';
    }});
  }}
  h += '</tbody></table></div>';
  document.getElementById('dash').innerHTML = h;
  var s = document.getElementById('meds-search');
  if (s) s.addEventListener('input', function () {{
    var q = s.value.toLowerCase();
    document.querySelectorAll('#meds-table tbody tr').forEach(function (tr) {{
      tr.style.display = tr.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
    }});
  }});
}}
async function unlock(pw) {{
  var enc = window.RAC_ENC;
  var km = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(pw), {{name:'PBKDF2'}}, false, ['deriveKey']
  );
  var key = await crypto.subtle.deriveKey(
    {{name:'PBKDF2', salt:b64(enc.salt), iterations:enc.iterations, hash:'SHA-256'}},
    km, {{name:'AES-GCM', length:256}}, false, ['decrypt']
  );
  var pt = await crypto.subtle.decrypt(
    {{name:'AES-GCM', iv:b64(enc.nonce)}}, key, b64(enc.ciphertext)
  );
  return JSON.parse(new TextDecoder().decode(pt));
}}
function doUnlock() {{
  var err = document.getElementById('err');
  err.textContent = '';
  unlock(document.getElementById('pw').value).then(function (d) {{
    document.getElementById('lock').hidden = true;
    document.getElementById('dash').hidden = false;
    render(d);
  }}).catch(function () {{
    err.textContent = 'Senha incorreta';
  }});
}}
document.getElementById('go').addEventListener('click', doUnlock);
document.getElementById('pw').addEventListener('keydown', function (e) {{
  if (e.key === 'Enter') doUnlock();
}});
</script>
</body>
</html>"""
