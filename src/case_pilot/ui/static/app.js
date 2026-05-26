(() => {
  const $ = (id) => document.getElementById(id);
  const escape = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // Smooth-scroll for nav anchors
  document.querySelectorAll("[data-scroll]").forEach((a) => {
    a.addEventListener("click", (e) => {
      const href = a.getAttribute("href");
      if (!href || !href.startsWith("#")) return;
      const el = document.querySelector(href);
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  // Health / mode
  fetch("/healthz")
    .then((r) => r.json())
    .then((h) => {
      const isLive = !h.use_mock_llm;
      const pill = $("mode-pill");
      pill.classList.add(isLive ? "live" : "mock");
      $("mode-text").textContent = isLive ? `LIVE · ${h.model}` : `MOCK · ${h.model}`;
      $("footer-mode").textContent = isLive ? `LIVE (${h.model})` : `MOCK (${h.model})`;
      $("stat-corpus").textContent = h.corpus_chunks ?? "—";
      $("stat-model").textContent = h.model;
    })
    .catch(() => {
      $("mode-pill").classList.add("mock");
      $("mode-text").textContent = "offline";
    });

  // Samples
  let caseSamples = [];
  fetch("/api/samples/cases").then((r) => r.json()).then((data) => {
    caseSamples = data;
    const sel = $("case-sample");
    data.forEach((s, i) => {
      const opt = document.createElement("option");
      opt.value = i;
      opt.textContent = `${s.case_id} — ${(s.submitted_by || "").slice(0, 30)}`;
      sel.appendChild(opt);
    });
    loadCase(0);
  });

  const loadCase = (i) => {
    const s = caseSamples[i];
    if (!s) return;
    $("case-id").value = s.case_id || "";
    $("case-date").value = s.date || "";
    $("case-submitter").value = s.submitted_by || "";
    $("case-site").value = s.site || "";
    $("case-description").value = s.description || "";
  };
  $("case-sample").addEventListener("change", (e) => loadCase(+e.target.value));

  // Submit
  document.querySelectorAll(".btn-primary").forEach((b) => {
    const t = b.querySelector(".btn-text");
    if (t && !b.dataset.label) b.dataset.label = t.textContent;
  });

  $("case-submit").addEventListener("click", async () => {
    const btn = $("case-submit");
    const status = $("case-status");
    const empty = $("case-empty");
    const result = $("case-result");

    const payload = {
      case_id: $("case-id").value.trim() || "CASE-DEMO",
      date: $("case-date").value.trim(),
      submitted_by: $("case-submitter").value.trim(),
      site: $("case-site").value.trim(),
      description: $("case-description").value.trim(),
    };

    setSubmitting(btn, true);
    showStatus(status, "running", "Retrieving from corpus and drafting case record…");
    empty.hidden = true;
    result.hidden = false;
    result.innerHTML = renderRunningSkeleton();
    const t0 = performance.now();

    try {
      const resp = await fetch("/agents/case/intake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error(await formatError(resp));
      const data = await resp.json();
      const wall = Math.round(performance.now() - t0);
      result.innerHTML = renderCaseResult(data, wall);
      showStatus(status, "ok", `Done — run_id ${data.run_id}`);
    } catch (e) {
      result.innerHTML = "";
      empty.hidden = false;
      showStatus(status, "error", e.message);
    } finally {
      setSubmitting(btn, false);
    }
  });

  const setSubmitting = (btn, on) => {
    btn.disabled = on;
    btn.querySelector(".btn-text").textContent = on ? "Running…" : btn.dataset.label;
    btn.querySelector(".btn-spinner").hidden = !on;
  };

  const showStatus = (el, kind, msg) => {
    if (!msg) { el.hidden = true; el.className = "status"; return; }
    el.hidden = false;
    el.className = `status ${kind}`;
    el.textContent = msg;
  };

  async function formatError(resp) {
    let msg = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      if (body && body.detail) {
        if (typeof body.detail === "string") {
          msg = `${msg}: ${body.detail}`;
        } else {
          msg = `${body.detail.error || "Error"}: ${body.detail.message || JSON.stringify(body.detail)}`;
        }
      }
    } catch (_) {}
    return msg;
  }

  const renderRunningSkeleton = () => `
    <div class="telemetry-strip">
      ${["Run","Steps","Tokens","Cost"].map((l) => `
        <div class="telem-cell"><div class="telem-label">${l}</div><div class="telem-value">…</div></div>
      `).join("")}
    </div>
    <div class="empty-state" style="padding:50px 20px">
      <p class="muted">Agent is thinking — typically 8–15 seconds with tool calls.</p>
    </div>
  `;

  const telemetryStrip = (data, wallMs) => {
    const cost = (data.cost_usd ?? 0).toFixed(4);
    return `
      <div class="telemetry-strip">
        <div class="telem-cell"><div class="telem-label">Steps</div><div class="telem-value">${data.steps ?? 0}</div></div>
        <div class="telem-cell"><div class="telem-label">Tokens</div><div class="telem-value">${(data.input_tokens || 0).toLocaleString()} <span class="muted" style="font-size:11px">in</span> · ${(data.output_tokens || 0).toLocaleString()} <span class="muted" style="font-size:11px">out</span></div></div>
        <div class="telem-cell"><div class="telem-label">Cost</div><div class="telem-value">$${cost}</div></div>
        <div class="telem-cell"><div class="telem-label">Wall time</div><div class="telem-value">${(wallMs / 1000).toFixed(1)}s</div></div>
      </div>
    `;
  };

  const renderCaseResult = (data, wallMs) => {
    const p = data.parsed || {};
    const parts = [telemetryStrip(data, wallMs)];

    if (p.case_summary) {
      parts.push(`
        <div class="result-section">
          <h4 class="result-section-title">Normalized case summary</h4>
          <div class="summary-card">${escape(p.case_summary)}</div>
        </div>
      `);
    } else if (data.final_text) {
      parts.push(`<div class="result-section"><h4 class="result-section-title">Raw output</h4><div class="summary-card">${escape(data.final_text)}</div></div>`);
    }

    // Badges
    const badges = [];
    if (p.imaging_benefit) {
      const band = String(p.imaging_benefit).split(" ")[0].toLowerCase();
      badges.push(`<span class="badge benefit-${band}"><span class="b-label">imaging benefit</span><span class="b-value">${escape(String(p.imaging_benefit).split(" ")[0])}</span></span>`);
    }
    if (p.complexity_band) {
      badges.push(`<span class="badge complexity-${p.complexity_band}"><span class="b-label">complexity</span><span class="b-value">${escape(p.complexity_band)}</span></span>`);
    }
    if (p.needs_clinical_specialist_review !== undefined) {
      const yes = !!p.needs_clinical_specialist_review;
      badges.push(`<span class="badge flag-${yes ? "yes" : "no"}"><span class="b-label">specialist review</span><span class="b-value">${yes ? "required" : "not required"}</span></span>`);
    }
    if (badges.length) {
      parts.push(`<div class="result-section"><div class="badges">${badges.join("")}</div></div>`);
    }

    if (Array.isArray(p.indications_check) && p.indications_check.length) {
      const items = p.indications_check.map((c) => `
        <div class="indication-row">
          <div class="indication-check ${c.ok ? "ok" : "not-ok"}">${c.ok ? "✓" : "✕"}</div>
          <div class="indication-text">
            <div class="indication-item">${escape(c.item)}</div>
            ${c.source ? `<div class="indication-source">${escape(c.source)}</div>` : ""}
          </div>
        </div>
      `).join("");
      parts.push(`<div class="result-section"><h4 class="result-section-title">Indications check · ${p.indications_check.length}</h4>${items}</div>`);
    }

    if (p.recommended_configuration && typeof p.recommended_configuration === "object") {
      const c = p.recommended_configuration;
      parts.push(`
        <div class="result-section">
          <h4 class="result-section-title">Recommended implant configuration</h4>
          <div class="config-grid">
            ${c.construct ? `<div class="config-cell"><div class="config-label">Construct</div><div class="config-value">${escape(c.construct)}</div></div>` : ""}
            <div class="config-cell"><div class="config-label">Screws</div><div class="config-value">${escape(c.screws || "—")}</div></div>
            <div class="config-cell"><div class="config-label">Rods</div><div class="config-value">${escape(c.rods || "—")}</div></div>
            ${c.rationale ? `<div class="config-cell full"><div class="config-label">Rationale</div><div class="config-value">${escape(c.rationale)}</div></div>` : ""}
          </div>
        </div>
      `);
    }

    if (Array.isArray(p.compliance_flags) && p.compliance_flags.length) {
      const items = p.compliance_flags.map((f) => `
        <div class="compliance-row">
          <span class="compliance-status ${escape(f.status || "ok")}">${escape(f.status || "—")}</span>
          <span class="compliance-category">${escape(f.category || "")}</span>
          <span class="compliance-note">${escape(f.note || "")}</span>
        </div>
      `).join("");
      parts.push(`<div class="result-section"><h4 class="result-section-title">Compliance flags · ${p.compliance_flags.length}</h4>${items}</div>`);
    }

    if (Array.isArray(p.open_questions) && p.open_questions.length) {
      parts.push(`<div class="result-section"><h4 class="result-section-title">Open questions for the surgeon</h4><ul class="list-tight">${p.open_questions.map((q) => `<li>${escape(q)}</li>`).join("")}</ul></div>`);
    }

    if (p.rationale) {
      parts.push(`<div class="result-section"><h4 class="result-section-title">Reviewer rationale</h4><div class="rationale">${escape(p.rationale)}</div></div>`);
    }

    if (data.tool_invocations && data.tool_invocations.length) {
      parts.push(renderTimeline(data.tool_invocations));
    }

    return parts.join("");
  };

  const renderTimeline = (invocations) => {
    const steps = invocations.map((inv, i) => `
      <div class="tool-step">
        <div class="tool-dot">${i + 1}</div>
        <details class="tool-card" ${i === 0 ? "open" : ""}>
          <summary>
            <span class="tool-name">${escape(inv.name)}</span>
            <span class="tool-args">${escape(formatToolArgs(inv.input))}</span>
          </summary>
          <div class="tool-body">${renderToolResult(inv)}</div>
        </details>
      </div>
    `).join("");
    return `
      <div class="result-section">
        <h4 class="result-section-title">Agent reasoning · ${invocations.length} tool calls</h4>
        <div class="timeline">${steps}</div>
      </div>
    `;
  };

  const formatToolArgs = (obj) => {
    if (!obj || typeof obj !== "object") return "";
    return Object.entries(obj).map(([k, v]) => {
      const sv = typeof v === "string" && v.length > 50 ? v.slice(0, 50) + "…" : JSON.stringify(v);
      return `${k}=${sv}`;
    }).join(", ");
  };

  const renderToolResult = (inv) => {
    const r = inv.result;
    if (r && Array.isArray(r.results)) {
      const items = r.results.slice(0, 8).map((x) => `
        <li>
          <span class="ret-id">${escape(x.source_type)}:${escape(x.source_id)}${x.section ? " · " + escape(x.section) : ""}</span>
          <span class="ret-score">${x.score}</span>
        </li>
      `).join("");
      return `<div class="muted" style="margin-top:10px;font-size:12px">${r.count} chunks returned</div><ul class="retrieved-list">${items}</ul>`;
    }
    return `<pre>${escape(JSON.stringify(r, null, 2))}</pre>`;
  };
})();
