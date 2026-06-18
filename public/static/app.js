const appState = {
  specialties: [],
  appointments: [],
  prescriptions: [],
  transactions: [],
  patients: [],
  workers: [],
  consultorios: [],
  medications: [],
  latest_iot: {},
  stats: {},
  called: { triage: null, doctor: null },
  active_triage_appointment_id: null,
  storage: "sqlite",
  mlInfo: null,
  mlDashboard: null,
};

const ROLE = {
  admin: ["reception", "cashier", "triage", "doctor", "pharmacy", "admin"],
  reception: ["reception"],
  cashier: ["cashier"],
  triage: ["triage"],
  doctor: ["doctor"],
  pharmacy: ["pharmacy"],
};

const PAYMENT_METHODS = ["Efectivo", "Tarjeta", "Yape/Plin", "Transferencia"];
const API_IDENTITY_FIELDS = ["first_name", "last_name", "birth_date", "age", "sex"];
const API_IDENTITY_FORMS = ["reception-form", "admin-patient-form", "worker-form"];

let currentUser = null;
let activeView = "reception";
let selectedTriageId = null;
let selectedConsultationId = null;
let toastTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  const isDisplay = location.pathname === "/display";
  try {
    currentUser = JSON.parse(localStorage.getItem("clinic_user"));
  } catch (error) {
    currentUser = null;
  }

  if (isDisplay) {
    document.body.classList.add("public-display");
    document.getElementById("sidebar").style.display = "none";
    switchView("display", true);
    loadState();
    setInterval(loadState, 4000);
    return;
  }

  if (!currentUser) {
    location.href = "/login";
    return;
  }

  document.getElementById("user-label").textContent = `${currentUser.full_name} - ${roleName(currentUser.role)}`;
  bindNavigation();
  bindFormEnhancements();
  filterViewsByRole();
  showPendingToast();
  activeView = localStorage.getItem("clinic_redirect") || firstAllowedView();
  localStorage.removeItem("clinic_redirect");
  switchView(activeView, true);
  loadState();
  setInterval(loadState, 5000);
});

function firstAllowedView() {
  return (ROLE[currentUser.role] || ["reception"])[0];
}

function roleName(role) {
  return {
    admin: "Administrador",
    reception: "Recepcion",
    cashier: "Caja",
    triage: "Enfermeria",
    doctor: "Medico",
    pharmacy: "Farmacia",
  }[role] || role;
}

function filterViewsByRole() {
  const allowed = ROLE[currentUser.role] || [];
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.hidden = !allowed.includes(button.dataset.view);
  });
}

function bindNavigation() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });
  document.querySelectorAll(".admin-tab").forEach((button) => {
    button.addEventListener("click", () => switchAdminTab(button.dataset.adminTab));
  });
  document.getElementById("logout-button").addEventListener("click", () => {
    localStorage.removeItem("clinic_user");
    localStorage.setItem("clinic_toast", "Sesion cerrada");
    location.href = "/login";
  });
  document.getElementById("refresh-button")?.addEventListener("click", loadState);
}

function bindFormEnhancements() {
  document.querySelectorAll('input[name="document"], input[name="phone"]').forEach((input) => {
    input.addEventListener("input", () => {
      const max = Number(input.getAttribute("maxlength") || 20);
      input.value = onlyDigits(input.value).slice(0, max);
      if (input.name === "document") {
        clearAutocompletedIdentity(input.closest("form"));
      }
    });
  });

  ["beforeinput", "paste", "drop", "keydown", "pointerdown"].forEach((eventName) => {
    document.addEventListener(eventName, protectApiLockedField, true);
  });
  document.addEventListener("input", restoreApiLockedField, true);
  document.addEventListener("change", restoreApiLockedField, true);

  document.querySelectorAll("[data-lookup-dni]").forEach((button) => {
    button.addEventListener("click", () => lookupDniForForm(button.dataset.lookupDni));
  });
  API_IDENTITY_FORMS.forEach((formId) => resetApiIdentityLock(document.getElementById(formId)));

  const workerRole = document.querySelector('#worker-form select[name="role"]');
  workerRole?.addEventListener("change", updateWorkerSpecialtyState);
  updateWorkerSpecialtyState();
}

function switchView(view, force = false) {
  if (!view) return;
  if (!force && currentUser && !(ROLE[currentUser.role] || []).includes(view)) return;
  activeView = view;
  document.querySelectorAll(".view").forEach((section) => section.classList.remove("is-visible"));
  document.getElementById(`view-${view}`)?.classList.add("is-visible");
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === view);
  });
  renderViews();
}

function switchAdminTab(tabName) {
  if (!tabName) return;
  document.querySelectorAll(".admin-tab").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.adminTab === tabName);
  });
  document.querySelectorAll(".admin-panel").forEach((panel) => {
    panel.classList.toggle("is-visible", panel.dataset.adminPanel === tabName);
  });
}

async function loadState() {
  try {
    const [state, specialties, called, patients, workers, consultorios, medications, mlInfo, mlDashboard] = await Promise.all([
      apiGet("/api/state"),
      apiGet("/api/specialties"),
      apiGet("/api/called"),
      apiGet("/api/patients").catch(() => ({ patients: [] })),
      apiGet("/api/workers").catch(() => ({ workers: [] })),
      apiGet("/api/consultorios").catch(() => ({ consultorios: [] })),
      apiGet("/api/medications").catch(() => ({ medications: [] })),
      apiGet("/api/ml/explain").catch(() => null),
      apiGet("/api/ml/dashboard").catch(() => null),
    ]);

    appState.specialties = specialties.specialties || state.specialties || [];
    appState.appointments = state.appointments || [];
    appState.prescriptions = state.prescriptions || [];
    appState.transactions = state.transactions || [];
    appState.latest_iot = state.latest_iot || {};
    appState.stats = state.stats || {};
    appState.storage = state.storage || "sqlite";
    appState.active_triage_appointment_id = state.active_triage_appointment_id;
    appState.called = called || { triage: null, doctor: null };
    appState.patients = patients.patients || [];
    appState.workers = workers.workers || [];
    appState.consultorios = consultorios.consultorios || [];
    appState.medications = medications.medications || [];
    appState.mlInfo = mlInfo;
    appState.mlDashboard = mlDashboard;
    updateWorkerSpecialtyState();

    document.getElementById("server-status")?.classList.add("is-online");
    setText("last-sync", `Actualizado ${new Date().toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })}`);
    renderViews();
  } catch (error) {
    document.getElementById("server-status")?.classList.remove("is-online");
    showToast("No se pudo sincronizar el sistema", "error");
  }
}

