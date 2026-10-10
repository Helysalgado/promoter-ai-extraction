const UI_RULES = {
  "maxDocumentChars": 100000,
  "formats": [
    [".tei.xml", "TEI/XML"],
    [".xml", "TEI/XML"],
    [".tei", "TEI/XML"],
    [".txt", "TXT"]
  ],
  "requestFields": [
    "paper_id",
    "promoter_name",
    "promoter_id",
    "paper_gene_synonym",
    "document_format",
    "document",
    "provider"
  ],
  "scientificStatuses": [
    "EXTRACTED",
    "NOT_FOUND",
    "INSUFFICIENT_EVIDENCE",
    "UNSUPPORTED_MODALITY",
    "AMBIGUOUS"
  ],
  "statusLabels": {
    "EXTRACTED": "Extraído",
    "NOT_FOUND": "No encontrado",
    "INSUFFICIENT_EVIDENCE": "Evidencia insuficiente",
    "UNSUPPORTED_MODALITY": "Modalidad no soportada",
    "AMBIGUOUS": "Ambiguo"
  }
};

const REGION = {
  accepted: 'data-region="accepted"',
  rejected: 'data-region="rejected"'
};

const state = {
  document: "",
  format: "",
  sending: false,
  persistedKey: "",
  selected: "TSS",
  response: null
};

function field(id) {
  const node = document.getElementById(id);
  return node ? node.value.trim() : "";
}

function identityKey() {
  return field("paper-id") + "\n" + field("promoter-name");
}

function detectFormat(name) {
  const lower = String(name).toLowerCase();
  for (const pair of UI_RULES.formats) {
    if (lower.endsWith(pair[0])) return pair[1];
  }
  return "";
}

function providerValue() {
  const chosen = document.querySelector('input[name="method"]:checked');
  if (chosen && chosen.value === "agent") return "anthropic";
  return document.getElementById("provider").value;
}

function endpoint() {
  const chosen = document.querySelector('input[name="method"]:checked');
  if (chosen && chosen.value === "agent") return "/agent/extract";
  return "/extract";
}

function payload() {
  const body = {
    paper_id: field("paper-id"),
    promoter_name: field("promoter-name"),
    document_format: state.format,
    document: state.document,
    provider: providerValue()
  };
  const promoterId = field("promoter-id");
  const synonym = field("paper-gene-synonym");
  if (promoterId) body.promoter_id = promoterId;
  if (synonym) body.paper_gene_synonym = synonym;
  return body;
}

function canSubmit() {
  if (state.sending) return false;
  if (state.persistedKey && state.persistedKey === identityKey()) return false;
  const confirm = document.getElementById("confirm-call");
  if (!confirm || !confirm.checked) return false;
  if (!state.document || !state.format) return false;
  if (!field("paper-id") || !field("promoter-name")) return false;
  if (state.document.length > UI_RULES.maxDocumentChars) return false;
  return true;
}

function canLoad() {
  if (state.sending) return false;
  return Boolean(field("paper-id") && field("promoter-name"));
}

function refreshRunButton() {
  document.getElementById("run").disabled = !canSubmit();
}

function refreshLoadButton() {
  document.getElementById("load-saved").disabled = !canLoad();
}

function syncProvider() {
  const chosen = document.querySelector('input[name="method"]:checked');
  const provider = document.getElementById("provider");
  const agent = Boolean(chosen && chosen.value === "agent");
  provider.disabled = agent;
  if (agent) provider.value = "anthropic";
  refreshRunButton();
}

function badgeFor(attempt) {
  if (!attempt) return { tone: "empty", label: "Sin resultado", code: "" };
  if (attempt.kind === "technical") {
    const code = attempt.code || "";
    return { tone: "technical", label: "Fallo técnico", code: code };
  }
  const status = attempt.status || "";
  const labels = UI_RULES.statusLabels;
  const known = Object.prototype.hasOwnProperty.call(labels, status);
  const tone = status === "EXTRACTED" ? "extracted" : "abstained";
  return { tone: tone, label: known ? labels[status] : status, code: status };
}

function summaryFor(attempt) {
  if (!attempt || attempt.kind !== "scientific") {
    return attempt && attempt.code ? attempt.code : "";
  }
  const values = attempt.values || [];
  const parts = [];
  for (let index = 0; index < values.length; index += 1) {
    parts.push(values[index].value_normalized || values[index].value_raw || "");
  }
  return parts.filter(Boolean).join(" · ");
}

function addRow(parent, label, value, kind) {
  if (value === null || value === undefined || value === "") return;
  const row = document.createElement("div");
  row.className = kind ? "fact " + kind : "fact";
  const term = document.createElement("span");
  term.className = "fact-label";
  term.textContent = label;
  const detail = document.createElement("span");
  detail.className = "fact-value";
  detail.textContent = String(value);
  row.appendChild(term);
  row.appendChild(detail);
  parent.appendChild(row);
}

function region(kind) {
  const node = document.createElement("div");
  const raw = REGION[kind];
  const value = raw.slice(raw.indexOf('"') + 1, raw.lastIndexOf('"'));
  node.setAttribute("data-region", value);
  return node;
}

