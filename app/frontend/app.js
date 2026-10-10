// Month-End Variance Copilot - frontend. Plain JavaScript; every figure comes from the backend API.

const state = { tab: "overview", period: "all", site: "all", meta: null };
const SITE_SLOT = {};               // colour follows the site, never its rank
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
  "September", "October", "November", "December"];

// --- Helpers ---------------------------------------------------------------------------------

const $ = (sel) => document.querySelector(sel);
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const nf0 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function sign(value, text) { return value > 0 ? `+${text}` : value < 0 ? `−${text}` : text; }
function eurK(value, signed = false) {
  if (value === null || value === undefined) return "–";
  const text = `EUR ${nf0.format(Math.abs(value) / 1000)}k`;
  return signed ? sign(Math.round(value / 1000), text) : text;
}
function eurM(value, signed = false) {
  if (value === null || value === undefined) return "–";
  const text = `EUR ${nf1.format(Math.abs(value) / 1e6)}m`;
  return signed ? sign(value, text) : text;
}
function eur(value) { return value === null || value === undefined ? "–" : `EUR ${nf0.format(value)}`; }
function pct(fraction, signed = true) {
  if (fraction === null || fraction === undefined) return "–";
  const text = `${nf1.format(Math.abs(fraction) * 100)}%`;
  return signed ? sign(Math.round(fraction * 1000), text) : text;
}
function periodLabel(period, long = false) {
  if (!period || period === "all") return "January to September 2026";
  const [year, month] = period.split("-");
  return `${(long ? MONTHS_LONG : MONTHS)[Number(month) - 1]} ${year}`;
}
function siteColor(site) { return css(`--site-${SITE_SLOT[site] || 1}`); }

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" }, ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

let toastTimer;
function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 4500);
}

function table(el, columns, rows, rowClass = () => "") {
  const head = columns.map((c) => `<th class="${c.num ? "num" : ""}">${esc(c.label)}</th>`).join("");
  const body = rows.map((row) => `<tr class="${rowClass(row)}">${columns.map((c) =>
    `<td class="${c.num ? "num" : ""}">${c.html ? c.html(row) : esc(c.value(row))}</td>`).join("")}</tr>`).join("");
  el.innerHTML = `<thead><tr>${head}</tr></thead><tbody>${body || `<tr><td class="muted" colspan="${columns.length}">No rows</td></tr>`}</tbody>`;
}

function tile(label, value, sub = "") {
  return `<div class="tile"><div class="tile-label">${esc(label)}</div><div class="tile-value">${esc(value)}</div>${sub ? `<div class="tile-sub">${esc(sub)}</div>` : ""}</div>`;
}

// --- Plotly ----------------------------------------------------------------------------------

function baseLayout(extra = {}) {
  const axis = { gridcolor: css("--grid"), linecolor: css("--axis"), zerolinecolor: css("--axis"),
    tickfont: { color: css("--ink-muted"), size: 12 }, automargin: true };
  return {
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: css("--font"), color: css("--ink-2"), size: 12.5 },
    margin: { l: 12, r: 12, t: 8, b: 8 },
    xaxis: { ...axis, showgrid: false }, yaxis: { ...axis },
    legend: { orientation: "h", x: 0, y: 1.12, font: { color: css("--ink-2") } },
    hoverlabel: { bgcolor: css("--surface"), bordercolor: css("--border"), font: { color: css("--ink") } },
    bargap: 0.35, barcornerradius: 4,
    ...extra,
  };
}
const plotConfig = { displayModeBar: false, responsive: true };
function plot(id, traces, layout) { Plotly.react(id, traces, baseLayout(layout), plotConfig); }

// --- Home (landing page) ----------------------------------------------------------------------