function renderViews() {
  renderDashboard();
  renderReception();
  renderCashier();
  renderTriage();
  renderDoctor();
  renderPharmacy();
  renderAdmin();
  renderMlOverview();
  renderDisplay();
}

function renderDashboard() {
  const stats = appState.stats;
  html("metric-grid", [
    metric("Ingresos", money(totalRevenue())),
    metric("Citas", stats.registered || 0),
    metric("Pend. pago", stats.pending_payment || 0),
    metric("Pend. triaje", stats.waiting_triage || 0),
    metric("Pend. consulta", stats.waiting_consultation || 0),
    metric("Farmacia", stats.pending_pharmacy || 0),
  ].join(""));

  const flow = appState.appointments.filter((item) => item.status !== "completed").slice(0, 10);
  html("active-flow-list", flow.length ? flow.map(queueAppointment).join("") : empty("Sin turnos activos"));
  renderVitals("dashboard-vitals", appState.latest_iot);
}

function renderReception() {
  html("specialty-select", appState.specialties.map((item) => {
    return `<option value="${item.id}">${escapeHtml(item.name)} - ${money(item.price)}</option>`;
  }).join(""));
  html("recent-appointments", appState.appointments.slice(0, 12).map((item) => {
    return `<tr>
      <td>${escapeHtml(item.ticket)}</td>
      <td>${escapeHtml(item.patient.full_name)}</td>
      <td>${escapeHtml(item.specialty.name)}</td>
      <td>${statusLabel(item.status)}</td>
      <td>${statusLabel(item.payment_status)}</td>
    </tr>`;
  }).join(""));
}

function renderCashier() {
  const query = value("cashier-search").toLowerCase();
  const pending = appState.appointments.filter((item) => item.payment_status === "pending").filter((item) => matchesAppointment(item, query));
  const paid = appState.appointments.filter((item) => item.payment_status === "paid").slice(0, 8);
  const transactions = appState.transactions.filter((item) => item.module === "cashier").slice(0, 10);

  html("cashier-pending", pending.length ? pending.map((item) => `
    <article class="queue-card">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · ${money(item.specialty.price)}</span>
      </div>
      <div class="card-actions payment-actions">
        ${paymentMethodSelect()}
        <button class="primary-button" data-pay="${item.id}" type="button">Cobrar</button>
      </div>
    </article>
  `).join("") : empty("No hay pagos pendientes"));

  html("cashier-paid", paid.length ? paid.map((item) => `
    <article class="queue-card">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.receipt_code || "Sin comprobante")} · ${money(item.specialty.price)}</span>
      </div>
      ${statusLabel("paid")}
    </article>
  `).join("") : empty("Aun no hay pagos confirmados"));
  html("cashier-transactions", renderTransactions(transactions));
}

function renderTriage() {
  const queue = appState.appointments.filter((item) => ["waiting", "in_progress"].includes(item.triage_status));
  selectedTriageId = selectedTriageId || Number(appState.active_triage_appointment_id) || null;
  html("triage-queue", queue.length ? queue.map((item) => `
    <article class="queue-card ${Number(selectedTriageId) === Number(item.id) ? "is-selected" : ""}">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · ${statusText(item.triage_status)}</span>
      </div>
      <div class="card-actions">
        <button class="secondary-button" data-call-triage="${item.id}" type="button">Llamar</button>
        <button class="primary-button" data-start-triage="${item.id}" type="button">Capturar</button>
      </div>
    </article>
  `).join("") : empty("No hay pacientes para triaje"));

  const active = appointmentById(selectedTriageId);
  setText("active-triage-pill", active ? `${active.ticket} · ${active.patient.full_name}` : "Sin paciente activo");
  document.getElementById("capture-triage-button").disabled = !active;
}

function renderDoctor() {
  const queue = appState.appointments.filter((item) => item.consultation_status === "waiting");
  html("doctor-queue", queue.length ? queue.map((item) => `
    <article class="queue-card ${Number(selectedConsultationId) === Number(item.id) ? "is-selected" : ""}">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · ${escapeHtml(item.room || "Sin consultorio")}</span>
      </div>
      <div class="card-actions">
        <button class="secondary-button" data-call-doctor="${item.id}" type="button">Llamar</button>
        <button class="primary-button" data-select-consultation="${item.id}" type="button">Iniciar</button>
      </div>
    </article>
  `).join("") : empty("No hay pacientes por atender"));

  const active = appointmentById(selectedConsultationId);
  setText("doctor-active-pill", active ? `${active.ticket} · ${active.patient.full_name}` : "Seleccione un paciente");
  html("doctor-patient-summary", active ? consultationMlSummary(active) : empty("Seleccione un paciente para revisar su triaje."));
}