function renderEvidence(item, parent) {
  if (!item) return;
  const block = document.createElement("div");
  block.className = "evidence";
  addRow(block, "Fragmento", item.fragment, "fragment");
  addRow(block, "Segmento", item.segment_id);
  addRow(block, "Ubicación", item.location);
  addRow(block, "Tipo de fuente", item.source_type);
  parent.appendChild(block);
}

function renderAccepted(value, parent) {
  const block = document.createElement("article");
  addRow(block, "Valor informado", value.value_raw);
  addRow(block, "Valor normalizado", value.value_normalized);
  addRow(block, "Calificador", value.qualifier);
  addRow(block, "Derivación", value.derivation_note);
  const evidence = value.evidence || [];
  for (let index = 0; index < evidence.length; index += 1) {
    renderEvidence(evidence[index], block);
  }
  parent.appendChild(block);
}

function renderRejected(candidate, parent) {
  const block = document.createElement("article");
  addRow(block, "Candidato no aceptado", candidate.candidate_raw);
  addRow(block, "Motivo", candidate.rejection_reason);
  addRow(block, "Regla", candidate.rule_violated);
  if (candidate.evidence) renderEvidence(candidate.evidence, block);
  parent.appendChild(block);
}

function renderDetail() {
  const detail = document.getElementById("detail");
  while (detail.firstChild) detail.removeChild(detail.firstChild);
  const heading = document.createElement("h2");
  heading.textContent = state.selected;
  detail.appendChild(heading);
  const properties = state.response && state.response.properties;
  const attempt = properties ? properties[state.selected] : null;
  if (!attempt) return;
  const badge = badgeFor(attempt);
  addRow(detail, "Estado", badge.label + (badge.code ? " (" + badge.code + ")" : ""));
  if (attempt.kind === "technical") {
    addRow(detail, "Etapa", attempt.stage);
    addRow(detail, "Mensaje", attempt.message);
    return;
  }
  addRow(detail, "Razón de abstención", attempt.abstention_reason);
  const accepted = region("accepted");
  const values = attempt.values || [];
  for (let index = 0; index < values.length; index += 1) {
    renderAccepted(values[index], accepted);
  }
  if (accepted.childNodes.length) {
    const title = document.createElement("h3");
    title.textContent = "Valores aceptados";
    detail.appendChild(title);
    detail.appendChild(accepted);
  }
  const rejected = region("rejected");
  const candidates = attempt.candidates || [];
  for (let index = 0; index < candidates.length; index += 1) {
    renderRejected(candidates[index], rejected);
  }
  if (rejected.childNodes.length) {
    const title = document.createElement("h3");
    title.textContent = "Candidatos rechazados";
    detail.appendChild(title);
    detail.appendChild(rejected);
  }
}

function renderCards() {
  const properties = (state.response && state.response.properties) || {};
  const cards = document.querySelectorAll("[data-property]");
  for (let index = 0; index < cards.length; index += 1) {
    const card = cards[index];
    const name = card.getAttribute("data-property");
    const attempt = properties[name];
    const badge = badgeFor(attempt);
    const status = card.querySelector(".status");
    status.textContent = badge.label;
    status.className = "status tone-" + badge.tone;
    card.setAttribute("data-tone", badge.tone);
    card.querySelector(".summary").textContent = summaryFor(attempt);
    card.setAttribute("aria-pressed", name === state.selected ? "true" : "false");
  }
}

function appendStep(list, label, value) {
  const item = document.createElement("li");
  const term = document.createElement("span");
  term.className = "fact-label";
  term.textContent = label;
  const detail = document.createElement("span");
  detail.className = "fact-value";
  detail.textContent = value;
  item.appendChild(term);
  item.appendChild(document.createTextNode(" "));
  item.appendChild(detail);
  list.appendChild(item);
}

function renderAgentTrace(agent, host) {
  const metrics = document.createElement("div");
  metrics.className = "trace-metrics";
  addRow(metrics, "Terminación", agent.termination);
  addRow(metrics, "Rondas", agent.rounds);
  addRow(metrics, "Herramientas", agent.tool_executions);
  host.appendChild(metrics);
  const steps = agent.steps || [];
  if (!steps.length) return;
  const list = document.createElement("ol");
  list.className = "trace-steps";
  for (let index = 0; index < steps.length; index += 1) {
    const step = steps[index];
    const result = step.result || {};
    const mark = result.status || result.code || result.kind || "";
    appendStep(list, step.tool || "herramienta", (step.property || "") + " " + mark);
  }
  host.appendChild(list);
}

function renderRetrievalTrace(retrieval, host) {
  const metrics = document.createElement("div");
  metrics.className = "trace-metrics";
  addRow(metrics, "Modelo de embeddings", retrieval.embedding_model);
  host.appendChild(metrics);
  const properties = retrieval.properties || {};
  const names = Object.keys(properties);
  if (!names.length) return;
  const list = document.createElement("ul");
  list.className = "trace-steps";
  for (let index = 0; index < names.length; index += 1) {
    const item = properties[names[index]] || {};
    const ids = (item.segment_ids || []).join(", ");
    appendStep(list, names[index], (item.mode || "") + " " + ids);
  }
  host.appendChild(list);
}