async function renderHome() {
  const [dq, overview, flags, business] = await Promise.all([
    api("/api/data-quality"), api("/api/overview"), api("/api/flags"), api("/api/business-case")]);
  const passed = dq.reconciliation.filter((r) => r.passed).length;
  const worst = Math.max(...dq.reconciliation.map((r) => Math.abs(r.difference_eur)));
  const flagCount = flags.length;
  const approved = flags.filter((i) => i.commentary && i.commentary.status === "Approved").length;
  const sites = state.meta.sites.length;
  const saved = business.today_h - business.after_h;

  $("#hero-stats").innerHTML = [
    [`${dq.mapped_rows}/${dq.harmonised_rows}`, `rows mapped across ${sites} sites`],
    [`${passed}/${dq.reconciliation.length}`, "reconciliation checks passed"],
    [String(dq.findings.length), "source-data problems caught"],
    [String(flagCount), `material items flagged · ${approved} approved`],
  ].map(([v, l]) => `<div><span class="stat-value">${esc(v)}</span><span class="stat-label">${esc(l)}</span></div>`).join("");

  const proof = [
    [`${Math.round(dq.mapped_rows / dq.harmonised_rows * 100)}<small>%</small>`, "Rows on one structure",
      `${nf0.format(dq.harmonised_rows)} rows from ${sites} layouts, languages and currencies, each with its local codes and source line.`],
    [`EUR ${nf0.format(worst)}`, "Largest reconciliation gap",
      `${passed} of ${dq.reconciliation.length} site-month checks tie back to the source files.`],
    [`${dq.findings.length}<small>/2</small>`, "Planted data errors caught",
      "A duplicated ledger line and a missing actual, both reported with file and line."],
    [`${flagCount}<small> of ${nf0.format(dq.harmonised_rows)}</small>`, "Items flagged as material",
      `${overview.flags.spend || 0} spend and ${overview.flags.volume || 0} volume flags, each tracing to a planted business event.`],
    [`~${nf0.format(saved)}<small> h</small>`, "Saved per close (estimate)",
      `${nf1.format(business.today_h)} h of manual work becomes ${nf1.format(business.after_h)} h of review.`],
  ];
  $("#proof-grid").innerHTML = proof.map(([v, l, sub]) =>
    `<div class="proof"><div class="proof-value">${v}</div><div class="proof-label">${esc(l)}</div><div class="proof-sub">${esc(sub)}</div></div>`).join("");

  const rows = business.rows.map((r) => `<tr><td>${esc(r.activity)}</td><td class="num">${nf1.format(r.today_h)}</td><td class="num">${nf1.format(r.after_h)}</td><td class="muted">${esc(r.assumption)}</td></tr>`).join("");
  $("#table-business-case").innerHTML = `<thead><tr><th>Activity</th><th class="num">Today (h)</th><th class="num">With the platform (h)</th><th>Assumption</th></tr></thead>
    <tbody>${rows}<tr class="total"><td>Total per close</td><td class="num">${nf1.format(business.today_h)}</td><td class="num">${nf1.format(business.after_h)}</td><td>About ${nf0.format(saved)} hours saved per close (estimate)</td></tr></tbody>`;
}

// --- Overview --------------------------------------------------------------------------------