function renderPharmacy() {
  const query = value("pharmacy-search").toLowerCase();
  const medQuery = value("medication-search").toLowerCase();
  const pending = appState.prescriptions.filter((item) => item.status === "pending").filter((item) => {
    return !query || [item.ticket, item.patient_name, item.patient_document].join(" ").toLowerCase().includes(query);
  });
  const done = appState.prescriptions.filter((item) => item.status === "dispensed").slice(0, 8);
  const medications = appState.medications.filter((item) => !medQuery || item.name.toLowerCase().includes(medQuery));
  const transactions = appState.transactions.filter((item) => item.module === "pharmacy").slice(0, 8);

  html("pharmacy-pending", pending.length ? pending.map(prescriptionCard).join("") : empty("No hay recetas pendientes"));
  html("pharmacy-done", done.length ? done.map((item) => `
    <article class="queue-card">
      <div><strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient_name)}</strong><span>${money(item.total)} · Entregado</span></div>
      ${statusLabel("dispensed")}
    </article>
  `).join("") : empty("Aun no hay entregas"));
  html("pharmacy-medications", medications.length ? medications.map((item) => `
    <article class="queue-card compact">
      <div><strong>${escapeHtml(item.name)}</strong><span>${money(item.price)} · Stock ${item.stock}</span></div>
    </article>
  `).join("") : empty("Sin medicamentos"));
  html("pharmacy-transactions", renderTransactions(transactions));
}

function renderAdmin() {
  if (!currentUser || currentUser.role !== "admin") return;
  html("admin-metric-grid", [
    metric("Ingresos totales", money(totalRevenue())),
    metric("Citas pendientes", pendingAdminAppointments().length),
    metric("Pacientes", appState.patients.length),
    metric("Trabajadores", appState.workers.length),
    metric("Consultorios", appState.consultorios.length),
    metric("Medicamentos", appState.medications.length),
  ].join(""));
  html("admin-pending-appointments", renderAdminPendingAppointments());
  html("admin-revenue-list", renderAdminRevenueList());
  html("admin-patients-list", adminRows(appState.patients, "patient", (item) => `${item.document} · ${item.first_name} ${item.last_name}`, (item) => `${item.age} anos · ${item.phone || "Sin telefono"}`));
  html("admin-workers-list", adminRows(appState.workers, "worker", (item) => `${item.document} · ${item.first_name} ${item.last_name}`, (item) => `${roleName(item.role)} · ${item.specialty || "Sin especialidad"}`));
  html("admin-consultorios-list", adminRows(appState.consultorios, "consultorio", (item) => item.name, (item) => `${item.floor || "Sin piso"} · ${item.equipment || "Sin equipos"}`));
  html("admin-medications-list", adminRows(appState.medications, "medication", (item) => item.name, (item) => `${money(item.price)} · Stock ${item.stock}`));
}

function pendingAdminAppointments() {
  return appState.appointments.filter((item) => {
    return item.payment_status === "pending"
      || ["waiting", "in_progress"].includes(item.triage_status)
      || item.consultation_status === "waiting"
      || item.pharmacy_status === "pending";
  });
}

function renderAdminPendingAppointments() {
  const items = pendingAdminAppointments().slice(0, 8);
  if (!items.length) return empty("No hay citas pendientes");
  return items.map((item) => `
    <article class="queue-card">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · Pago: ${statusText(item.payment_status)} · Triaje: ${statusText(item.triage_status)} · Consulta: ${statusText(item.consultation_status)} · Farmacia: ${statusText(item.pharmacy_status)}</span>
      </div>
      ${statusLabel(item.status)}
    </article>
  `).join("");
}

function renderAdminRevenueList() {
  const paidAppointments = appState.appointments
    .filter((item) => item.payment_status === "paid")
    .map((item) => ({
      label: `${item.ticket} - ${item.patient.full_name}`,
      detail: `Consulta ${item.specialty.name}`,
      amount: Number(item.specialty.price || 0),
      date: item.paid_at || item.created_at,
    }));
  const pharmacy = appState.prescriptions
    .filter((item) => item.status === "dispensed")
    .map((item) => ({
      label: `${item.ticket} - ${item.patient_name}`,
      detail: "Farmacia",
      amount: Number(item.total || 0),
      date: item.dispensed_at || item.created_at,
    }));
  const items = paidAppointments.concat(pharmacy).sort((a, b) => String(b.date).localeCompare(String(a.date))).slice(0, 8);
  if (!items.length) return empty("Aun no hay ingresos registrados");
  return items.map((item) => `
    <article class="queue-card">
      <div><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.detail)}</span></div>
      <strong>${money(item.amount)}</strong>
    </article>
  `).join("");
}

function renderMlOverview() {
  html("admin-ml-list", renderMlModelCards());
  html("admin-ml-insights", renderMlInsights());
  renderMlCharts();
}

function renderMlModelCards() {
  const info = appState.mlInfo;
  const cards = [
    {
      title: "Regresion lineal",
      value: info ? `PA = ${info.linear_regression.slope} x FC + ${info.linear_regression.intercept}` : "Presion por FC",
      detail: "Estima la presion sistolica esperada desde el ritmo cardiaco capturado por IoT.",
    },
    {
      title: "Regresion lineal multiple",
      value: info ? `${info.multiple_linear_regression.coefficients.length} coeficientes` : "Tiempo de consulta",
      detail: "Calcula minutos probables de consulta usando edad, signos vitales e IMC.",
    },
    {
      title: "Regresion logistica",
      value: info ? `${info.logistic_regression.weights.length} pesos` : "Riesgo clinico",
      detail: "Devuelve la probabilidad de riesgo para apoyar la priorizacion del paciente.",
    },
    {
      title: "Arbol de decision",
      value: info ? info.decision_tree.classes.join(" / ") : "Prioridad",
      detail: "Clasifica el turno como emergencia, urgente, preferente o rutina.",
    },
  ];
  return cards.map((card) => `
    <article class="ml-card">
      <span>${escapeHtml(card.title)}</span>
      <strong>${escapeHtml(card.value)}</strong>
      <p>${escapeHtml(card.detail)}</p>
    </article>
  `).join("");
}