function renderTrace(body) {
  const host = document.getElementById("trace-body");
  while (host.firstChild) host.removeChild(host.firstChild);
  if (body.agent) renderAgentTrace(body.agent, host);
  if (body.retrieval) renderRetrievalTrace(body.retrieval, host);
}

function clearResults() {
  state.response = null;
  renderCards();
  const detail = document.getElementById("detail");
  while (detail.firstChild) detail.removeChild(detail.firstChild);
  const host = document.getElementById("trace-body");
  while (host.firstChild) host.removeChild(host.firstChild);
}

function showError(status, body) {
  const code = body && body.code ? body.code : "CONNECTION_ERROR";
  const message = body && body.message ? body.message : "No se pudo contactar el servidor local.";
  const fields = body && body.fields ? body.fields.join(", ") : "";
  document.getElementById("status").textContent = [String(status || ""), code, message, fields]
    .filter(Boolean)
    .join(" · ");
  clearResults();
  if (code === "FILE_EXISTS" || status === 409) state.persistedKey = identityKey();
}

function setSelected(name) {
  state.selected = name;
  renderCards();
  renderDetail();
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  return Math.round(bytes / 1024) + " KB";
}

function onFile() {
  const input = document.getElementById("article");
  const file = input.files && input.files[0];
  state.document = "";
  state.format = "";
  if (!file) {
    document.getElementById("file-name").textContent = "Ningún archivo seleccionado";
    document.getElementById("file-size").textContent = "";
    document.getElementById("document-format").textContent = "—";
    refreshRunButton();
    return;
  }
  state.format = detectFormat(file.name);
  document.getElementById("file-name").textContent = file.name;
  document.getElementById("file-size").textContent = formatSize(file.size);
  document.getElementById("document-format").textContent = state.format || "Formato no reconocido";
  const reader = new FileReader();
  reader.onload = function () {
    state.document = typeof reader.result === "string" ? reader.result : "";
    if (state.document.length > UI_RULES.maxDocumentChars) {
      document.getElementById("status").textContent =
        "413 · DOCUMENT_TOO_LARGE · El documento supera el límite del servidor.";
    }
    refreshRunButton();
  };
  reader.readAsText(file, "UTF-8");
}

async function loadSaved() {
  if (!canLoad()) return;
  state.sending = true;
  refreshRunButton();
  refreshLoadButton();
  const runId = field("paper-id") + "__" + field("promoter-name");
  try {
    const response = await fetch("/predictions/" + encodeURIComponent(runId));
    const body = await response.json();
    if (!response.ok) {
      showError(response.status, body);
      return;
    }
    state.response = body;
    state.persistedKey = identityKey();
    document.getElementById("status").textContent = "Resultado previamente guardado";
    renderCards();
    renderDetail();
    renderTrace(body);
  } catch (error) {
    showError(0, {
      code: "CONNECTION_ERROR",
      message: "No se pudo contactar el servidor local."
    });
  } finally {
    state.sending = false;
    refreshRunButton();
    refreshLoadButton();
  }
}

async function submitExtraction(event) {
  event.preventDefault();
  if (!canSubmit()) return;
  state.sending = true;
  refreshRunButton();
  refreshLoadButton();
  try {
    const response = await fetch(endpoint(), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload())
    });
    const body = await response.json();
    if (!response.ok) {
      showError(response.status, body);
      return;
    }
    state.response = body;
    state.persistedKey = identityKey();
    document.getElementById("status").textContent =
      "Extracción guardada. No se repetirá sola para esta identidad.";
    renderCards();
    renderDetail();
    renderTrace(body);
  } catch (error) {
    showError(0, {
      code: "CONNECTION_ERROR",
      message: "No se pudo contactar el servidor local."
    });
  } finally {
    state.sending = false;
    refreshRunButton();
    refreshLoadButton();
  }
}

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("article").addEventListener("change", onFile);
  document.getElementById("extract-form").addEventListener("submit", submitExtraction);
  document.getElementById("load-saved").addEventListener("click", loadSaved);
  const methods = document.querySelectorAll('input[name="method"]');
  for (let index = 0; index < methods.length; index += 1) {
    methods[index].addEventListener("change", syncProvider);
  }
  document.getElementById("provider").addEventListener("change", refreshRunButton);
  document.getElementById("confirm-call").addEventListener("change", refreshRunButton);
  document.getElementById("paper-id").addEventListener("input", function () {
    refreshRunButton();
    refreshLoadButton();
  });
  document.getElementById("promoter-name").addEventListener("input", function () {
    refreshRunButton();
    refreshLoadButton();
  });
  const cards = document.querySelectorAll("[data-property]");
  for (let index = 0; index < cards.length; index += 1) {
    cards[index].addEventListener("click", function () {
      setSelected(this.getAttribute("data-property"));
    });
  }
  syncProvider();
  refreshRunButton();
  refreshLoadButton();
});