async function renderOverview() {
  const data = await api(`/api/overview?period=${state.period}`);
  const t = data.totals;
  const flags = data.flags;
  $("#kpi-tiles").innerHTML = [
    tile("Plan cost", eurM(t.plan_eur), periodLabel(state.period)),
    tile("Actual cost", eurM(t.actual_eur)),
    tile("Total variance", eurM(t.total_var, true), `${pct(t.total_var / t.plan_eur)} of plan`),
    tile("Volume effect", eurM(t.volume_effect, true), "cost that moved with wafer output"),
    tile("Spend effect", eurM(t.spend_effect, true), "cost above or below the flexed budget"),
    tile("Flagged items", String((flags.spend || 0) + (flags.volume || 0)),
      `${flags.spend || 0} spend · ${flags.volume || 0} volume`),
  ].join("");

  $("#not-posted-note").textContent = data.not_posted.length
    ? `Variance figures exclude ${data.not_posted.length} row(s) whose actual is not posted yet: ` +
      data.not_posted.map((r) => `${r.site} ${periodLabel(r.period)} ${r.group_area} ${r.group_account} (plan ${eurK(r.plan_eur)})`).join("; ") + "."
    : "";

  const months = data.monthly.map((m) => periodLabel(m.period));
  const selected = data.monthly.map((m) => state.period === "all" || m.period === state.period);
  const opacity = selected.map((s) => (s ? 1 : 0.35));
  const hover = (name) => `%{x}<br>${name}: %{customdata}<extra></extra>`;
  plot("chart-monthly", [
    { type: "bar", name: "Volume effect", x: months, y: data.monthly.map((m) => m.volume_effect / 1000),
      customdata: data.monthly.map((m) => eurK(m.volume_effect, true)), hovertemplate: hover("Volume effect"),
      marker: { color: css("--effect-volume"), opacity, line: { color: css("--surface"), width: 2 } } },
    { type: "bar", name: "Spend effect", x: months, y: data.monthly.map((m) => m.spend_effect / 1000),
      customdata: data.monthly.map((m) => eurK(m.spend_effect, true)), hovertemplate: hover("Spend effect"),
      marker: { color: css("--effect-spend"), opacity, line: { color: css("--surface"), width: 2 } } },
    { type: "scatter", mode: "markers", name: "Total variance", x: months, y: data.monthly.map((m) => m.total_var / 1000),
      customdata: data.monthly.map((m) => eurK(m.total_var, true)), hovertemplate: hover("Total variance"),
      marker: { color: css("--ink"), size: 9, line: { color: css("--surface"), width: 2 } } },
  ], { barmode: "relative", yaxis: { ...baseLayout().yaxis, title: { text: "EUR thousand", font: { size: 12 } } },
    margin: { l: 12, r: 12, t: 30, b: 8 } });

  table($("#table-sites"), [
    { label: "Site", value: (r) => r.site },
    { label: "Plan", num: true, value: (r) => eurK(r.plan_eur) },
    { label: "Actual", num: true, value: (r) => eurK(r.actual_eur) },
    { label: "Variance", num: true, value: (r) => eurK(r.total_var, true) },
    { label: "% of plan", num: true, value: (r) => pct(r.total_var_pct) },
    { label: "Volume effect", num: true, value: (r) => eurK(r.volume_effect, true) },
    { label: "Spend effect", num: true, value: (r) => eurK(r.spend_effect, true) },
    { label: "Flags", num: true, value: (r) => `${r.spend_flags} spend · ${r.volume_flags} volume` },
  ], data.by_site);
}

// --- Site comparison -------------------------------------------------------------------------