function renderMlCharts() {
  const data = appState.mlDashboard || {};
  renderBarChart("ml-priority-chart", data.priority_distribution || []);
  renderBarChart("ml-risk-chart", data.risk_distribution || []);
  renderRegressionChart("ml-regression-chart", data.linear_regression_points || []);
  renderAttentionChart("ml-attention-chart", data.multiple_regression_points || []);
}

function renderMlInsights() {
  const summary = appState.mlDashboard?.summary;
  if (!summary) return empty("Sin indicadores predictivos disponibles");
  const urgentRate = Math.round(Number(summary.urgent_rate || 0));
  const risk = Math.round(Number(summary.average_risk || 0));
  const minutes = Number(summary.average_attention_minutes || 0).toFixed(1);
  return `
    <article class="insight-strip">
      <div><span>Muestra</span><strong>${summary.samples}</strong><small>${escapeHtml(summary.source || "")}</small></div>
      <div><span>Riesgo promedio</span><strong>${risk}%</strong><small>Regresion logistica</small></div>
      <div><span>Tiempo estimado</span><strong>${minutes} min</strong><small>Regresion multiple</small></div>
      <div><span>Casos urgentes</span><strong>${urgentRate}%</strong><small>Arbol de decision</small></div>
    </article>
    <div class="decision-note">${escapeHtml(summary.insight || "El panel traduce los modelos en acciones operativas.")}</div>
  `;
}

function renderDisplay() {
  const triage = appState.called.triage;
  const doctor = appState.called.doctor;
  setText("display-triage-ticket", triage?.ticket || "--");
  setText("display-triage-name", triage?.patient?.full_name || "Sin llamado");
  setText("display-doctor-ticket", doctor?.ticket || "--");
  setText("display-doctor-name", doctor?.patient?.full_name || "Sin llamado");
  const next = appState.appointments.filter((item) => item.payment_status === "paid" && item.status !== "completed").slice(0, 8);
  html("display-next-list", next.length ? next.map((item) => `
    <div class="display-next"><strong>${escapeHtml(item.ticket)}</strong><span>${escapeHtml(item.patient.full_name)}</span><small>${escapeHtml(item.specialty.name)}</small></div>
  `).join("") : "");
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button, [data-select-patient]");
  if (!button) return;

  try {
    if (button.dataset.pay) {
      await apiPost(`/api/appointments/${button.dataset.pay}/pay`, {
        payment_method: selectedPaymentMethod(button),
        created_by: currentUser?.username || "",
      });
      showToast("Cobro realizado", "success");
      await loadState();
    } else if (button.dataset.callTriage) {
      await apiPost(`/api/appointments/${button.dataset.callTriage}/call`, { target: "triage" });
      showToast("Paciente llamado a triaje", "success");
      await loadState();
    } else if (button.dataset.startTriage) {
      await apiPost(`/api/triage/${button.dataset.startTriage}/activate`);
      selectedTriageId = Number(button.dataset.startTriage);
      syncIoTToForm();
      showToast("Paciente activo para triaje", "success");
      await loadState();
    } else if (button.dataset.callDoctor) {
      await apiPost(`/api/appointments/${button.dataset.callDoctor}/call`, { target: "doctor" });
      showToast("Paciente llamado a consultorio", "success");
      await loadState();
    } else if (button.dataset.selectConsultation) {
      selectedConsultationId = Number(button.dataset.selectConsultation);
      showToast("Consulta iniciada", "success");
      renderDoctor();
    } else if (button.dataset.dispense) {
      await apiPost(`/api/prescriptions/${button.dataset.dispense}/dispense`, {
        payment_method: selectedPaymentMethod(button),
        created_by: currentUser?.username || "",
      });
      showToast("Cobro y entrega registrados", "success");
      await loadState();
    } else if (button.id === "sync-iot-button") {
      syncIoTToForm();
    } else if (button.id === "add-medicine-button") {
      addMedicineRow();
      showToast("Medicamento agregado", "success");
    } else if (button.id === "clear-reception-form") {
      const form = document.getElementById("reception-form");
      form.reset();
      resetApiIdentityLock(form);
      showToast("Formulario limpio", "info");
    } else if (button.dataset.selectPatient) {
      const form = document.getElementById("reception-form");
      fillForm("reception-form", patientById(button.dataset.selectPatient));
      setIdentityLocked(form, true);
      showToast("Paciente cargado", "success");
    } else if (button.dataset.edit) {
      editAdmin(button.dataset.edit, button.dataset.id);
      showToast("Registro cargado para editar", "info");
    } else if (button.dataset.delete) {
      await deleteAdmin(button.dataset.delete, button.dataset.id);
      await loadState();
    } else if (button.dataset.clearForm) {
      const form = document.getElementById(button.dataset.clearForm);
      form.reset();
      resetApiIdentityLock(form);
      updateWorkerSpecialtyState();
      showToast("Formulario limpio", "info");
    } else if (button.dataset.removeMedicine) {
      button.closest(".medicine-row")?.remove();
      showToast("Medicamento retirado", "info");
    }
  } catch (error) {
    showToast(error.message || "No se pudo completar la accion", "error");
  }
});