async function renderSites() {
  const data = await api(`/api/sites?period=${state.period}`);
  const sites = data.cost_per_wafer.map((r) => r.site);

  plot("chart-cpw", [
    { type: "bar", name: "Plan", x: sites, y: data.cost_per_wafer.map((r) => r.cpw_plan),
      text: data.cost_per_wafer.map((r) => nf0.format(r.cpw_plan)), textposition: "outside",
      textfont: { color: css("--ink-2") }, hovertemplate: "%{x}<br>Plan: EUR %{y:,.0f} per wafer<extra></extra>",
      marker: { color: css("--plan-bar"), line: { color: css("--surface"), width: 2 } } },
    { type: "bar", name: "Actual", x: sites, y: data.cost_per_wafer.map((r) => r.cpw_actual),
      text: data.cost_per_wafer.map((r) => nf0.format(r.cpw_actual) + (r.complete ? "" : "*")), textposition: "outside",
      textfont: { color: css("--ink") }, hovertemplate: "%{x}<br>Actual: EUR %{y:,.0f} per wafer<extra></extra>",
      marker: { color: sites.map(siteColor), line: { color: css("--surface"), width: 2 } } },
  ], { barmode: "group", margin: { l: 12, r: 12, t: 30, b: 8 },
    yaxis: { ...baseLayout().yaxis, title: { text: "EUR per wafer", font: { size: 12 } }, rangemode: "tozero" } });

  const bySite = {};
  data.trend.forEach((r) => { (bySite[r.site] ||= []).push(r); });
  const traces = Object.entries(bySite).map(([site, rows]) => ({
    type: "scatter", mode: "lines+markers", name: site,
    x: rows.map((r) => periodLabel(r.period)), y: rows.map((r) => r.cpw_actual),
    line: { color: siteColor(site), width: 2 }, marker: { size: 8, color: siteColor(site), line: { color: css("--surface"), width: 2 } },
    hovertemplate: `${site}<br>%{x}: EUR %{y:,.0f} per wafer<extra></extra>`,
  }));
  const shapes = state.period === "all" ? [] : [{
    type: "line", xref: "x", yref: "paper", x0: periodLabel(state.period), x1: periodLabel(state.period), y0: 0, y1: 1,
    line: { color: css("--axis"), width: 2 } }];
  const annotations = Object.entries(bySite).map(([site, rows]) => ({
    x: periodLabel(rows.at(-1).period), y: rows.at(-1).cpw_actual, text: site, showarrow: false,
    xanchor: "left", xshift: 8, font: { color: css("--ink-2"), size: 12 } }));
  plot("chart-cpw-trend", traces, { shapes, annotations, showlegend: true, margin: { l: 12, r: 90, t: 30, b: 8 },
    yaxis: { ...baseLayout().yaxis, title: { text: "EUR per wafer", font: { size: 12 } } } });

  const accounts = state.meta.group_accounts;
  const heatSites = [...new Set(data.heatmap.map((r) => r.site))];
  const lookup = Object.fromEntries(data.heatmap.map((r) => [`${r.site}|${r.group_account}`, r]));
  const z = heatSites.map((s) => accounts.map((a) => lookup[`${s}|${a}`]?.total_var_pct * 100));
  const maxAbs = Math.max(5, ...z.flat().map((v) => Math.abs(v || 0)));
  plot("chart-heatmap", [{
    type: "heatmap", x: accounts, y: heatSites, z, zmin: -maxAbs, zmax: maxAbs, xgap: 2, ygap: 2,
    colorscale: [[0, css("--neg")], [0.25, css("--neg-soft")], [0.5, css("--mid")], [0.75, css("--pos-soft")], [1, css("--pos")]],
    text: z.map((row) => row.map((v) => (v === undefined ? "" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${nf1.format(Math.abs(v))}%`))),
    texttemplate: "%{text}", textfont: { color: css("--ink"), size: 12.5 },
    hovertemplate: "%{y} · %{x}<br>Variance: %{text} of plan<extra></extra>",
    colorbar: { title: { text: "% of plan", font: { size: 12 } }, thickness: 10, outlinewidth: 0, tickfont: { color: css("--ink-muted") } },
  }], { xaxis: { ...baseLayout().xaxis, side: "bottom" }, yaxis: { ...baseLayout().yaxis, autorange: "reversed" } });

  table($("#table-cpw"), [
    { label: "Site", value: (r) => r.site },
    { label: "Plan wafers", num: true, value: (r) => nf0.format(r.plan_wafers) },
    { label: "Actual wafers", num: true, value: (r) => nf0.format(r.actual_wafers) },
    { label: "Wafer deviation", num: true, value: (r) => pct(r.actual_wafers / r.plan_wafers - 1) },
    { label: "Cost per wafer, plan", num: true, value: (r) => eur(r.cpw_plan) },
    { label: "Cost per wafer, actual", num: true, value: (r) => eur(r.cpw_actual) + (r.complete ? "" : " *") },
  ], data.cost_per_wafer);
  if (data.cost_per_wafer.some((r) => !r.complete)) {
    $("#table-cpw").insertAdjacentHTML("beforeend",
      `<caption class="muted" style="caption-side:bottom;text-align:left;padding-top:8px">* Incomplete: an actual is not posted yet in this selection.</caption>`);
  }
}

// --- Variance bridge -------------------------------------------------------------------------

async function renderBridge() {
  const data = await api(`/api/bridge?site=${state.site}&period=${state.period}`);
  const t = data.totals;
  $("#bridge-title").textContent = `Variance bridge · ${state.site === "all" ? "All sites" : state.site} · ${periodLabel(state.period)}`;

  const variance = t.actual_eur - t.plan_eur;
  $("#bridge-sub").textContent = `Plan ${eurK(t.plan_eur)} → actual ${eurK(t.actual_eur)}: a variance of ` +
    `${eurK(variance, true)}, split into the volume effect and the spend effect for each cost type.`;
  const labels = ["Volume effect", ...data.by_account.map((r) => `Spend: ${r.group_account}`), "Total variance"];
  const values = [t.volume_effect, ...data.by_account.map((r) => r.spend_effect), variance];
  const measures = [...labels.slice(0, -1).map(() => "relative"), "total"];
  const text = values.map((v) => eurK(v, true));
  plot("chart-bridge", [{
    type: "waterfall", x: labels, y: values.map((v) => v / 1000), measure: measures, base: 0,
    text, textposition: "outside", textfont: { color: css("--ink-2"), size: 12 }, cliponaxis: false,
    customdata: text, hovertemplate: "%{x}<br>%{customdata}<extra></extra>",
    increasing: { marker: { color: css("--pos") } },
    decreasing: { marker: { color: css("--neg") } },
    totals: { marker: { color: css("--total-bar") } },
    connector: { line: { color: css("--axis"), width: 1 } },
  }], { showlegend: false, margin: { l: 12, r: 12, t: 30, b: 8 },
    yaxis: { ...baseLayout().yaxis, title: { text: "EUR thousand (red = cost above plan)", font: { size: 12 } } } });

  table($("#table-rows"), [
    { label: "Site", value: (r) => r.site },
    { label: "Period", value: (r) => periodLabel(r.period) },
    { label: "Area", value: (r) => r.group_area },
    { label: "Account", value: (r) => r.group_account },
    { label: "Local codes", value: (r) => `${r.local_cost_centre} / ${r.local_account_code}` },
    { label: "Plan", num: true, value: (r) => eurK(r.plan_eur) },
    { label: "Flexed budget", num: true, value: (r) => eurK(r.flexed_eur) },
    { label: "Actual", num: true, value: (r) => (r.actual_posted ? eurK(r.actual_eur) : "not posted") },
    { label: "Variance", num: true, value: (r) => eurK(r.total_var, true) },
    { label: "Volume effect", num: true, value: (r) => eurK(r.volume_effect, true) },
    { label: "Spend effect", num: true, value: (r) => eurK(r.spend_effect, true) },
    { label: "Flag", html: (r) => (r.spend_flag ? '<span class="badge critical">Spend flag</span>' : "") },
    { label: "Source", html: (r) => `<span class="muted">${esc(r.source_file.split("/").at(-1))} line ${r.source_line_plan}${r.source_line_actual !== r.source_line_plan ? ` / ${r.source_line_actual}` : ""}</span>` },
  ], data.rows, (r) => (r.spend_flag ? "flagged" : ""));
}

// --- Flagged items ---------------------------------------------------------------------------

const FIGURE_LABELS = {
  plan_teur: "Plan", actual_teur: "Actual", flexed_budget_teur: "Flexed budget", total_variance_teur: "Variance",
  volume_effect_teur: "Volume effect", spend_effect_teur: "Spend effect",
  spend_effect_pct_of_flexed_budget: "Spend effect, % of flexed", plan_wafers: "Plan wafers",
  actual_wafers: "Actual wafers", wafer_deviation_pct: "Wafer deviation", site_plan_cost_teur: "Site plan cost",
  site_actual_cost_teur: "Site actual cost", site_total_variance_teur: "Site variance",
  site_volume_effect_teur: "Site volume effect", site_spend_effect_teur: "Site spend effect",
  cost_per_wafer_plan_eur: "Cost per wafer, plan", cost_per_wafer_actual_eur: "Cost per wafer, actual",
};
function figureText(key, value) {
  if (key.endsWith("_pct") || key.endsWith("_pct_of_flexed_budget")) return `${value > 0 ? "+" : value < 0 ? "−" : ""}${nf1.format(Math.abs(value))}%`;
  if (key.endsWith("_teur")) {
    const signed = /variance|effect/.test(key);
    const text = `EUR ${nf0.format(Math.abs(value))}k`;
    return signed ? sign(value, text) : text;
  }
  if (key.endsWith("_eur")) return `EUR ${nf0.format(value)}`;
  return nf0.format(value);
}

function flagCard(item) {
  const c = item.commentary;
  const id = encodeURIComponent(item.item_id);
  const title = item.item_type === "spend"
    ? `${item.site} · ${periodLabel(item.period, true)} · ${item.group_area} · ${item.group_account}`
    : `${item.site} · ${periodLabel(item.period, true)} · wafer volume`;
  const codes = item.local_cost_centre ? `Local codes ${item.local_cost_centre} / ${item.local_account_code}` : "All cost centres of the site";
  const figures = Object.entries(item.figures).map(([k, v]) =>
    `<div><div class="figure-label">${esc(FIGURE_LABELS[k] || k)}</div><div class="figure-value">${esc(figureText(k, v))}</div></div>`).join("");

  const approved = c && c.status === "Approved";
  const status = !c ? '<span class="badge">No draft</span>'
    : approved ? '<span class="badge good">Approved</span>' : '<span class="badge warning">Draft</span>';
  const check = !c ? "" : c.check_passed
    ? '<span class="badge good">Figures verified</span>'
    : '<span class="badge critical">Unverified figures</span>';
  const writer = !c ? "" : { llm: `written by ${c.model || "Claude"}`, template: "written by template", edited: "edited by reviewer" }[c.source];
  const approval = approved ? ` · approved by ${esc(c.reviewer_role)}, ${esc(String(c.approved_at).replace("T", " ").slice(0, 16))} UTC` : "";
  const roles = state.meta.reviewer_roles.map((r) => `<option>${esc(r)}</option>`).join("");

  return `<article class="card" data-item="${esc(item.item_id)}">
    <div class="flag-head">
      <div class="flag-title"><span class="chip">${item.item_type}</span><h3>${esc(title)}</h3></div>
      <span class="codes">${esc(codes)}</span>
    </div>
    <div class="figures">${figures}</div>
    <div class="commentary-box">
      <div class="commentary-meta">${status}${check}<span>${esc(writer || "")}${approval}</span></div>
      <textarea aria-label="Commentary" ${approved ? "readonly" : ""} data-role="text">${esc(c ? c.text : "")}</textarea>
      ${c && !c.check_passed ? `<div class="check-detail">Not in the data: ${esc(c.unknown_numbers)}. Edit or regenerate before approval.</div>` : ""}
      <div class="actions">
        ${approved
          ? `<button class="btn" data-action="reopen" data-id="${id}">Reopen</button>`
          : `<button class="btn" data-action="save" data-id="${id}">Save edit</button>
             <button class="btn" data-action="regenerate" data-id="${id}">Regenerate</button>
             <select data-role="language" aria-label="Language"><option value="en">English</option><option value="de">German</option></select>
             <select data-role="role" aria-label="Reviewer role">${roles}</select>
             <button class="btn btn-primary" data-action="approve" data-id="${id}" ${c && c.check_passed ? "" : "disabled"}>Approve</button>`}
      </div>
      <div class="cause-row">
        <input type="text" maxlength="300" data-role="cause" aria-label="Cause from the cost-centre owner"
          placeholder="Cost-centre owner: enter the cause (used in the next draft)" value="${esc(item.cause ? item.cause.cause : "")}">
        <button class="btn" data-action="cause" data-id="${id}">Save cause</button>
      </div>
    </div>
  </article>`;
}

async function renderFlags() {
  const items = await api("/api/flags");
  const open = items.filter((i) => !i.commentary || i.commentary.status !== "Approved").length;
  $("#flag-count").textContent = `${open}/${items.length}`;
  $("#flag-count").title = `${open} of ${items.length} not yet approved`;
  $("#flag-list").innerHTML = items.map(flagCard).join("") || '<p class="muted">No flagged items.</p>';
}

async function flagAction(button) {
  const card = button.closest("[data-item]");
  const id = button.dataset.id;
  const action = button.dataset.action;
  const value = (role) => card.querySelector(`[data-role="${role}"]`)?.value;
  button.disabled = true;
  try {
    if (action === "save") await api(`/api/flags/${id}/text`, { method: "PUT", body: { text: value("text") } });
    if (action === "regenerate") await api(`/api/flags/${id}/regenerate`, { method: "POST", body: { language: value("language") } });
    if (action === "approve") await api(`/api/flags/${id}/approve`, { method: "POST", body: { reviewer_role: value("role") } });
    if (action === "reopen") await api(`/api/flags/${id}/reopen`, { method: "POST" });
    if (action === "cause") {
      await api(`/api/flags/${id}/cause`, { method: "PUT", body: { cause: value("cause") } });
      toast("Cause saved. Regenerate the draft to use it.");
    }
    await renderFlags();
  } catch (error) {
    toast(error.message);
    button.disabled = false;
  }
}

// --- Data quality ----------------------------------------------------------------------------

async function renderQuality() {
  const data = await api("/api/data-quality");
  const passed = data.reconciliation.filter((r) => r.passed).length;
  const worst = Math.max(...data.reconciliation.map((r) => Math.abs(r.difference_eur)));
  $("#dq-tiles").innerHTML = [
    tile("Source rows loaded", nf0.format(data.raw_rows.reduce((s, r) => s + r.n, 0)),
      data.raw_rows.map((r) => `${r.site} ${r.n}`).join(" · ")),
    tile("Harmonised rows", nf0.format(data.harmonised_rows), "site × month × area × account"),
    tile("Mapped to group structure", pct(data.mapped_rows / data.harmonised_rows, false), `${data.mapped_rows} of ${data.harmonised_rows} rows`),
    tile("Reconciliation checks passed", `${passed} of ${data.reconciliation.length}`, `largest difference ${eur(worst)}`),
    tile("Findings", String(data.findings.length), "see table below"),
  ].join("");

  table($("#table-findings"), [
    { label: "Finding", html: (r) => `<span class="badge ${r.finding === "duplicate_removed" ? "warning" : "critical"}">${r.finding === "duplicate_removed" ? "Duplicate removed" : "Actual not posted"}</span>` },
    { label: "Site", value: (r) => r.site },
    { label: "Period", value: (r) => periodLabel(r.period) },
    { label: "Local codes", value: (r) => `${r.local_cost_centre} / ${r.local_account_code}` },
    { label: "Source", value: (r) => `${r.source_file} line ${r.source_line}` },
    { label: "Treatment", value: (r) => r.detail },
  ], data.findings);

  table($("#table-recon"), [
    { label: "Site", value: (r) => r.site },
    { label: "Period", value: (r) => periodLabel(r.period) },
    { label: "Measure", value: (r) => r.measure },
    { label: "Source total", num: true, value: (r) => eur(r.source_total_eur) },
    { label: "Harmonised total", num: true, value: (r) => eur(r.harmonised_total_eur) },
    { label: "Corrections", num: true, value: (r) => eur(r.corrections_eur) },
    { label: "Difference", num: true, value: (r) => eur(r.difference_eur) },
    { label: "Result", html: (r) => (r.passed ? '<span class="badge good">Pass</span>' : '<span class="badge critical">Fail</span>') },
  ], data.reconciliation);
}

// --- Shell -----------------------------------------------------------------------------------

const RENDER = { home: renderHome, overview: renderOverview, sites: renderSites, bridge: renderBridge, flags: renderFlags, quality: renderQuality };

async function render() {
  const view = $(`#view-${state.tab}`);
  view.classList.add("loading");          // hold the previous render, no skeleton flash
  try { await RENDER[state.tab](); } catch (error) { toast(error.message); }
  view.classList.remove("loading");
}

function selectTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
  document.querySelectorAll(".view").forEach((v) => { v.hidden = v.id !== `view-${tab}`; });
  $("#site-filter").hidden = tab !== "bridge";
  $("#filters").hidden = ["home", "flags", "quality"].includes(tab);
  $("#app-bar").hidden = tab === "home";
  window.scrollTo({ top: 0 });
  history.replaceState(null, "", `${location.search}#${tab}`);
  render();
}

async function loadMeta() {
  state.meta = await api("/api/meta");
  state.meta.sites.forEach((site, i) => { SITE_SLOT[site] = i + 1; });
  $("#notice-text").textContent = state.meta.notice;
  $("#writer-chip").textContent = state.meta.writer === "anthropic"
    ? `Commentary: Claude (${state.meta.model})` : "Commentary: template (no API key)";
  $("#refreshed-chip").textContent = `Data built ${state.meta.data_refreshed_at.replace("T", " ").slice(0, 16)}`;
  $("#period-select").innerHTML = '<option value="all">All months</option>' +
    state.meta.periods.map((p) => `<option value="${p}">${periodLabel(p, true)}</option>`).join("");
  $("#period-select").value = state.period;
  $("#site-select").innerHTML = '<option value="all">All sites</option>' +
    state.meta.sites.map((s) => `<option>${s}</option>`).join("");
  $("#site-select").value = state.site;
  const m = state.meta.materiality;
  const shares = Object.entries(state.meta.variable_shares).map(([a, s]) => `${a} ${Math.round(s * 100)}%`).join(", ");
  $("#footer").innerHTML = `
    <p><strong>Method.</strong> Positive variance = cost above plan (unfavourable). Flexed budget = plan × ((1 − variable share) + variable share × actual wafers / plan wafers). Volume effect = flexed budget − plan; spend effect = actual − flexed budget.</p>
    <p><strong>Assumption.</strong> Share of each cost type that moves with wafer volume: ${esc(shares)}. Kept in data/reference/cost_behaviour.csv and can be changed.</p>
    <p><strong>Flags.</strong> Spend flag when |spend effect| ≥ EUR ${nf0.format(m.spend_abs_eur)} and ≥ ${m.spend_pct * 100}% of the flexed budget. Volume flag when wafers differ from plan by ≥ ${m.volume_pct * 100}%.</p>
    <p>${esc(state.meta.notice)}</p>`;
}

function setupTheme() {
  const button = $("#theme-btn");
  const current = () => document.documentElement.dataset.theme
    || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const label = () => { button.textContent = current() === "dark" ? "Light theme" : "Dark theme"; };
  try { const saved = localStorage.getItem("vc-theme"); if (saved) document.documentElement.dataset.theme = saved; } catch { /* ignore */ }
  const forced = new URLSearchParams(location.search).get("theme");   // ?theme=dark for links and screenshots
  if (forced === "dark" || forced === "light") document.documentElement.dataset.theme = forced;
  label();
  button.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("vc-theme", next); } catch { /* ignore */ }
    label();
    render();                                 // charts read colours at render time
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { label(); render(); });
}

async function rebuild(button) {
  button.disabled = true;
  button.textContent = "Rebuilding…";
  try {
    const s = await api("/api/pipeline/run", { method: "POST" });
    await loadMeta();
    toast(`Rebuilt: ${s.harmonised_rows} rows, ${s.reconciliation_checks} reconciliation checks passed, ` +
      `${s.spend_flags} spend and ${s.volume_flags} volume flags, ${s.new_drafts} new draft(s).`);
    await render();
  } catch (error) {
    toast(error.message);
  }
  button.disabled = false;
  button.textContent = "Rebuild data";
}

async function init() {
  setupTheme();
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => selectTab(b.dataset.tab)));
  $("#period-select").addEventListener("change", (e) => { state.period = e.target.value; render(); });
  $("#site-select").addEventListener("change", (e) => { state.site = e.target.value; render(); });
  $("#flag-list").addEventListener("click", (e) => { const b = e.target.closest("[data-action]"); if (b) flagAction(b); });
  $("#rebuild-btn").addEventListener("click", (e) => rebuild(e.currentTarget));
  document.addEventListener("click", (e) => {
    const target = e.target.closest("[data-goto]");
    if (target) { e.preventDefault(); selectTab(target.dataset.goto); }
  });
  window.addEventListener("hashchange", () => {
    const tab = location.hash.slice(1);
    if (RENDER[tab] && tab !== state.tab) selectTab(tab);
  });
  try {
    await loadMeta();
  } catch (error) {
    toast(error.message);
    return;
  }
  const tab = location.hash.slice(1);
  selectTab(RENDER[tab] ? tab : "home");          // the landing page opens by default
  api("/api/flags").then((items) => {
    const open = items.filter((i) => !i.commentary || i.commentary.status !== "Approved").length;
    $("#flag-count").textContent = `${open}/${items.length}`;
  }).catch(() => {});
}

init();