document.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  try {
    if (form.id === "reception-form") {
      validateClinicForm(form);
      await apiPost("/api/appointments", formData(form));
      form.reset();
      resetApiIdentityLock(form);
      showToast("Cita registrada", "success");
      await loadState();
    } else if (form.id === "vitals-form") {
      if (!selectedTriageId) throw new Error("Seleccione un paciente para triaje");
      const data = { vitals: formData(form), source: "IoT simulado" };
      const result = await apiPost(`/api/triage/${selectedTriageId}/capture`, data);
      html("triage-analysis", analysisMlBox(result.analysis));
      selectedTriageId = null;
      form.reset();
      showToast("Triaje guardado", "success");
      await loadState();
    } else if (form.id === "consultation-form") {
      if (!selectedConsultationId) throw new Error("Seleccione un paciente");
      const data = formData(form);
      data.prescription_items = prescriptionItems();
      await apiPost(`/api/consultations/${selectedConsultationId}`, data);
      selectedConsultationId = null;
      form.reset();
      html("medicine-list", "");
      showToast("Consulta registrada", "success");
      await loadState();
    } else if (["admin-patient-form", "worker-form", "consultorio-form", "medication-form"].includes(form.id)) {
      validateClinicForm(form);
      await saveAdmin(form);
      form.reset();
      resetApiIdentityLock(form);
      updateWorkerSpecialtyState();
      await loadState();
    }
  } catch (error) {
    showToast(error.message || "No se pudo guardar", "error");
  }
});

document.addEventListener("input", async (event) => {
  if (["cashier-search", "pharmacy-search", "medication-search"].includes(event.target.id)) renderViews();
  if (event.target.matches('#worker-form select[name="role"]')) updateWorkerSpecialtyState();
  if (event.target.id === "patient-search") {
    const query = event.target.value.trim();
    if (query.length < 2) {
      html("patient-search-results", "");
      return;
    }
    const data = await apiGet(`/api/patients/search?q=${encodeURIComponent(query)}`);
    html("patient-search-results", (data.patients || []).map((patient) => `
      <article class="queue-card" data-select-patient="${patient.id}">
        <div><strong>${escapeHtml(patient.first_name)} ${escapeHtml(patient.last_name)}</strong><span>${escapeHtml(patient.document)} · ${patient.age} anos</span></div>
      </article>
    `).join("") || empty("Sin resultados"));
  }
});

async function saveAdmin(form) {
  const data = formData(form);
  const id = data.id;
  delete data.id;
  const config = {
    "admin-patient-form": ["/api/patients", "patient"],
    "worker-form": ["/api/workers", "worker"],
    "consultorio-form": ["/api/consultorios", "consultorio"],
    "medication-form": ["/api/medications", "medication"],
  }[form.id];
  const url = id ? `${config[0]}/${id}` : config[0];
  await apiJson(url, { method: id ? "PUT" : "POST", body: data });
  showToast(id ? "Registro actualizado" : "Registro creado", "success");
}

async function deleteAdmin(type, id) {
  const urls = {
    patient: "/api/patients",
    worker: "/api/workers",
    consultorio: "/api/consultorios",
    medication: "/api/medications",
  };
  await apiJson(`${urls[type]}/${id}`, { method: "DELETE" });
  showToast(type === "patient" ? "Paciente dado de baja" : "Registro eliminado", "success");
}

function editAdmin(type, id) {
  const maps = {
    patient: ["admin-patient-form", appState.patients],
    worker: ["worker-form", appState.workers],
    consultorio: ["consultorio-form", appState.consultorios],
    medication: ["medication-form", appState.medications],
  };
  const [formId, collection] = maps[type];
  fillForm(formId, collection.find((item) => Number(item.id) === Number(id)));
  setIdentityLocked(document.getElementById(formId), true);
  if (formId === "worker-form") updateWorkerSpecialtyState();
}

function addMedicineRow(item = {}) {
  const options = appState.medications.map((med) => {
    return `<option value="${escapeHtml(med.name)}" data-price="${med.price}">${escapeHtml(med.name)} - ${money(med.price)}</option>`;
  }).join("");
  document.getElementById("medicine-list").insertAdjacentHTML("beforeend", `
    <div class="medicine-row">
      <label>Medicamento<select name="medicine">${options}</select></label>
      <label>Dosis<input name="dosage" value="${escapeHtml(item.dosage || "1 tableta")}" /></label>
      <label>Frecuencia<input name="frequency" value="${escapeHtml(item.frequency || "Cada 8 horas")}" /></label>
      <label>Dias<input name="days" type="number" value="${item.days || 3}" /></label>
      <label>Cant.<input name="quantity" type="number" value="${item.quantity || 6}" /></label>
      <label>Precio<input name="unit_price" step="0.01" type="number" value="${item.unit_price || medicationPrice(appState.medications[0])}" /></label>
      <button class="danger-button" data-remove-medicine="1" type="button">Quitar</button>
    </div>
  `);
}

function prescriptionItems() {
  return Array.from(document.querySelectorAll("#medicine-list .medicine-row")).map((row) => {
    const item = {};
    row.querySelectorAll("input, select").forEach((field) => {
      item[field.name] = field.value;
    });
    return item;
  });
}

function syncIoTToForm() {
  const form = document.getElementById("vitals-form");
  Object.entries(appState.latest_iot || {}).forEach(([key, value]) => {
    if (form.elements[key]) form.elements[key].value = value;
  });
  showToast("Signos IoT cargados", "success");
}

function fillForm(formId, data) {
  if (!data) return;
  const form = document.getElementById(formId);
  Object.entries(data).forEach(([key, value]) => {
    if (form.elements[key]) form.elements[key].value = value ?? "";
  });
}

function adminRows(items, type, title, subtitle) {
  return items.length ? items.map((item) => `
    <article class="queue-card">
      <div><strong>${escapeHtml(title(item))}</strong><span>${escapeHtml(subtitle(item))}</span></div>
      <div class="card-actions">
        <button class="secondary-button" data-edit="${type}" data-id="${item.id}" type="button">Editar</button>
        <button class="danger-button" data-delete="${type}" data-id="${item.id}" type="button">Eliminar</button>
      </div>
    </article>
  `).join("") : empty("Sin registros");
}

function prescriptionCard(item) {
  const rows = (item.items || []).map((med) => {
    return `<li>${escapeHtml(med.medicine)} · ${escapeHtml(med.dosage)} · ${escapeHtml(med.frequency)} · ${med.quantity} und. · ${money(med.unit_price * med.quantity)}</li>`;
  }).join("");
  return `<article class="queue-card prescription-card">
    <div>
      <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient_name)}</strong>
      <span>DNI ${escapeHtml(item.patient_document)} · ${escapeHtml(item.diagnosis || "Sin diagnostico")}</span>
      <ul>${rows}</ul>
      <b>Total: ${money(item.total)}</b>
    </div>
    <div class="card-actions payment-actions">
      ${paymentMethodSelect()}
      <button class="primary-button" data-dispense="${item.id}" type="button">Cobrar y entregar</button>
    </div>
  </article>`;
}

function renderTransactions(items) {
  if (!items.length) return empty("Sin transacciones registradas");
  return items.map((item) => `
    <article class="queue-card compact transaction-card">
      <div>
        <strong>${escapeHtml(item.transaction_code)} - ${escapeHtml(item.patient_name)}</strong>
        <span>${escapeHtml(item.concept)} Â· ${escapeHtml(item.payment_method)} Â· ${formatDateTime(item.created_at)}</span>
      </div>
      <strong>${money(item.amount)}</strong>
    </article>
  `).join("");
}

function queueAppointment(item) {
  return `<article class="queue-card">
    <div><strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong><span>${escapeHtml(item.specialty.name)} · ${statusText(item.status)}</span></div>
    ${statusLabel(item.payment_status)}
  </article>`;
}

function consultationMlSummary(item) {
  const triage = item.triage;
  if (!triage) return empty("Paciente sin triaje registrado.");
  const analysis = triage.analysis || {};
  return `<div class="summary-grid">
    <span>Prioridad</span><strong>${escapeHtml(triage.priority)}</strong>
    <span>Riesgo</span><strong>${escapeHtml(triage.risk_label)}</strong>
    <span>Signos</span><strong>${triage.temperature} C - FC ${triage.heart_rate} - SpO2 ${triage.spo2}% - PA ${triage.systolic}/${triage.diastolic}</strong>
    <span>ML</span><strong>PA esperada ${analysis.predicted_systolic ?? triage.predicted_systolic} - Consulta ${analysis.estimated_attention_minutes ?? triage.estimated_attention_minutes} min</strong>
    <span>Decision</span><strong>${escapeHtml(triage.decision_summary)}</strong>
  </div>`;
}

function analysisMlBox(analysis) {
  if (!analysis) return "";
  return `<div class="summary-grid">
      <span>Prioridad</span><strong>${escapeHtml(analysis.priority)}</strong>
      <span>Riesgo</span><strong>${escapeHtml(analysis.risk_label)} (${Math.round(analysis.risk_probability * 100)}%)</strong>
      <span>IMC</span><strong>${analysis.bmi}</strong>
      <span>Decision</span><strong>${escapeHtml(analysis.decision_summary)}</strong>
    </div>
    <div class="ml-result-grid">
      <div><span>Regresion lineal</span><strong>PA sistolica esperada: ${analysis.predicted_systolic}</strong></div>
      <div><span>Regresion lineal multiple</span><strong>Consulta estimada: ${analysis.estimated_attention_minutes} min</strong></div>
      <div><span>Regresion logistica</span><strong>Probabilidad de riesgo: ${Math.round(analysis.risk_probability * 100)}%</strong></div>
      <div><span>Arbol de decision</span><strong>Prioridad: ${escapeHtml(analysis.priority)}</strong></div>
    </div>`;
}

function consultationSummary(item) {
  const triage = item.triage;
  if (!triage) return empty("Paciente sin triaje registrado.");
  return `<div class="summary-grid">
    <span>Prioridad</span><strong>${escapeHtml(triage.priority)}</strong>
    <span>Riesgo</span><strong>${escapeHtml(triage.risk_label)}</strong>
    <span>Signos</span><strong>${triage.temperature} C · FC ${triage.heart_rate} · SpO2 ${triage.spo2}% · PA ${triage.systolic}/${triage.diastolic}</strong>
    <span>Decision</span><strong>${escapeHtml(triage.decision_summary)}</strong>
  </div>`;
}

function analysisBox(analysis) {
  if (!analysis) return "";
  return `<div class="summary-grid">
    <span>Prioridad</span><strong>${escapeHtml(analysis.priority)}</strong>
    <span>Riesgo</span><strong>${escapeHtml(analysis.risk_label)} (${Math.round(analysis.risk_probability * 100)}%)</strong>
    <span>IMC</span><strong>${analysis.bmi}</strong>
    <span>Decision</span><strong>${escapeHtml(analysis.decision_summary)}</strong>
  </div>`;
}

function renderVitals(targetId, vitals) {
  const items = [
    ["Temp.", `${vitals.temperature ?? "--"} C`],
    ["FC", `${vitals.heart_rate ?? "--"} lpm`],
    ["SpO2", `${vitals.spO2 ?? "--"}%`],
    ["PA", `${vitals.blood_pressure_systolic ?? "--"}/${vitals.blood_pressure_diastolic ?? "--"}`],
    ["Peso", `${vitals.weight ?? "--"} kg`],
    ["Talla", `${vitals.height ?? "--"} cm`],
  ];
  html(targetId, items.map(([label, valueText]) => `<div class="vital-chip"><span>${label}</span><strong>${valueText}</strong></div>`).join(""));
}

function metric(label, valueText) {
  return `<div class="metric-card"><span>${label}</span><strong>${valueText}</strong></div>`;
}

function totalRevenue() {
  const appointments = appState.appointments
    .filter((item) => item.payment_status === "paid")
    .reduce((sum, item) => sum + Number(item.specialty.price || 0), 0);
  const pharmacy = appState.prescriptions
    .filter((item) => item.status === "dispensed")
    .reduce((sum, item) => sum + Number(item.total || 0), 0);
  return appointments + pharmacy;
}

function matchesAppointment(item, query) {
  return !query || [item.ticket, item.patient.full_name, item.patient.document, item.specialty.name].join(" ").toLowerCase().includes(query);
}

function appointmentById(id) {
  return appState.appointments.find((item) => Number(item.id) === Number(id));
}

function patientById(id) {
  return appState.patients.find((item) => Number(item.id) === Number(id));
}

function medicationPrice(item) {
  return item ? Number(item.price || 0).toFixed(2) : "0.00";
}

function paymentMethodSelect(name = "payment_method") {
  return `<label class="payment-select">Metodo
    <select name="${name}">
      ${PAYMENT_METHODS.map((method) => `<option value="${escapeHtml(method)}">${escapeHtml(method)}</option>`).join("")}
    </select>
  </label>`;
}

function selectedPaymentMethod(button) {
  return button.closest(".queue-card")?.querySelector('select[name="payment_method"]')?.value || "Efectivo";
}

function transactionFor(module, referenceType, referenceId) {
  return appState.transactions.find((item) => {
    return item.module === module
      && item.reference_type === referenceType
      && Number(item.reference_id) === Number(referenceId);
  });
}

function statusText(valueText) {
  return {
    registered: "Registrado",
    pending: "Pendiente",
    paid: "Pagado",
    waiting: "En espera",
    in_progress: "En proceso",
    done: "Completado",
    not_started: "No iniciado",
    triaged: "Triaje listo",
    prescription_pending: "Receta pendiente",
    completed: "Finalizado",
    dispensed: "Entregado",
    none: "No aplica",
  }[valueText] || valueText || "--";
}

function statusLabel(valueText) {
  const good = ["paid", "done", "completed", "dispensed"];
  const warn = ["pending", "waiting", "registered", "prescription_pending"];
  const type = good.includes(valueText) ? "ok" : warn.includes(valueText) ? "pending" : "info";
  return `<span class="status-label status-${type}">${statusText(valueText)}</span>`;
}

async function lookupDniForForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  const dni = onlyDigits(form.elements.document.value);
  if (dni.length !== 8) {
    showToast("Ingrese un DNI de 8 digitos", "warning");
    form.elements.document.focus();
    return;
  }

  const button = document.querySelector(`[data-lookup-dni="${formId}"]`);
  button.disabled = true;
  try {
    const data = await apiGet(`/api/dni/${dni}`);
    applyIdentityData(form, data.person || data.patient || {});
    showToast("Datos encontrados y bloqueados", "success");
  } catch (error) {
    showToast(error.message || "No se pudo buscar el DNI", "error");
  } finally {
    button.disabled = false;
  }
}

function applyIdentityData(form, person) {
  if (!form) return;
  const identity = { ...person };
  if (!identity.age && identity.birth_date) identity.age = calculateAge(identity.birth_date) || "";
  API_IDENTITY_FIELDS.forEach((fieldName) => {
    const field = form.elements[fieldName];
    const nextValue = identity[fieldName];
    if (!field || nextValue === undefined || nextValue === null || nextValue === "") return;
    field.value = nextValue;
  });
  setIdentityLocked(form, false);
  setIdentityLocked(form, true, API_IDENTITY_FIELDS);
}

function setIdentityLocked(form, locked, fields = null) {
  if (!form) return;
  const targetFields = fields || API_IDENTITY_FIELDS;
  targetFields.forEach((fieldName) => {
    const field = form.elements[fieldName];
    if (!field) return;
    if (locked) {
      field.dataset.apiLocked = "true";
      field.dataset.apiLockedValue = field.value;
      field.setAttribute("aria-disabled", "true");
      if (field.tagName !== "SELECT") field.readOnly = true;
    } else {
      delete field.dataset.apiLocked;
      delete field.dataset.apiLockedValue;
      field.removeAttribute("aria-disabled");
      field.readOnly = false;
    }
    field.classList.toggle("is-readonly", locked);
  });
  if (locked) {
    form.dataset.identityLocked = targetFields.join(",");
  } else if (!fields) {
    delete form.dataset.identityLocked;
  }
}

function clearAutocompletedIdentity(form) {
  if (!form || !API_IDENTITY_FORMS.includes(form.id)) return;
  API_IDENTITY_FIELDS.forEach((fieldName) => {
    const field = form.elements[fieldName];
    if (!field) return;
    field.value = fieldName === "sex" ? "No especificado" : "";
  });
  resetApiIdentityLock(form);
}

function resetApiIdentityLock(form) {
  if (!form || !API_IDENTITY_FORMS.includes(form.id)) return;
  setIdentityLocked(form, false);
  setIdentityLocked(form, true, API_IDENTITY_FIELDS);
}

function protectApiLockedField(event) {
  const field = event.target;
  if (!field?.dataset?.apiLocked) return;
  if (event.type === "pointerdown" && field.tagName !== "SELECT") return;
  if (event.type === "keydown" && isAllowedLockedFieldKey(event)) return;
  event.preventDefault();
  restoreApiLockedField(event);
}

function restoreApiLockedField(event) {
  const field = event.target;
  if (!field?.dataset?.apiLocked) return;
  const lockedValue = field.dataset.apiLockedValue ?? "";
  if (field.value !== lockedValue) field.value = lockedValue;
}

function isAllowedLockedFieldKey(event) {
  const allowedKeys = ["Tab", "Shift", "Control", "Alt", "Meta", "Escape", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"];
  return allowedKeys.includes(event.key) || event.ctrlKey || event.metaKey || event.altKey;
}

function updateWorkerSpecialtyState() {
  const form = document.getElementById("worker-form");
  if (!form) return;
  const field = form.querySelector(".worker-specialty-field");
  const specialty = form.elements.specialty;
  const isDoctor = form.elements.role.value === "doctor";
  const currentValue = specialty.value;
  specialty.innerHTML = workerSpecialtyOptions();
  specialty.disabled = !isDoctor;
  specialty.required = isDoctor;
  if (isDoctor && currentValue) specialty.value = currentValue;
  if (!isDoctor) specialty.value = "";
  field?.classList.toggle("is-disabled", !isDoctor);
}

function workerSpecialtyOptions() {
  const options = appState.specialties.length
    ? appState.specialties.map((item) => `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`).join("")
    : `<option value="Medicina General">Medicina General</option>`;
  return `<option value="">Seleccione especialidad</option>${options}`;
}

function validateClinicForm(form) {
  const documentInput = form.elements.document;
  const phoneInput = form.elements.phone;
  if (documentInput && onlyDigits(documentInput.value).length !== 8) {
    throw new Error("DNI debe tener 8 digitos.");
  }
  if (phoneInput && onlyDigits(phoneInput.value).length !== 9) {
    throw new Error("Telefono debe tener 9 digitos y no aceptar letras.");
  }
  if (form.id === "worker-form" && form.elements.role.value === "doctor" && !form.elements.specialty.value) {
    throw new Error("Seleccione especialidad para el medico.");
  }
  if (!form.checkValidity()) {
    form.reportValidity();
    throw new Error("Complete los campos obligatorios correctamente.");
  }
}

function renderBarChart(targetId, items) {
  const total = Math.max(1, items.reduce((sum, item) => sum + Number(item.value || 0), 0));
  html(targetId, items.map((item) => {
    const percent = Math.round((Number(item.value || 0) / total) * 100);
    return `<div class="bar-row">
      <span>${escapeHtml(item.label)}</span>
      <div class="bar-track"><i style="width:${percent}%"></i></div>
      <strong>${item.value}</strong>
    </div>`;
  }).join("") || empty("Sin datos"));
}

function renderRegressionChart(targetId, points) {
  if (!points.length) {
    html(targetId, empty("Sin datos"));
    return;
  }
  const maxValue = Math.max(...points.flatMap((point) => [point.actual_systolic, point.predicted_systolic, 1]));
  html(targetId, `<div class="paired-bars">${points.map((point) => {
    const actual = Math.round((point.actual_systolic / maxValue) * 100);
    const predicted = Math.round((point.predicted_systolic / maxValue) * 100);
    return `<div class="paired-bar">
      <small>FC ${Math.round(point.heart_rate)}</small>
      <span class="actual" style="height:${actual}%"></span>
      <span class="predicted" style="height:${predicted}%"></span>
    </div>`;
  }).join("")}</div>
  <div class="chart-legend"><span class="dot actual"></span> Real <span class="dot predicted"></span> Predicha</div>`);
}

function renderAttentionChart(targetId, points) {
  if (!points.length) {
    html(targetId, empty("Sin datos"));
    return;
  }
  const maxMinutes = Math.max(...points.map((point) => Number(point.minutes || 0)), 1);
  html(targetId, `<div class="attention-chart">${points.map((point) => {
    const height = Math.round((Number(point.minutes || 0) / maxMinutes) * 100);
    return `<div class="attention-point">
      <span style="height:${height}%"></span>
      <small>${Math.round(point.risk)}%</small>
    </div>`;
  }).join("")}</div>
  <div class="chart-legend">Barras: minutos estimados. Etiqueta: riesgo logistico.</div>`);
}

function onlyDigits(valueText) {
  return String(valueText || "").replace(/\D/g, "");
}

function calculateAge(dateText) {
  const birthDate = new Date(`${dateText}T00:00:00`);
  if (Number.isNaN(birthDate.getTime())) return "";
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDelta = today.getMonth() - birthDate.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < birthDate.getDate())) age -= 1;
  return Math.max(0, age);
}

function formData(form) {
  const data = {};
  Array.from(form.elements).forEach((field) => {
    if (!field.name || ["button", "submit", "reset"].includes(field.type)) return;
    const valueText = field.value;
    data[field.name] = ["document", "phone"].includes(field.name) ? onlyDigits(valueText) : valueText;
  });
  return data;
}

function formatDateTime(valueText) {
  if (!valueText) return "Sin fecha";
  const parsed = new Date(valueText);
  if (Number.isNaN(parsed.getTime())) return String(valueText).slice(0, 16);
  return parsed.toLocaleString("es-PE", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function apiGet(url) {
  const response = await fetch(url);
  return parseResponse(response);
}

async function apiPost(url, body = {}) {
  return apiJson(url, { method: "POST", body });
}

async function apiJson(url, options) {
  const response = await fetch(url, {
    method: options.method,
    headers: { "Content-Type": "application/json" },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  return parseResponse(response);
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || "Error del servidor");
  return data;
}

function html(id, content) {
  const element = document.getElementById(id);
  if (element) element.innerHTML = content;
}

function setText(id, text) {
  const element = document.getElementById(id);
  if (element) element.textContent = text;
}

function value(id) {
  return document.getElementById(id)?.value || "";
}

function money(valueText) {
  return `S/ ${Number(valueText || 0).toFixed(2)}`;
}

function empty(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function escapeHtml(valueText) {
  return String(valueText ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  const label = {
    success: "Correcto",
    error: "Atencion",
    warning: "Revise",
    info: "Sistema",
  }[type] || "Sistema";
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${label}</span><strong>${escapeHtml(message)}</strong>`;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

function showPendingToast() {
  const pendingToast = localStorage.getItem("clinic_toast");
  if (!pendingToast) return;
  localStorage.removeItem("clinic_toast");
  showToast(pendingToast, "success");
}
