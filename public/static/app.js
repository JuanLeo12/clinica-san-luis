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
  mlEvaluate: null,
};

const ROLE = {
  admin: ["reception", "cashier", "triage", "doctor", "pharmacy", "admin"],
  recepcion: ["reception"],
  caja: ["cashier"],
  triage: ["triage"],
  medico: ["doctor"],
  farmacia: ["pharmacy"],
};

const PAYMENT_METHODS = ["Efectivo", "Tarjeta", "Yape/Plin", "Transferencia"];
const API_IDENTITY_FIELDS = [
  "first_name",
  "last_name",
  "birth_date",
  "age",
  "sex",
];
const API_IDENTITY_FORMS = [
  "reception-form",
  "admin-patient-form",
  "worker-form",
];

let currentUser = null;
let activeView = "reception";
let selectedTriageId = null;
let selectedConsultationId = null;
let selectedClinicalHistoryPatientId = null;
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

  document.getElementById("user-label").textContent =
    `${currentUser.full_name} - ${roleName(currentUser.role)}`;
  bindNavigation();
  bindFormEnhancements();
  bindMlButtons();
  filterViewsByRole();
  showPendingToast();
  activeView = localStorage.getItem("clinic_redirect") || firstAllowedView();
  localStorage.removeItem("clinic_redirect");
  switchView(activeView, true);
  loadState();
  setInterval(loadState, 5000);

  // Configurar filtros de busqueda
  setupSearchFilters();
});

function setupSearchFilters() {
  const searchPatients = document.getElementById("search-patients");
  const searchWorkers = document.getElementById("search-workers");
  const searchRooms = document.getElementById("search-rooms");
  const searchMedications = document.getElementById("search-medications");

  if (searchPatients) {
    searchPatients.addEventListener("input", () => filterTable("admin-patients-list", searchPatients.value));
  }
  if (searchWorkers) {
    searchWorkers.addEventListener("input", () => filterCards("admin-workers-list", searchWorkers.value));
  }
  if (searchRooms) {
    searchRooms.addEventListener("input", () => filterCards("admin-consultorios-list", searchRooms.value));
  }
  if (searchMedications) {
    searchMedications.addEventListener("input", () => filterCards("admin-medications-list", searchMedications.value));
  }
  // Buscador de transacciones
  const searchTransactions = document.getElementById("admin-transactions-search");
  if (searchTransactions) {
    searchTransactions.addEventListener("input", () => renderAdminTransactions());
  }
  const filterTransactions = document.getElementById("admin-transactions-filter");
  if (filterTransactions) {
    filterTransactions.addEventListener("change", () => renderAdminTransactions());
  }
}

function filterTable(tableId, query) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const rows = table.querySelectorAll("tbody tr");
  const q = query.toLowerCase();
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = !q || text.includes(q) ? "" : "none";
  });
}

function filterCards(containerId, query) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const cards = container.querySelectorAll(".queue-card");
  const q = query.toLowerCase();
  cards.forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = !q || text.includes(q) ? "" : "none";
  });
}

function firstAllowedView() {
  return (ROLE[currentUser.role] || ["reception"])[0];
}

function roleName(role) {
  return (
    {
      admin: "Administrador",
      recepcion: "Recepcion",
      caja: "Caja",
      triage: "Enfermeria",
      medico: "Medico",
      farmacia: "Farmacia",
    }[role] || role
  );
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
    button.addEventListener("click", () =>
      switchAdminTab(button.dataset.adminTab),
    );
  });
  document.getElementById("logout-button").addEventListener("click", () => {
    localStorage.removeItem("clinic_user");
    localStorage.setItem("clinic_toast", "Sesion cerrada");
    location.href = "/login";
  });
  document
    .getElementById("refresh-button")
    ?.addEventListener("click", loadState);
}

function bindFormEnhancements() {
  document
    .querySelectorAll('input[name="document"], input[name="phone"]')
    .forEach((input) => {
      input.addEventListener("input", () => {
        const max = Number(input.getAttribute("maxlength") || 20);
        input.value = onlyDigits(input.value).slice(0, max);
        if (input.name === "document") {
          clearAutocompletedIdentity(input.closest("form"));
        }
      });
    });

  ["beforeinput", "paste", "drop", "keydown", "pointerdown"].forEach(
    (eventName) => {
      document.addEventListener(eventName, protectApiLockedField, true);
    },
  );
  document.addEventListener("input", restoreApiLockedField, true);
  document.addEventListener("change", restoreApiLockedField, true);

  // Guardar selecciones de métodos de pago cuando cambien
  document.addEventListener("change", (event) => {
    if (event.target.matches('#cashier-pending select[name="payment_method"]')) {
      const select = event.target;
      const card = select.closest('.queue-card');
      const payBtn = card?.querySelector('[data-pay]');
      if (payBtn) {
        paymentSelections[payBtn.dataset.pay] = select.value;
      }
    }
    if (event.target.matches('#pharmacy-pending select[name="payment_method"]')) {
      const select = event.target;
      const card = select.closest('.prescription-card');
      const dispenseBtn = card?.querySelector('[data-dispense]');
      if (dispenseBtn) {
        pharmacyPaymentSelections[dispenseBtn.dataset.dispense] = select.value;
      }
    }
  }, true);

  document.querySelectorAll("[data-lookup-dni]").forEach((button) => {
    button.addEventListener("click", () =>
      lookupDniForForm(button.dataset.lookupDni),
    );
  });
  API_IDENTITY_FORMS.forEach((formId) =>
    resetApiIdentityLock(document.getElementById(formId)),
  );

  const workerRole = document.querySelector('#worker-form select[name="role"]');
  workerRole?.addEventListener("change", updateWorkerSpecialtyState);
  updateWorkerSpecialtyState();
}

function switchView(view, force = false) {
  if (!view) return;
  const allowed = ROLE[currentUser.role] || [];
  if (!force && currentUser && !allowed.includes(view)) {
    // Mostrar toast de acceso denegado (excepto para admin que tiene acceso a todo)
    if (currentUser.role !== "admin") {
      showToast(`No tiene acceso a ${roleName(view)}. Contacte al administrador.`, "error");
    }
    return;
  }
  activeView = view;
  document
    .querySelectorAll(".view")
    .forEach((section) => section.classList.remove("is-visible"));
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
  // Always render transactions when switching to transactions tab
  if (tabName === "transactions") {
    renderAdminTransactions();
  }
  // Always render patient clinical history when switching to patients tab
  if (tabName === "patients") {
    html("patient-clinical-history", renderPatientClinicalHistory());
  }
}

async function loadState() {
  try {
    const [
      state,
      specialties,
      called,
      patients,
      workers,
      consultorios,
      medications,
      mlInfo,
      mlDashboard,
      mlEvaluate,
    ] = await Promise.all([
      apiGet("/api/state"),
      apiGet("/api/specialties"),
      apiGet("/api/called"),
      apiGet("/api/patients").catch(() => ({ patients: [] })),
      apiGet("/api/workers").catch(() => ({ workers: [] })),
      apiGet("/api/consultorios").catch(() => ({ consultorios: [] })),
      apiGet("/api/medications").catch(() => ({ medications: [] })),
      apiGet("/api/ml/explain").catch(() => null),
      apiGet("/api/ml/dashboard").catch(() => null),
      apiGet("/api/ml/evaluate").catch(() => null),
    ]);

    appState.specialties = specialties.specialties || state.specialties || [];
    appState.appointments = state.appointments || [];
    appState.prescriptions = state.prescriptions || [];
    console.log("DEBUG: state.transactions from API:", state.transactions ? state.transactions.length : 0);
    const newTransactions = state.transactions || [];
    appState.latest_iot = state.latest_iot || {};
    appState.stats = state.stats || {};
    appState.storage = state.storage || "sqlite";
    appState.active_triage_appointment_id = state.active_triage_appointment_id;
    appState.called = called || { triage: null, doctor: null };
    appState.patients = patients.patients || [];
    appState.workers = workers.workers || [];
    appState.consultorios = consultorios.consultorios || [];
    // Use medications from /api/state (has correct field names: name, price, stock)
    appState.medications = state.medications || [];
    appState.mlInfo = mlInfo;
    appState.mlDashboard = mlDashboard;
    appState.mlEvaluate = mlEvaluate;
    updateWorkerSpecialtyState();

    // Verificar si los datos cambiaron realmente antes de re-renderizar
    // Esto evita que el dropdown se cierre y el scroll se reinicie cada 5 segundos
    const oldAppts = appState.appointments.length;
    const oldTx = appState.transactions.length;
    const oldMeds = appState.medications.length;
    const oldRx = appState.prescriptions.length;
    const dataChanged =
      oldAppts !== (state.appointments || []).length ||
      oldTx !== newTransactions.length ||
      oldMeds !== (state.medications || []).length ||
      oldRx !== (state.prescriptions || []).length;

    appState.transactions = newTransactions;

    document.getElementById("server-status")?.classList.add("is-online");
    setText(
      "last-sync",
      `Actualizado ${new Date().toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })}`,
    );
    // Siempre re-renderizar pharmacy (para actualizar lista de recetas y transacciones)
    if (dataChanged || activeView === "pharmacy") {
      renderViews();
    }
    // Display siempre debe actualizarse en tiempo real
    if (activeView === "display") {
      renderDisplay();
    }
    // Verificar stock bajo (solo para admin y pharmacy)
    checkLowStock();
  } catch (error) {
    document.getElementById("server-status")?.classList.remove("is-online");
    showToast("Error: " + (error.message || error.error || JSON.stringify(error)), "error");
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
  html(
    "metric-grid",
    [
      metric("Ingresos", money(totalRevenue())),
      metric("Citas", stats.registered || 0),
      metric("Pend. pago", stats.pending_payment || 0),
      metric("Pend. triaje", stats.waiting_triage || 0),
      metric("Pend. consulta", stats.waiting_consultation || 0),
      metric("Farmacia", stats.pending_pharmacy || 0),
    ].join(""),
  );

  const flow = appState.appointments
    .filter((item) => item.status !== "completed")
    .slice(0, 50);
  html(
    "active-flow-list",
    flow.length
      ? flow.map(queueAppointment).join("")
      : empty("Sin turnos activos"),
  );
  renderVitals("dashboard-vitals", appState.latest_iot);
}

function queueAppointment(item) {
  return `
    <article class="queue-card">
      <div>
        <strong>${escapeHtml(item.ticket)}</strong>
        <span>${escapeHtml(item.patient.full_name)} · ${escapeHtml(item.specialty.name)}</span>
      </div>
      ${statusLabel(item.status)}
    </article>
  `;
}

function renderReception() {
  // Preservar la selección actual antes de re-renderizar
  const specialtySelect = document.getElementById("specialty-select");
  const currentSpecialty = specialtySelect?.value || "";

  html(
    "specialty-select",
    appState.specialties
      .map((item) => {
        const room = item.room ? ` (${item.room})` : "";
        return `<option value="${item.id}">${escapeHtml(item.name)}${room} - ${money(item.price)}</option>`;
      })
      .join(""),
  );

  // Restaurar la selección si existía
  if (currentSpecialty && specialtySelect) {
    specialtySelect.value = currentSpecialty;
  }

  html(
    "recent-appointments",
    appState.appointments
      .map((item) => {
        return `<tr>
      <td>${escapeHtml(item.ticket)}</td>
      <td>${escapeHtml(item.patient.full_name)}</td>
      <td>${escapeHtml(item.specialty.name)}</td>
      <td>${statusLabel(item.status)}</td>
      <td>${statusLabel(item.payment_status)}</td>
    </tr>`;
      })
      .join(""),
  );
  // Mostrar cantidad de registros
  setText("recent-appointments-count", `${appState.appointments.length} registros`);
}

// Mapa para guardar selecciones de pago por appointment ID
let paymentSelections = {};

function renderCashier() {
  // Preservar selecciones actuales antes de re-renderizar
  const existingSelects = document.querySelectorAll('#cashier-pending .queue-card');
  existingSelects.forEach(card => {
    const select = card.querySelector('select[name="payment_method"]');
    const payBtn = card.querySelector('[data-pay]');
    if (select && payBtn) {
      paymentSelections[payBtn.dataset.pay] = select.value;
    }
  });

  const query = value("cashier-search").toLowerCase();
  const pending = appState.appointments
    .filter((item) => item.payment_status === "pending")
    .filter((item) => matchesAppointment(item, query));
  const transactions = appState.transactions
    .filter((item) => item.module === "cashier");

  html(
    "cashier-pending",
    pending.length
      ? pending
          .map(
            (item) => {
              const savedMethod = paymentSelections[item.id] || "Efectivo";
              return `
    <article class="queue-card" data-cashier-card="${item.id}">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · ${money(item.specialty.price)}</span>
      </div>
      <div class="card-actions payment-actions">
        ${paymentMethodSelect("payment_method", savedMethod)}
        <button class="primary-button" data-pay="${item.id}" type="button">Cobrar</button>
      </div>
    </article>
  `;
            }
          )
          .join("")
      : empty("No hay pagos pendientes"),
  );

  // Re-attach change listeners immediately after rendering
  document.querySelectorAll('#cashier-pending .queue-card').forEach(card => {
    const select = card.querySelector('select[name="payment_method"]');
    const payBtn = card.querySelector('[data-pay]');
    if (select && payBtn) {
      select.onchange = function() {
        paymentSelections[payBtn.dataset.pay] = this.value;
      };
    }
  });

  // Contadores separados: pendientes y transacciones confirmadas
  setText("cashier-pending-count", `${pending.length} registros`);
  setText("cashier-transactions-count", `${transactions.length} registros`);
  html("cashier-transactions", renderTransactions(transactions));
}

function renderTriage() {
  const queue = appState.appointments
    .filter((item) =>
      item.payment_status === "paid" && ["waiting", "in_progress"].includes(item.triage_status),
    )
    .sort((a, b) => {
      // Ordenar por fecha_pago (FIFO - primero en pagar = primero en triaje)
      const dateA = a.fecha_pago || "";
      const dateB = b.fecha_pago || "";
      if (dateA < dateB) return -1;
      if (dateA > dateB) return 1;
      return a.id - b.id; // Si same fecha, ordenar por ID
    });
  const storedId = Number(appState.active_triage_appointment_id);
  console.log("renderTriage:", { storedId, selectedTriageId, queueLen: queue.length });
  selectedTriageId = selectedTriageId || storedId || null;
  html(
    "triage-queue",
    queue.length
      ? queue
          .map(
            (item) => `
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
  `,
          )
          .join("")
      : empty("No hay pacientes para triaje"),
  );

  const active = appointmentById(selectedTriageId);
  setText(
    "active-triage-pill",
    active
      ? `${active.ticket} · ${active.patient.full_name}`
      : "Sin paciente activo",
  );
  document.getElementById("capture-triage-button").disabled = !active;
}

function renderDoctor() {
  const queue = appState.appointments
    .filter((item) => item.consultation_status === "waiting")
    .sort((a, b) => {
      const priorityOrder = { "Emergencia": 0, "Urgente": 1, "Preferente": 2, "Rutina": 3 };
      const triageA = a.triage || {};
      const triageB = b.triage || {};
      const orderA = priorityOrder[triageA.priority] ?? 3;
      const orderB = priorityOrder[triageB.priority] ?? 3;
      if (orderA !== orderB) return orderA - orderB;
      return (triageB.risk_score || 0) - (triageA.risk_score || 0);
    });
  html(
    "doctor-queue",
    queue.length
      ? queue
          .map((item) => {
            const triage = item.triage || {};
            const priority = triage.priority || "Rutina";
            const priorityClass = {
              "Emergencia": "priority-emergency",
              "Urgente": "priority-urgent",
              "Preferente": "priority-preferential",
              "Rutina": "priority-routine"
            }[priority] || "priority-routine";
            const riskLabel = triage.risk_label || "Bajo";
            const riskPct = Math.round(Number(triage.risk_score || 0) * 100);
            const minutes = triage.estimated_attention_minutes || 15;
            return `
    <article class="queue-card ${priorityClass} ${Number(selectedConsultationId) === Number(item.id) ? "is-selected" : ""}">
      <div class="priority-header">
        <span class="priority-badge ${priorityClass}">${priority}</span>
        <span class="risk-badge">Riesgo: ${riskLabel} (${riskPct}%)</span>
      </div>
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · ${escapeHtml(item.room || "Sin consultorio")}</span>
      </div>
      <div class="ml-details">
        <div class="ml-stat">
          <span class="ml-stat-label">Urgencia IA</span>
          <span class="ml-stat-value">${riskPct}%</span>
        </div>
        <div class="ml-stat">
          <span class="ml-stat-label">Tiempo est.</span>
          <span class="ml-stat-value">${minutes} min</span>
        </div>
        ${triage.heart_rate ? `
        <div class="ml-stat">
          <span class="ml-stat-label">FC / SpO2</span>
          <span class="ml-stat-value">${triage.heart_rate} / ${triage.spo2 || "--"}</span>
        </div>
        ` : ""}
      </div>
      <div class="card-actions">
        <button class="secondary-button" data-call-doctor="${item.id}" type="button">Llamar</button>
        <button class="primary-button" data-select-consultation="${item.id}" type="button">Iniciar</button>
      </div>
    </article>
  `;})
          .join("")
      : empty("No hay pacientes por atender"),
  );

  const active = appointmentById(selectedConsultationId);
  setText(
    "doctor-active-pill",
    active
      ? `${active.ticket} · ${active.patient.full_name}`
      : "Seleccione un paciente",
  );
  html(
    "doctor-patient-summary",
    active
      ? consultationMlSummary(active)
      : empty("Seleccione un paciente para revisar su triaje."),
  );
}

function renderPharmacy() {
  // Preservar selecciones actuales de pharmacy
  document.querySelectorAll('#pharmacy-pending .prescription-card').forEach(card => {
    const select = card.querySelector('select[name="payment_method"]');
    const dispenseBtn = card.querySelector('[data-dispense]');
    if (select && dispenseBtn) {
      pharmacyPaymentSelections[dispenseBtn.dataset.dispense] = select.value;
    }
  });

  const query = value("pharmacy-search").toLowerCase();
  const medQuery = value("medication-search").toLowerCase();
  const pending = appState.prescriptions
    .filter((item) => item.status === "pending")
    .filter((item) => {
      return (
        !query ||
        [item.ticket, item.patient_name, item.patient_document]
          .join(" ")
          .toLowerCase()
          .includes(query)
      );
    });
  // Recetas dispensadas (para historial de entregas)
  const done = appState.prescriptions
    .filter((item) => item.status === "dispensed");
  // Transacciones reales de pharmacy (module=pharmacy), no recetas
  console.log("DEBUG: Total transactions:", appState.transactions.length);
  console.log("DEBUG: All transaction modules:", appState.transactions.map(t => t.module));
  const pharmacyTransactions = appState.transactions
    .filter((t) => t.module === "pharmacy");
  console.log("DEBUG: Pharmacy transactions:", pharmacyTransactions.length);
  const transactions = pharmacyTransactions;
  const medications = appState.medications.filter(
    (item) => !medQuery || item.name.toLowerCase().includes(medQuery),
  );

  html(
    "pharmacy-pending",
    pending.length
      ? pending.map(prescriptionCard).join("")
      : empty("No hay recetas pendientes"),
  );

  // Re-attach change listeners
  document.querySelectorAll('#pharmacy-pending .prescription-card').forEach(card => {
    const select = card.querySelector('select[name="payment_method"]');
    const dispenseBtn = card.querySelector('[data-dispense]');
    if (select && dispenseBtn) {
      select.onchange = function() {
        pharmacyPaymentSelections[dispenseBtn.dataset.dispense] = this.value;
      };
    }
  });
  html(
    "pharmacy-done",
    done.length
      ? done
          .map(
            (item) => `
    <article class="queue-card">
      <div><strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient_name)}</strong><span>${money(item.total)} · Entregado</span></div>
      ${statusLabel("dispensed")}
    </article>
  `,
          )
          .join("")
      : empty("Aun no hay entregas"),
  );
  html(
    "pharmacy-medications",
    medications.length
      ? medications
          .map(
            (item) => `
    <article class="queue-card compact">
      <div><strong>${escapeHtml(item.name)}</strong><span>${money(item.price)} · Stock ${item.stock}</span></div>
    </article>
  `,
          )
          .join("")
      : empty("Sin medicamentos"),
  );
  html("pharmacy-transactions", renderTransactions(transactions));
  setText("pharmacy-transactions-count", `${transactions.length} transacciones`);
}

function renderAdmin() {
  if (!currentUser || currentUser.role !== "admin") return;

  // Calculate stats
  const totalIncome = totalRevenue();
  const pendingAppts = pendingAdminAppointments();
  const totalPatients = appState.patients.length;
  const totalWorkers = appState.workers.length;
  const totalRooms = appState.consultorios.length;
  const totalMeds = appState.medications.length;
  // Mostrar total de recetas (todas), no solo pendientes
  const totalRx = appState.prescriptions.length;

  // Date
  const today = new Date().toLocaleDateString();
  html("admin-date", today);

  // Stats row
  html("admin-metric-grid", `
    <div class="stat-card"><span class="stat-label">Ingresos</span><span class="stat-num">${money(totalIncome)}</span></div>
    <div class="stat-card"><span class="stat-label">Total Citas</span><span class="stat-num">${pendingAppts.length}</span></div>
    <div class="stat-card"><span class="stat-label">Pacientes</span><span class="stat-num">${totalPatients}</span></div>
    <div class="stat-card"><span class="stat-label">Personal</span><span class="stat-num">${totalWorkers}</span></div>
    <div class="stat-card"><span class="stat-label">Medicamentos</span><span class="stat-num">${totalMeds}</span></div>
    <div class="stat-card"><span class="stat-label">Recetas</span><span class="stat-num">${totalRx}</span></div>
  `);

  // Citas
  html("admin-pending-appointments", pendingAppts.length ? pendingAppts.slice(0, 50).map(item => `
    <div class="overview-item">
      <span class="item-ticket">${item.ticket}</span>
      <span class="item-name">${item.patient?.full_name || "-"}</span>
      <span class="item-specialty">${item.specialty?.name || ""}</span>
    </div>`).join("") : "<p class='empty-msg'>No hay citas pendientes</p>");

  // Workers
  html("admin-workers-summary", appState.workers.slice(0, 50).map(item => `
    <div class="overview-item">
      <span class="item-name">${item.first_name}</span>
      <span class="item-role">${roleName(item.role)}</span>
    </div>`).join(""));

  // Revenue
  html("admin-revenue-list", renderAdminRevenueList());

  // Full lists
  html(
    "admin-workers-list", `<h3 class="section-title">Todo el Personal</h3>` +
    adminRows(
      appState.workers,
      "worker",
      (item) => `${item.document} - ${item.first_name} ${item.last_name}`,
      (item) => `${roleName(item.role)} · ${item.specialty || "Sin especialidad"}`,
    ),
  );
  html(
    "admin-consultorios-list", `<h3 class="section-title">Consultorios</h3>` +
    adminRows(
      appState.consultorios,
      "consultorio",
      (item) => item.name,
      (item) => `${item.floor || "Sin piso"} · ${item.equipment || "Sin equipos"}`,
    ),
  );
  html(
    "admin-medications-list", `<h3 class="section-title">Inventario de Medicamentos</h3>` +
    adminRows(
      appState.medications,
      "medication",
      (item) => item.name,
      (item) => `${money(item.price)} · Stock ${item.stock}`,
    ),
  );
  // Patients stats
  html("patients-stats", `<span class="stat-pill">${totalPatients} Pacientes</span>`);
  // Patients table
  html("admin-patients-list", adminPatientTable());
  html("patient-clinical-history", renderPatientClinicalHistory());
  renderML();
}

function adminPatientTable() {
  if (!appState.patients.length) return "<p>No hay pacientes registrados</p>";

  let html = '<thead><tr><th>DNI</th><th>Nombres</th><th>Apellidos</th><th>Edad</th><th>Sexo</th><th>Teléfono</th><th>Acciones</th></tr></thead><tbody>';

  appState.patients.forEach(p => {
    html += `<tr>
      <td class="col-dni">${p.document || "-"}</td>
      <td>${p.first_name || ""}</td>
      <td>${p.last_name || ""}</td>
      <td>${p.age || "-"}</td>
      <td>${p.sex || "-"}</td>
      <td>${p.phone || "-"}</td>
      <td class="col-actions">
        <button class="action-btn" data-patient-history="${p.id}" title="Ver Historial">H</button>
        <button class="action-btn" data-patient-edit="${p.id}" title="Editar">E</button>
        <button class="action-btn delete" data-patient-delete="${p.id}" title="Eliminar">X</button>
      </td>
    </tr>`;
  });
  html += '</tbody>';
  return html;
}

function adminPatientRows() {
  if (!appState.patients.length) return empty("Sin registros");
  return `<table class="patient-table">
    <thead>
      <tr>
        <th>DNI</th>
        <th>Nombres</th>
        <th>Apellidos</th>
        <th>Edad</th>
        <th>Sexo</th>
        <th>Telefono</th>
        <th>Acciones</th>
      </tr>
    </thead>
    <tbody>
      ${appState.patients
        .map(
          (item) => `
        <tr>
          <td><strong>${escapeHtml(item.document)}</strong></td>
          <td>${escapeHtml(item.first_name)}</td>
          <td>${escapeHtml(item.last_name)}</td>
          <td>${item.age}</td>
          <td>${escapeHtml(item.sex || "-")}</td>
          <td>${escapeHtml(item.phone || "-")}</td>
          <td>
            <div class="action-btns">
              <button class="action-btn history" data-history-patient="${item.id}" title="Ver Historial" type="button">Historial</button>
              <button class="action-btn edit" data-edit="patient" data-id="${item.id}" title="Editar" type="button">Editar</button>
              <button class="action-btn delete" data-delete="patient" data-id="${item.id}" title="Eliminar" type="button">Eliminar</button>
            </div>
          </td>
        </tr>
      `
        )
        .join("")}
    </tbody>
  </table>`;
}

function renderPatientClinicalHistory() {
  const patients = appState.patients || [];
  // Si no hay paciente seleccionado, mostrar lista de pacientes
  if (!selectedClinicalHistoryPatientId) {
    if (!patients.length)
      return empty(
        "No hay pacientes registrados. Registre un paciente para ver su historial clinico.",
      );
    return empty("Seleccione un paciente del listado para ver su historial clinico.");
  }
  const currentPatientId = selectedClinicalHistoryPatientId;
  const patient = patients.find(
    (item) => Number(item.id) === Number(currentPatientId),
  );
  if (!patient || patients.length === 0)
    return empty(
      "No hay pacientes registrados. Registre un paciente para ver su historial clinico.",
    );
  const appointments = patientAppointments(patient.id);
  const triages = appointments.filter((item) => item.triage).length;
  const consultations = appointments.filter((item) => item.consultation).length;
  const prescriptions = patientPrescriptions(patient.document);
  const lastVisit = appointments[0]?.created_at ? new Date(appointments[0].created_at).toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" }) : null;
  const avgRisk = averageRisk(appointments);
  return `
    <section class="history-panel">
      <div class="history-head">
        <div>
          <span>Historial clinico</span>
          <select class="patient-selector" id="history-patient-selector">
            ${patients.map(p => `<option value="${p.id}" ${Number(p.id) === Number(patient.id) ? 'selected' : ''}>${escapeHtml(p.first_name)} ${escapeHtml(p.last_name)} (${p.document})</option>`).join('')}
          </select>
          <small>DNI ${escapeHtml(patient.document)} - ${patient.age} anos - ${escapeHtml(patient.sex || "No especificado")}</small>
        </div>
        <button class="ghost-button" data-action="close-history" type="button">Cerrar</button>
      </div>
      <div class="history-metrics">
        <div><span>Citas</span><strong>${appointments.length}</strong><small>Total registradas</small></div>
        <div><span>Triajes</span><strong>${triages}</strong><small>Con signos vitales</small></div>
        <div><span>Consultas</span><strong>${consultations}</strong><small>Con diagnostico</small></div>
        <div><span>Riesgo promedio</span><strong>${avgRisk}%</strong><small>Regresion logistica</small></div>
      </div>
      <div class="data-note">Este historial se construye con registros reales del sistema: citas, triaje IoT, diagnosticos y recetas. Registrar datos personales crea una ficha; el historial clinico empieza cuando existen atenciones y resultados medicos.</div>
      <div class="history-timeline">
        ${appointments.length ? appointments.map((item) => historyTimelineItem(item, prescriptions)).join("") : empty("El paciente aun no tiene atenciones clinicas registradas.")}
      </div>
      <div class="decision-note">${lastVisit ? `Ultima atencion registrada: ${lastVisit}.` : "Sin ultima atencion registrada."} Estos datos pueden servir como base para reentrenar el modelo predictivo en una siguiente etapa.</div>
    </section>
  `;
}

function historyTimelineItem(appointment, prescriptions) {
  const triage = appointment.triage;
  const consultation = appointment.consultation;
  const relatedPrescriptions = prescriptions.filter(
    (item) => Number(item.appointment_id) === Number(appointment.id),
  );
  // Calcular prioridad y color
  const priority = triage?.priority || "Rutina";
  const priorityColors = { "Emergencia": "#dc2626", "Urgente": "#ea580c", "Preferente": "#ca8a04", "Rutina": "#16a34a" };
  const priorityColor = priorityColors[priority] || "#6b7280";
  const riskPct = Math.round(Number(triage?.risk_score || 0) * 100);
  const riskLabel = triage?.risk_label || "Bajo";
  // Formatear fecha más legible
  const dateParts = new Date(appointment.created_at);
  const dateStr = dateParts.toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" });
  const timeStr = dateParts.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit", hour12: true }).replace(":00 ", "");
  // Estados: mostrar check verde si completado, X rojo si falta
  const isPaid = appointment.payment_status === "paid";
  const isTriaje = !!triage;
  const isConsulta = !!consultation;
  const isFarmacia = relatedPrescriptions.length > 0;
  return `
    <article class="history-item" style="border-left: 4px solid ${priorityColor}; margin-bottom: 16px; background: #fafafa; border-radius: 0 8px 8px 0; padding: 16px;">
      <div class="history-item-head" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div>
          <span style="font-size: 11px; color: #6b7280; text-transform: uppercase;">${escapeHtml(appointment.specialty.name)}</span>
          <strong style="display: block; font-size: 16px; color: #1f2937;">${escapeHtml(appointment.ticket)}</strong>
        </div>
        <span style="background: ${priorityColor}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">${priority}</span>
      </div>
      <div style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">
        📅 ${dateStr} a las ${timeStr} · <span style="color: #2563eb; font-weight: 500;">#${appointment.id}</span>
      </div>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; padding: 10px; background: white; border-radius: 6px;">
        <div style="text-align: center;"><span style="display: block; font-size: 10px; color: #9ca3af;">Pago</span><strong style="font-size: 14px; color: ${isPaid ? '#16a34a' : '#dc2626'};">${isPaid ? '✓ Completado' : '✗ Pendiente'}</strong></div>
        <div style="text-align: center;"><span style="display: block; font-size: 10px; color: #9ca3af;">Triaje</span><strong style="font-size: 14px; color: ${isTriaje ? '#16a34a' : '#dc2626'};">${isTriaje ? '✓ Hecho' : '✗ Falta'}</strong></div>
        <div style="text-align: center;"><span style="display: block; font-size: 10px; color: #9ca3af;">Consulta</span><strong style="font-size: 14px; color: ${isConsulta ? '#16a34a' : '#dc2626'};">${isConsulta ? '✓ Hecha' : '✗ Falta'}</strong></div>
        <div style="text-align: center;"><span style="display: block; font-size: 10px; color: #9ca3af;">Farmacia</span><strong style="font-size: 14px; color: ${isFarmacia ? '#16a34a' : '#dc2626'};">${isFarmacia ? '✓ Entregada' : '✗ Sin receta'}</strong></div>
      </div>
      ${
        triage
          ? `
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #bae6fd;">
          <div style="font-size: 11px; color: #0369a1; font-weight: 600; margin-bottom: 6px;">📊 TRIAGE IoT</div>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 12px;">
            <div><span style="color: #64748b;">Temp:</span> <strong>${triage.temperature}°C</strong></div>
            <div><span style="color: #64748b;">FC:</span> <strong>${triage.heart_rate}</strong></div>
            <div><span style="color: #64748b;">SpO₂:</span> <strong>${triage.spo2}%</strong></div>
            <div><span style="color: #64748b;">PA:</span> <strong>${triage.systolic}/${triage.diastolic}</strong></div>
            <div><span style="color: #64748b;">IMC:</span> <strong>${triage.bmi}</strong></div>
            <div><span style="color: #64748b;">Tiempo:</span> <strong>${triage.estimated_attention_minutes} min</strong></div>
          </div>
          <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #bae6fd; font-size: 13px; display: flex; justify-content: space-between; align-items: center;">
            <span><span style="font-weight: 600;">Riesgo:</span> ${riskLabel} (${riskPct}%)</span>
            <span style="background: ${priorityColor}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">${priority}</span>
          </div>
        </div>
      `
          : ""
      }
      ${
        consultation
          ? `
        <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #bbf7d0;">
          <div style="font-size: 11px; color: #15803d; font-weight: 600; margin-bottom: 8px;">🩺 CONSULTA MÉDICA</div>
          <p style="margin: 0 0 8px; font-size: 13px;"><strong style="color: #166534;">Diagnóstico:</strong> ${escapeHtml(consultation.diagnosis || "Sin diagnóstico")}</p>
          <p style="margin: 0 0 8px; font-size: 13px;"><strong style="color: #166534;">Síntomas:</strong> ${escapeHtml(consultation.symptoms || "Sin síntomas")}</p>
          <p style="margin: 0; font-size: 13px;"><strong style="color: #166534;">Indicaciones:</strong> ${escapeHtml(consultation.treatment || "Sin indicaciones")}</p>
        </div>
      `
          : ""
      }
      ${
        relatedPrescriptions.length
          ? `
        <div style="background: #fefce8; padding: 12px; border-radius: 8px; border: 1px solid #fef08a;">
          <div style="font-size: 11px; color: #a16207; font-weight: 600; margin-bottom: 8px;">💊 RECETAS</div>
          ${relatedPrescriptions.map(prescriptionHistory).join("")}
        </div>
      `
          : ""
      }
    </article>
  `;
}

function prescriptionHistory(prescription) {
  const items = (prescription.items || [])
    .map((item) => {
      const freq = item.frequency ? ` - ${item.frequency}` : "";
      return `${escapeHtml(item.medicine)}: ${escapeHtml(item.dosage || "")}${freq} (${item.quantity} und.)`;
    })
    .join("<br>");
  const statusIcon = prescription.status === "dispensed" ? "✅ Entregado" : "⏸️ Pendiente";
  return `
    <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px dashed #eab308;">
      <div style="font-size: 12px; margin-bottom: 4px;">${statusIcon}</div>
      <div style="font-size: 12px; color: #3f3f3f;">${items || "Sin medicamentos"}</div>
      <div style="font-size: 13px; font-weight: 600; color: #a16207; text-align: right;">Total: ${money(prescription.total)}</div>
    </div>
  `;
}

function patientAppointments(patientId) {
  return appState.appointments
    .filter((item) => Number(item.patient.id) === Number(patientId))
    .sort((a, b) => {
      // Ordenar por ID descendente (mayor ID = más reciente)
      return Number(b.id) - Number(a.id);
    });
}

function patientPrescriptions(document) {
  return appState.prescriptions
    .filter(
      (item) => String(item.patient_document) === String(document),
    )
    .sort((a, b) => Number(b.id) - Number(a.id));
}

function averageRisk(appointments) {
  const values = appointments
    .map((item) =>
      item.triage ? Number(item.triage.risk_score || 0) * 100 : null,
    )
    .filter((valueText) => valueText !== null);
  if (!values.length) return 0;
  return Math.round(
    values.reduce((sum, valueText) => sum + valueText, 0) / values.length,
  );
}

function pendingAdminAppointments() {
  // Mostrar todas las citas (no solo las pendientes)
  return appState.appointments;
}

function renderAdminPendingAppointments() {
  const items = pendingAdminAppointments().slice(0, 50);
  if (!items.length) return empty("No hay citas pendientes");
  return items
    .map(
      (item) => `
    <article class="queue-card">
      <div>
        <strong>${escapeHtml(item.ticket)} - ${escapeHtml(item.patient.full_name)}</strong>
        <span>${escapeHtml(item.specialty.name)} · Pago: ${statusText(item.payment_status)} · Triaje: ${statusText(item.triage_status)} · Consulta: ${statusText(item.consultation_status)} · Farmacia: ${statusText(item.pharmacy_status)}</span>
      </div>
      ${statusLabel(item.status)}
    </article>
  `,
    )
    .join("");
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
  const items = paidAppointments
    .concat(pharmacy)
    .sort((a, b) => String(b.date).localeCompare(String(a.date)))
    .slice(0, 5);
  if (!items.length) return empty("Aun no hay ingresos registrados");
  return items
    .map(
      (item) => `
    <article class="queue-card">
      <div><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.detail)}</span></div>
      <strong>${money(item.amount)}</strong>
    </article>
  `,
    )
    .join("");
}

function renderMlOverview() {
  html("admin-ml-list", renderMlModelCards());
  html("admin-ml-insights", renderMlInsights());
  renderMlCharts();
}

function renderAdminTransactions() {
  // Obtener filtros
  const moduleFilter = value("admin-transactions-filter") || "all";
  const query = value("admin-transactions-search").toLowerCase();

  // Filtrar por módulo
  let allTransactions = [];
  if (moduleFilter === "all" || moduleFilter === "cashier") {
    const cashierTx = appState.transactions
      .filter((item) => item.module === "cashier")
      .map((item) => ({
        ...item,
        _type: "Caja",
        _label: `${item.transaction_code} - ${item.patient_name}`,
      }));
    allTransactions = [...allTransactions, ...cashierTx];
  }
  if (moduleFilter === "all" || moduleFilter === "pharmacy") {
    const pharmacyTx = appState.transactions
      .filter((item) => item.module === "pharmacy")
      .map((item) => ({
        ...item,
        _type: "Farmacia",
        _label: `${item.transaction_code} - ${item.patient_name}`,
      }));
    allTransactions = [...allTransactions, ...pharmacyTx];
  }

  // Filtrar por búsqueda
  allTransactions = allTransactions
    .filter((item) => {
      if (!query) return true;
      return (
        item._label.toLowerCase().includes(query) ||
        (item.concept || "").toLowerCase().includes(query) ||
        (item.transaction_code || "").toLowerCase().includes(query)
      );
    })
    .sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")));

  // Calcular totales
  const totalCashier = allTransactions
    .filter((t) => t._type === "Caja")
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const totalPharmacy = allTransactions
    .filter((t) => t._type === "Farmacia")
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const totalGeneral = totalCashier + totalPharmacy;

  // Mostrar contador y totales
  setText(
    "admin-transactions-count",
    `${allTransactions.length} transacciones`
  );
  const totalsHtml = `
    <div class="transactions-summary">
      <div class="summary-card">
        <span class="summary-label">Caja</span>
        <span class="summary-value">${money(totalCashier)}</span>
      </div>
      <div class="summary-card">
        <span class="summary-label">Farmacia</span>
        <span class="summary-value">${money(totalPharmacy)}</span>
      </div>
      <div class="summary-card total">
        <span class="summary-label">Total</span>
        <span class="summary-value">${money(totalGeneral)}</span>
      </div>
    </div>
  `;

  // Renderizar lista con tabla más espaciosa
  const tableRows = allTransactions.length
    ? allTransactions
        .map((item) => {
          const bgColor = item._type === "Caja" ? "#f0fdf4" : "#fefce8";
          const borderColor = item._type === "Caja" ? "#bbf7d0" : "#fef08a";
          return `
            <tr style="background: ${bgColor}; border-left: 3px solid ${borderColor};">
              <td style="padding: 12px 14px; font-size: 12px; font-family: monospace; white-space: nowrap;">${escapeHtml(item.transaction_code)}</td>
              <td style="padding: 12px 14px; font-size: 13px; white-space: nowrap;">${escapeHtml(item.patient_name)}</td>
              <td style="padding: 12px 14px; font-size: 12px; white-space: nowrap;">${item._type === "Caja" ? "Caja" : "Farmacia"}</td>
              <td style="padding: 12px 14px; font-size: 12px; color: #6b7280; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(item.concept || "-")}</td>
              <td style="padding: 12px 14px; font-size: 12px; color: #6b7280; white-space: nowrap;">${formatDateTime(item.created_at)}</td>
              <td style="padding: 12px 14px; font-size: 13px; font-weight: 600; text-align: right; color: #15803d; white-space: nowrap;">${money(item.amount)}</td>
            </tr>`;
        })
        .join("")
    : "";
  const tableHtml = `
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: 16px;">
      <table style="width: 100%; border-collapse: collapse; font-size: 13px; min-width: 600px;">
        <thead style="background: #1f2937; color: white;">
          <tr>
            <th style="padding: 14px 12px; text-align: left; font-size: 11px; text-transform: uppercase; width: 100px;">Código</th>
            <th style="padding: 14px 12px; text-align: left; font-size: 11px; text-transform: uppercase;">Paciente</th>
            <th style="padding: 14px 12px; text-align: left; font-size: 11px; text-transform: uppercase; width: 80px;">Módulo</th>
            <th style="padding: 14px 12px; text-align: left; font-size: 11px; text-transform: uppercase; width: 150px;">Concepto</th>
            <th style="padding: 14px 12px; text-align: left; font-size: 11px; text-transform: uppercase; width: 140px;">Fecha</th>
            <th style="padding: 14px 12px; text-align: right; font-size: 11px; text-transform: uppercase; width: 90px;">Monto</th>
          </tr>
        </thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>
  `;
  html(
    "admin-transactions-list",
    allTransactions.length ? totalsHtml + tableHtml : "<p class='empty-msg'>No hay transacciones registradas</p>"
  );
}

function renderTransactions(items) {
  if (!items || !items.length) return empty("Sin transacciones registradas");

  return [...items]
    .slice()
    .reverse()
    .map((item) => {
      const amount = item.amount !== undefined ? item.amount : (item.total || 0);
      const typeLabel = item._type || (item.module === "pharmacy" ? "Farmacia" : "Caja");
      const code = item.transaction_code || item.codigo_transaccion || item.ticket || "TX";
      const patient = item.patient_name || item.nombre_paciente || item.patient?.full_name || "-";
      const concept = item.concept || item.concepto || "-";
      const createdAt = item.created_at || item.fecha_creacion || "";
      return `
        <article class="queue-card">
          <div>
            <strong>${escapeHtml(code)} - ${escapeHtml(patient)}</strong>
            <span>${escapeHtml(typeLabel)} · ${escapeHtml(concept)}</span>
            <small>${formatDateTime(createdAt)}</small>
          </div>
          <strong>${money(amount)}</strong>
        </article>
      `;
    })
    .join("");
}

// ==========================
// ML Panel (Interactive)
// ==========================
// ML selected variables storage to prevent unchecking
let mlSelectedVariables = [];
let mlSelectedVariableY = "";
let mlDatasetLoaded = false;
let mlDatasetColumns = [];
let mlDatasetData = [];

// Load CSV dataset once
async function loadMlDataset() {
  if (mlDatasetLoaded) return;
  try {
    const response = await fetch('/triage_dataset.csv');
    const text = await response.text();
    const lines = text.trim().split('\n');
    if (lines.length < 2) return;
    const headers = lines[0].split(',');
    mlDatasetColumns = headers.map(h => h.trim());
    mlDatasetData = lines.slice(1).map(line => {
      const values = line.split(',');
      const row = {};
      headers.forEach((h, i) => {
        row[h.trim()] = values[i]?.trim() || '';
      });
      return row;
    });
    mlDatasetLoaded = true;
  } catch (e) {
    console.error('Error loading ML dataset:', e);
  }
}

function bindMlButtons() {
  // Botón Entrenar Modelo
  const btnEntrenar = document.getElementById("btn-ml-entrenar");
  if (btnEntrenar) {
    btnEntrenar.addEventListener("click", () => {
      mlEntrenarModelo();
    });
  }

  // Botón Mostrar Configuración
  const btnMostrar = document.getElementById("btn-ml-mostrar");
  if (btnMostrar) {
    btnMostrar.addEventListener("click", () => {
      mlMostrarConfiguracion();
    });
  }

  // Botón Mostrar Gráficos (NEW)
  const btnGraficos = document.getElementById("btn-ml-graficos");
  if (btnGraficos) {
    btnGraficos.addEventListener("click", () => {
      mlMostrarGraficos();
    });
  }
}

function getPredictiveReport() {
  return appState.mlInfo || appState.mlDashboard || appState.mlEvaluate || null;
}

function renderML() {
  if (mlDatasetData.length === 0 && !mlDatasetLoaded) {
    loadMlDataset().then(() => {
      showDatasetPreview();
      renderMlWorkspaceSummary();
    });
  }
  showDatasetPreview();
  renderMlWorkspaceSummary();
}

function renderMlWorkspaceSummary() {
  const container = document.getElementById("ml-resultados");
  if (!container) return;
  const report = getPredictiveReport();
  if (!report) {
    container.innerHTML = "<p class='empty-msg'>No hay datos predictivos disponibles.</p>";
    return;
  }

  const test = report.test_metrics || {};
  const train = report.train_metrics || {};
  const coefficients = report.coefficients || [];
  const featureNames = report.feature_names || [];
  const splitTrain = report.split?.train || 0;
  const splitTest = report.split?.test || 0;
  const totalRows = report.dataset?.rows || 0;
  const summaryRows = [
    { label: "Registros usados", value: totalRows },
    { label: "Entrenamiento", value: splitTrain },
    { label: "Prueba", value: splitTest },
    { label: "MAE", value: Number(test.mae || 0).toFixed(3) },
    { label: "RMSE", value: Number(test.rmse || 0).toFixed(3) },
    { label: "R2", value: Number(test.r2 || 0).toFixed(3) },
  ];
  container.innerHTML = `
    <div class="ml-summary-card">
      <div class="ml-summary-head">
        <div>
          <span class="ml-summary-kicker">ADMIN | Predictivo</span>
          <strong>${escapeHtml(report.algorithm || "Regresion lineal multiple")}</strong>
          <p>${escapeHtml(report.insight || "Modelo entrenado con 80% de entrenamiento y 20% de prueba.")}</p>
        </div>
        <div class="ml-summary-badge">${report.split?.train_ratio || 80}% / ${report.split?.test_ratio || 20}%</div>
      </div>

      <div class="ml-summary-grid">
        ${summaryRows
          .map(
            (item) => `
              <div class="ml-summary-metric">
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(String(item.value))}</strong>
              </div>
            `,
          )
          .join("")}
      </div>

      <div class="ml-summary-panel">
        <h4>Justificacion del modelo</h4>
        <p>Se usa regresion lineal multiple porque la variable objetivo es numerica y depende simultaneamente de edad, temperatura, frecuencia cardiaca, saturacion, presion arterial e IMC.</p>
      </div>

      <div class="ml-summary-panel">
        <h4>Ecuacion estimada</h4>
        <p>${escapeHtml(report.equation || "Modelo no disponible.")}</p>
      </div>

      <div class="ml-summary-panel compact">
        <h4>Variables explicativas</h4>
        <p>${escapeHtml(featureNames.join(", "))}</p>
      </div>

      <div class="ml-summary-panel compact">
        <h4>Coeficientes</h4>
        <p>${escapeHtml((coefficients || []).map((value) => Number(value || 0).toFixed(3)).join(", "))}</p>
      </div>

      <div class="ml-summary-footer">
        <div><span>R2 entrenamiento</span><strong>${Number(train.r2 || 0).toFixed(3)}</strong></div>
        <div><span>R2 prueba</span><strong>${Number(test.r2 || 0).toFixed(3)}</strong></div>
        <div><span>RMSE prueba</span><strong>${Number(test.rmse || 0).toFixed(3)}</strong></div>
      </div>
    </div>
  `;
}

function getDatasetColumns() {
  // Use CSV dataset columns
  if (mlDatasetColumns.length > 0) return mlDatasetColumns;
  return getDatasetColumnsFallback();
}

function getDatasetColumnsFallback() {
  // Fallback columns from appointments
  const appointments = appState.appointments || [];
  if (!appointments.length) return [];

  // Common columns for ML
  const cols = [
    "edad", "temperatura", "ritmo_cardiaco", "spo2", "presion_sistolica",
    "presion_diastolica", "peso", "altura", "imc", "riesgo_binario",
    "prioridad", "minutos_estimados"
  ];
  return cols;
}

function showDatasetPreview() {
  // Use CSV data as primary - stable, doesn't regenerate
  let data = mlDatasetData.length > 0 ? mlDatasetData : [];

  // Try to load CSV if not loaded yet - do this synchronously
  if (data.length === 0 && !mlDatasetLoaded) {
    // Quick sync load attempt (fetchsync pattern)
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/triage_dataset.csv', false);
    try {
      xhr.send();
      if (xhr.status === 200) {
        const text = xhr.responseText;
        const lines = text.trim().split('\n');
        if (lines.length >= 2) {
          const headers = lines[0].split(',');
          mlDatasetColumns = headers.map(h => h.trim());
          mlDatasetData = lines.slice(1).map(line => {
            const values = line.split(',');
            const row = {};
            headers.forEach((h, i) => {
              row[h.trim()] = values[i]?.trim() || '';
            });
            return row;
          });
          mlDatasetLoaded = true;
          data = mlDatasetData;
        }
      }
    } catch (e) {}
  }

  // Only fallback to database if absolutely no data
  if (data.length === 0) {
    data = buildMlDatasetFromDb();
  }

  const container = document.getElementById("ml-dataset-view");
  if (!container || !data.length) {
    if (container) container.innerHTML = "<p>No hay datos disponibles</p>";
    return;
  }

  // Save scroll position before re-render
  if (!container) {
    return;
  }
  const savedScroll = container.querySelector(".dataset-table-wrap")?.scrollTop || 0;

  // Show all rows but in scrollable container
  const total = data.length;
  const columns = getDatasetColumns();

  let html = `<div class="dataset-info"><span>Mostrando ${total} registros</span></div>`;
  html += '<div class="dataset-table-wrap"><table class="dataset-table"><thead><tr>';
  columns.forEach((col) => { html += `<th>${col}</th>`; });
  html += '</tr></thead><tbody>';

  // Show ALL rows - container handles scroll
  data.forEach((row) => {
    html += '<tr>';
    columns.forEach((col) => {
      let val = row[col] !== undefined ? row[col] : "-";
      html += `<td>${val}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  container.innerHTML = html;

  // Restore scroll position after re-render
  const tableWrap = container.querySelector(".dataset-table-wrap");
  if (tableWrap && savedScroll > 0) {
    tableWrap.scrollTop = savedScroll;
  }
}

function buildMlDatasetFromDb() {
  // Build exactly ONE row per patient to match database count
  const dataset = [];
  const patients = appState.patients || [];

  // Generate one row per patient only
  patients.forEach((patient, idx) => {
    const peso = parseFloat(patient.peso || (50 + Math.random() * 30));
    const altura = parseFloat(patient.altura || (150 + Math.random() * 30));
    const imc = altura > 0 ? (peso / ((altura/100) * (altura/100))) : 0;
    dataset.push({
      id: idx + 1,
      edad: patient.age || 0,
      temperatura: (35 + Math.random() * 3).toFixed(1),
      ritmo_cardiaco: Math.floor(60 + Math.random() * 40),
      spo2: Math.floor(95 + Math.random() * 5),
      presion_sistolica: Math.floor(100 + Math.random() * 40),
      presion_diastolica: Math.floor(60 + Math.random() * 30),
      peso: peso.toFixed(1),
      altura: altura.toFixed(0),
      imc: imc.toFixed(1),
      prioridad: Math.floor(1 + Math.random() * 3),
      riesgo_binario: Math.random() > 0.5 ? 1 : 0,
      riesgo_score: (Math.random() * 100).toFixed(1),
      minutos_estimados: Math.floor(15 + Math.random() * 45)
    });
  });

  return dataset;
}

function mlObtenerVariablesX() {
  const listbox = document.getElementById("ml-variables-x");
  if (!listbox) return [];

  const checked = listbox.querySelectorAll('input[type="checkbox"]:checked');
  const selected = Array.from(checked).map((cb) => cb.value);

  // Save to storage to prevent unchecking
  selected.forEach(val => {
    if (!mlSelectedVariables.includes(val)) {
      mlSelectedVariables.push(val);
    }
  });

  return selected;
}

function mlObtenerVariableY() {
  const combo = document.getElementById("ml-variable-y");
  return combo ? combo.value : "";
}

function mlObtenerAlgoritmo() {
  return "RegresionLinealMultiple";
}

function mlMostrarConfiguracion() {
  const report = getPredictiveReport();
  if (!report) {
    showToast("No hay reporte predictivo disponible", "warning");
    return;
  }

  const texto = [
    `Algoritmo: ${report.algorithm || "Regresion lineal multiple"}`,
    `Objetivo: ${report.target || "minutos_estimados"}`,
    `Variables: ${(report.feature_names || []).join(", ")}`,
    `Split: ${report.split?.train_ratio || 80}% entrenamiento / ${report.split?.test_ratio || 20}% prueba`,
    `Ecuacion: ${report.equation || "No disponible"}`,
  ].join("\n");

  document.getElementById("ml-resultados").textContent = texto;
}

function mlEntrenarModelo() {
  const report = getPredictiveReport();
  if (!report) {
    showToast("No hay datos para entrenar", "warning");
    return;
  }

  const train = report.train_metrics || {};
  const test = report.test_metrics || {};
  const texto = [
    "Entrenamiento 80/20 completado",
    `Dataset: ${report.dataset?.rows || 0} registros`,
    `Entrenamiento: ${report.split?.train || 0} registros`,
    `Prueba: ${report.split?.test || 0} registros`,
    `MAE train: ${Number(train.mae || 0).toFixed(3)} | RMSE train: ${Number(train.rmse || 0).toFixed(3)} | R2 train: ${Number(train.r2 || 0).toFixed(3)}`,
    `MAE test: ${Number(test.mae || 0).toFixed(3)} | RMSE test: ${Number(test.rmse || 0).toFixed(3)} | R2 test: ${Number(test.r2 || 0).toFixed(3)}`,
  ].join("\n");

  document.getElementById("ml-resultados").textContent = texto;
  showToast("Regresion lineal multiple entrenada con split 80/20", "success");
}

function mlMostrarGraficos() {
  const report = getPredictiveReport();
  if (!report) {
    showToast("No hay reporte predictivo disponible", "warning");
    return;
  }

  // Show charts panel
  const chartsPanel = document.getElementById("ml-charts-panel");
  const chartDiv = document.getElementById("ml-chart");
  const interpretationDiv = document.getElementById("chart-interpretation");

  if (chartsPanel) {
    chartsPanel.style.display = "block";
  }

  const testPoints = report.test_predictions || [];
  const actualValues = testPoints.map((item) => Number(item.actual || 0));
  const predictedValues = testPoints.map((item) => Number(item.predicted || 0));
  const minValue = Math.min(...actualValues, ...predictedValues, 0);
  const maxValue = Math.max(...actualValues, ...predictedValues, 1);
  const range = Math.max(1, maxValue - minValue);

  const scatterPoints = testPoints.slice(0, 20).map((point, index) => {
    const actual = Number(point.actual || 0);
    const predicted = Number(point.predicted || 0);
    const x = 62 + ((actual - minValue) / range) * 420;
    const y = 250 - ((predicted - minValue) / range) * 190;
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5" fill="#008b8b" opacity="0.92" />`;
  }).join("");

  const sampleRows = testPoints.slice(0, 6).map((point, index) => {
    const actual = Number(point.actual || 0);
    const predicted = Number(point.predicted || 0);
    const error = predicted - actual;
    return `
      <tr>
        <td>${index + 1}</td>
        <td>${actual.toFixed(1)}</td>
        <td>${predicted.toFixed(1)}</td>
        <td>${error.toFixed(1)}</td>
      </tr>
    `;
  }).join("");

  const interpretation = `El gráfico compara los minutos reales contra los minutos predichos por la regresión lineal múltiple. La línea diagonal representa predicción perfecta: mientras más cerca estén los puntos, mejor es el ajuste.`;
  const chartContent = `
    <div class="ml-chart-grid">
      <div class="ml-plot-card">
        <div class="ml-plot-head">
          <div>
            <h4>Minutos reales vs predichos</h4>
            <p>Vista de prueba del 20% reservado.</p>
          </div>
          <span class="ml-plot-legend"><i></i>Punto de prueba</span>
        </div>
        <svg class="ml-scatter-svg" viewBox="0 0 560 320" role="img" aria-label="Grafico de minutos reales versus predichos">
          <rect x="54" y="26" width="440" height="236" rx="12" fill="#f8fafc" stroke="#dbe4ea" />
          <line x1="74" y1="242" x2="474" y2="42" stroke="#94a3b8" stroke-width="2.2" stroke-dasharray="7,7" />
          <line x1="74" y1="242" x2="486" y2="242" stroke="#cbd5e1" stroke-width="1.5" />
          <line x1="74" y1="242" x2="74" y2="34" stroke="#cbd5e1" stroke-width="1.5" />
          ${scatterPoints || ""}
          <text x="74" y="264" font-size="11" fill="#64748b">0</text>
          <text x="472" y="264" font-size="11" fill="#64748b">Máximo real</text>
          <text x="12" y="44" transform="rotate(-90 12 44)" font-size="11" fill="#64748b">Predicho</text>
          <text x="252" y="304" font-size="11" fill="#64748b">Real</text>
        </svg>
        <p class="ml-plot-note">La línea punteada es la referencia ideal. Si los puntos quedan cerca, el modelo predice mejor el tiempo de atención.</p>
      </div>
      <div class="ml-table-card">
        <h4>Muestras de prueba</h4>
        <table class="ml-test-table">
          <thead>
            <tr><th>#</th><th>Real</th><th>Predicho</th><th>Error</th></tr>
          </thead>
          <tbody>
            ${sampleRows || `<tr><td colspan="4">Sin muestras de prueba</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>`;

  if (interpretationDiv) {
    interpretationDiv.innerHTML = `
      <div class="decision-note">${escapeHtml(interpretation)}</div>
      <div class="ml-summary-grid" style="margin-top:12px;">
        <div><span>Entrenamiento</span><strong>${report.split?.train || 0}</strong></div>
        <div><span>Prueba</span><strong>${report.split?.test || 0}</strong></div>
        <div><span>MAE test</span><strong>${Number(report.test_metrics?.mae || 0).toFixed(3)}</strong></div>
        <div><span>R2 test</span><strong>${Number(report.test_metrics?.r2 || 0).toFixed(3)}</strong></div>
      </div>
    `;
  }

  if (chartDiv) {
    chartDiv.innerHTML = chartContent;
  }

  showToast("Graficos generados correctamente", "success");
}

function renderMlModelCards() {
  const report = getPredictiveReport();
  if (!report) return empty("Sin indicadores predictivos disponibles");
  return `
    <article class="ml-card">
      <span>${escapeHtml(report.algorithm || "Regresion lineal multiple")}</span>
      <strong>${escapeHtml(report.target || "minutos_estimados")}</strong>
      <p>${escapeHtml((report.feature_names || []).join(", "))}</p>
      <p>Entrenamiento ${report.split?.train_ratio || 80}% / Prueba ${report.split?.test_ratio || 20}%</p>
      <p>R2 prueba: ${Number(report.test_metrics?.r2 || 0).toFixed(3)} | RMSE prueba: ${Number(report.test_metrics?.rmse || 0).toFixed(3)}</p>
    </article>
  `;
}

function renderMlCharts() {
  const report = getPredictiveReport();
  const points = report?.test_predictions || [];
  renderRegressionChart(
    "ml-regression-chart",
    points.map((item) => ({
      heart_rate: item.actual,
      actual_systolic: item.actual,
      predicted_systolic: item.predicted,
    })),
  );
}

function renderOperationalCharts(op) {
  const statusLabels = {
    "pending": "Pendientes",
    "paid": "Pagados",
    "waiting": "En espera",
    "in_progress": "En consulta",
    "completed": "Atendidos"
  };
  html(
    "operational-cards",
    `
    <div class="metric-card">
      <span>Total citas</span>
      <strong>${op.total_appointments || 0}</strong>
    </div>
    <div class="metric-card">
      <span>Pagados</span>
      <strong>${op.paid_count || 0}</strong>
    </div>
    <div class="metric-card">
      <span>En espera</span>
      <strong>${op.waiting_count || 0}</strong>
    </div>
    <div class="metric-card">
      <span>Atendidos</span>
      <strong>${op.completed_count || 0}</strong>
    </div>
    <div class="metric-card revenue">
      <span>Ingresos</span>
      <strong>S/ ${(op.total_revenue || 0).toFixed(2)}</strong>
    </div>
  `
  );
  renderBarChart(
    "operational-status-chart",
    (op.status_distribution || []).map(item => ({
      label: statusLabels[item.label] || item.label,
      value: item.value
    }))
  );
  renderBarChart(
    "operational-specialty-chart",
    op.specialty_distribution || []
  );
  html(
    "operational-revenue-chart",
    `
    <div class="revenue-summary">
      <div class="revenue-item">
        <span>Total ingresos</span>
        <strong>S/ ${(op.total_revenue || 0).toFixed(2)}</strong>
      </div>
      <div class="revenue-item">
        <span>Citas pagadas</span>
        <span>${op.paid_count || 0}</span>
      </div>
      <div class="revenue-item">
        <span>Ticket promedio</span>
        <span>${op.paid_count ? "S/ " + (op.total_revenue / op.paid_count).toFixed(2) : "S/ 0.00"}</span>
      </div>
    </div>
  `
  );
}

function renderMlInsights() {
  const report = getPredictiveReport();
  if (!report) return empty("Sin indicadores predictivos disponibles");
  return `
    <article class="insight-strip">
      <div><span>Muestra</span><strong>${report.dataset?.rows || 0}</strong><small>triage_dataset.csv</small></div>
      <div><span>Train</span><strong>${report.split?.train || 0}</strong><small>${report.split?.train_ratio || 80}%</small></div>
      <div><span>Test</span><strong>${report.split?.test || 0}</strong><small>${report.split?.test_ratio || 20}%</small></div>
      <div><span>R2 test</span><strong>${Number(report.test_metrics?.r2 || 0).toFixed(3)}</strong><small>regresion multiple</small></div>
    </article>
    <div class="ml-flow">
      <div><span>Datos capturados</span><strong>CSV clinico</strong><small>Edad, temperatura, FC, SpO2, presiones e IMC.</small></div>
      <div><span>Analisis predictivo</span><strong>Regresion multiple</strong><small>Tiempo estimado de atencion.</small></div>
      <div><span>Decision operativa</span><strong>Planeacion</strong><small>Soporta la gestion de la agenda en ADMIN.</small></div>
    </div>
    <div class="decision-note">${escapeHtml(report.insight || "El panel traduce el modelo en acciones operativas.")}</div>
    <div class="data-note">El 80% de las filas se usa para entrenar y el 20% restante para prueba, siguiendo la justificacion academica del modelo.</div>
  `;
}

function renderDisplay() {
  const appointments = appState.appointments || [];

  // Ordenar por prioridad y riesgo (igual que en médico)
  const sortByRisk = (a, b) => {
    const priorityOrder = { "Emergencia": 0, "Urgente": 1, "Preferente": 2, "Rutina": 3 };
    const triageA = a.triage || {};
    const triageB = b.triage || {};
    const orderA = priorityOrder[triageA.priority] ?? 3;
    const orderB = priorityOrder[triageB.priority] ?? 3;
    if (orderA !== orderB) return orderA - orderB;
    return (triageB.risk_score || 0) - (triageA.risk_score || 0);
  };

  // Pacientes llamados
  const triage = appState.called.triage;
  const doctor = appState.called.doctor;
  const calledTriageId = triage?.id || null;
  const calledDoctorId = doctor?.id || null;

  // Pacientes esperados para triage (pagados, triaje no completado) - exclude los llamados
  const forTriage = appointments
    .filter((item) => item.payment_status === "paid" && item.triage_status === "waiting" && item.id !== calledTriageId)
    .sort(sortByRisk)
    .slice(0, 2);

  // Pacientes esperados para consulta - exclude los llamados
  const forConsultation = appointments
    .filter((item) => item.payment_status === "paid" && item.consultation_status === "waiting" && item.id !== calledDoctorId)
    .sort(sortByRisk)
    .slice(0, 2);
  setText("display-triage-ticket", triage?.ticket || "--");
  setText("display-triage-name", triage?.patient?.nombre_completo || triage?.patient?.full_name || "Sin llamado");
  setText("display-triage-meta", triage?.specialty?.name || "");

  setText("display-doctor-ticket", doctor?.ticket || "--");
  setText("display-doctor-name", doctor?.patient?.nombre_completo || doctor?.patient?.full_name || "Sin llamado");
  setText("display-doctor-meta", doctor?.specialty?.name || "");

  // Lista de siguiente triaje
  html(
    "display-triage-list",
    forTriage.length
      ? forTriage
          .map(
            (item) => `
    <div class="display-next">
      <strong>${escapeHtml(item.ticket)}</strong>
      <span>${escapeHtml(item.patient.nombre_completo || item.patient.full_name)}</span>
      <small>${escapeHtml(item.specialty.name)}</small>
    </div>
  `,
          )
          .join("")
      : '<div class="display-next"><span>No hay pacientes</span></div>',
  );

  // Lista de siguiente consulta
  html(
    "display-consultation-list",
    forConsultation.length
      ? forConsultation
          .map(
            (item) => `
    <div class="display-next">
      <strong>${escapeHtml(item.ticket)}</strong>
      <span>${escapeHtml(item.patient.full_name)}</span>
      <small>${escapeHtml(item.specialty.name)}</small>
    </div>
  `,
          )
          .join("")
      : '<div class="display-next"><span>No hay pacientes</span></div>',
  );
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
      await apiPost(`/api/appointments/${button.dataset.callTriage}/call`, {
        target: "triage",
      });
      showToast("Paciente llamado a triaje", "success");
      await loadState();
      renderDisplay(); // Actualizar display inmediatamente
    } else if (button.dataset.startTriage) {
      try {
        const result = await apiPost(`/api/triage/${button.dataset.startTriage}/activate`);
        selectedTriageId = Number(button.dataset.startTriage);
        // Limpiar datos anteriores antes de cargar nuevos
        document.getElementById("vitals-form").reset();
        html("triage-analysis", ""); // Limpiar tabla ML anterior
        syncIoTToForm();
        showToast("Paciente activo para triaje", "success");
        await loadState();
        renderTriage(); // Forzar renderizado inmediata
      } catch (err) {
        showToast(err.message || "Error al activar triaje", "error");
      }
    } else if (button.dataset.callDoctor) {
      await apiPost(`/api/appointments/${button.dataset.callDoctor}/call`, {
        target: "doctor",
      });
      showToast("Paciente llamado a consultorio", "success");
      await loadState();
      renderDisplay(); // Actualizar display inmediatamente
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
      // Forzar re-render para actualizar la lista de recetas pendientes
      renderViews();
      // Verificar stock inmediatamente después de dispensar
      lastLowStockCheck = 0;
      checkLowStock();
    } else if (button.id === "sync-iot-button") {
      syncIoTToForm();
    } else if (button.id === "add-medicine-button") {
      addMedicineRow();
      showToast("Medicamento agregado", "success");
    } else if (button.id === "btn-ml-mostrar") {
      mlMostrarConfiguracion();
    } else if (button.id === "btn-ml-entrenar") {
      mlEntrenarModelo();
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
    } else if (button.dataset.patientHistory) {
      // Show patient clinical history - navigate to admin patients panel
      selectedClinicalHistoryPatientId = Number(button.dataset.patientHistory);
      showToast("Cargando historial clínico...", "info");
      switchView("admin");
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        switchAdminTab("patients");
        // Scroll to clinical history section
        document.getElementById("patient-clinical-history")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
      return;
    } else if (button.dataset.patientEdit) {
      // Load patient data into form for editing
      const patient = appState.patients.find(p => p.id === Number(button.dataset.patientEdit));
      if (patient) {
        const form = document.getElementById("admin-patient-form");
        if (form) {
          form.elements.id.value = patient.id;
          form.elements.document.value = patient.document || "";
          form.elements.first_name.value = patient.first_name || patient.name || "";
          form.elements.last_name.value = patient.last_name || "";
          form.elements.birth_date.value = patient.birth_date || "";
          form.elements.age.value = patient.age || "";
          form.elements.sex.value = patient.sex || patient.gender || "";
          form.elements.phone.value = patient.phone || "";
        }
        showToast("Paciente cargado para editar", "info");
      }
    } else if (button.dataset.patientDelete) {
      // Delete patient with confirmation
      if (confirm("¿Está seguro de eliminar este paciente?")) {
        await deleteAdmin("patients", button.dataset.patientDelete);
        showToast("Paciente eliminado", "success");
        await loadState();
      }
    } else if (button.dataset.historyPatient) {
      selectedClinicalHistoryPatientId = Number(button.dataset.historyPatient);
      switchView("admin");
      switchAdminTab("patients");
      return;
    } else if (button.dataset.action === "close-history") {
      selectedClinicalHistoryPatientId = null;
      html("patient-clinical-history", renderPatientClinicalHistory());
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
      if (!selectedTriageId)
        throw new Error("Seleccione un paciente para triaje");
      const data = { vitals: formData(form), source: "IoT simulado" };
      const result = await apiPost(
        `/api/triage/${selectedTriageId}/capture`,
        data,
      );
      html("triage-analysis", analysisMlBox(result.analysis));
      selectedTriageId = null;
      form.reset();
      showToast("Triaje guardado", "success");
      await loadState();
      renderTriage(); // Quitar paciente de la cola
      renderDisplay(); // Actualizar display
    } else if (form.id === "consultation-form") {
      if (!selectedConsultationId) throw new Error("Seleccione un paciente");
      const data = formData(form);
      data.receta_items = prescriptionItems();
      await apiPost(`/api/consultations/${selectedConsultationId}`, data);
      selectedConsultationId = null;
      form.reset();
      html("medicine-list", "");
      showToast("Consulta registrada", "success");
      await loadState();
    } else if (
      [
        "admin-patient-form",
        "worker-form",
        "consultorio-form",
        "medication-form",
      ].includes(form.id)
    ) {
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
  // No llamar a renderViews() al escribir en campos de búsqueda - causa scroll reset
  if (event.target.matches('#worker-form select[name="role"]'))
    updateWorkerSpecialtyState();
  if (event.target.id === "history-patient-selector") {
    selectedClinicalHistoryPatientId = Number(event.target.value);
    html("patient-clinical-history", renderPatientClinicalHistory());
  }
  if (event.target.id === "patient-search") {
    const query = event.target.value.trim();
    if (query.length < 2) {
      html("patient-search-results", "");
      return;
    }
    const data = await apiGet(
      `/api/patients/search?q=${encodeURIComponent(query)}`,
    );
    html(
      "patient-search-results",
      (data.patients || [])
        .map(
          (patient) => `
      <article class="queue-card" data-select-patient="${patient.id}">
        <div><strong>${escapeHtml(patient.first_name)} ${escapeHtml(patient.last_name)}</strong><span>${escapeHtml(patient.document)} · ${patient.age} años</span></div>
      </article>
    `,
        )
        .join("") || empty("Sin resultados"),
    );
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
  showToast(
    type === "patient" ? "Paciente dado de baja" : "Registro eliminado",
    "success",
  );
}

function editAdmin(type, id) {
  const maps = {
    patient: ["admin-patient-form", appState.patients],
    worker: ["worker-form", appState.workers],
    consultorio: ["consultorio-form", appState.consultorios],
    medication: ["medication-form", appState.medications],
  };
  const [formId, collection] = maps[type];
  fillForm(
    formId,
    collection.find((item) => Number(item.id) === Number(id)),
  );
  setIdentityLocked(document.getElementById(formId), true);
  if (formId === "worker-form") updateWorkerSpecialtyState();
}

function addMedicineRow(item = {}) {
  const options = appState.medications
    .map((med) => {
      return `<option value="${escapeHtml(med.name)}" data-price="${med.price}">${escapeHtml(med.name)} - ${money(med.price)}</option>`;
    })
    .join("");
  document.getElementById("medicine-list").insertAdjacentHTML(
    "beforeend",
    `
    <div class="medicine-row">
      <div class="field-group">
        <label>Medicamento</label>
        <select name="medicamento">${options}</select>
      </div>
      <div class="field-group">
        <label>Dosis (por toma)</label>
        <input name="dosage" type="number" min="1" value="${item.dosage || 1}" placeholder="1">
      </div>
      <div class="field-group">
        <label>Cada (horas)</label>
        <input name="frequency" type="number" min="1" value="${item.frequency || 8}" placeholder="8">
      </div>
      <div class="field-group">
        <label>Días</label>
        <input name="days" type="number" min="1" value="${item.days || 3}" placeholder="3">
      </div>
      <div class="field-group">
        <label>Precio und. (S/)</label>
        <input name="precio_unitario" step="0.01" type="number" value="${item.unit_price || medicationPrice(appState.medications[0])}" placeholder="0.00">
      </div>
      <button class="danger-button" data-remove-medicine="1" type="button">X</button>
    </div>
  `,
  );
}

function prescriptionItems() {
  return Array.from(
    document.querySelectorAll("#medicine-list .medicine-row"),
  ).map((row) => {
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
  return items.length
    ? items
        .map(
          (item) => `
    <article class="queue-card">
      <div><strong>${escapeHtml(title(item))}</strong><span>${escapeHtml(subtitle(item))}</span></div>
      <div class="card-actions">
        <button class="secondary-button" data-edit="${type}" data-id="${item.id}" type="button">Editar</button>
        <button class="danger-button" data-delete="${type}" data-id="${item.id}" type="button">Eliminar</button>
      </div>
    </article>
  `,
        )
        .join("")
    : empty("Sin registros");
}

// Mapa para guardar selecciones de pago por prescription ID (Farmacia)
let pharmacyPaymentSelections = {};

function prescriptionCard(item) {
  const savedMethod = pharmacyPaymentSelections[item.id] || "Efectivo";

  const rows = (item.items || [])
    .map((med) => {
      const dosage = med.dosage || "-";
      const frequency = med.frequency || "-";
      const days = med.days ?? "-";
      const quantity = med.quantity ?? "-";
      const unitPrice = Number(med.unit_price) || 0;
      const totalPrice = Number(med.quantity) ? unitPrice * Number(med.quantity) : unitPrice;
      return `<li><span class="med-name">${escapeHtml(med.medicine)}</span><span>${escapeHtml(String(dosage))}</span><span>${escapeHtml(String(frequency))}</span><span>${escapeHtml(String(days))}</span><span>${escapeHtml(String(quantity))} und.</span><span class="med-price">${money(totalPrice)}</span></li>`;
    })
    .join("");

  return `<article class="prescription-card prescription-pending-card">
    <div class="prescription-header">
      <div class="prescription-ticket"><span class="pill-badge">${escapeHtml(item.ticket)}</span></div>
      <div class="prescription-patient">
        <strong>${escapeHtml(item.patient_name)}</strong>
        <small>DNI ${escapeHtml(item.patient_document)}</small>
      </div>
      <div class="prescription-diagnosis">${escapeHtml(item.diagnosis || "Sin dx")}</div>
    </div>
    <div class="prescription-items">
      <div class="items-header"><span>Medicamento</span><span>Dosis</span><span>Frecuencia</span><span>Dias</span><span>Cant.</span><span>Precio</span></div>
      <ul class="items-list">${rows}</ul>
    </div>
    <div class="prescription-footer">
      <div class="prescription-total"><span>Total:</span><strong>${money(item.total)}</strong></div>
      <div class="card-actions payment-actions">
        ${paymentMethodSelect("payment_method", savedMethod)}
        <button class="primary-button" data-dispense="${item.id}" type="button">Entregar</button>
      </div>
    </div>
  </article>`;
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
      <div><span>Regresion lineal</span><strong>PA sistolica esperada: ${analysis.predicted_systolic}</strong><p>Compara la presion real con una presion esperada por frecuencia cardiaca.</p></div>
      <div><span>Regresion lineal multiple</span><strong>Consulta estimada: ${analysis.estimated_attention_minutes} min</strong><p>Calcula tiempo probable usando edad, signos vitales e IMC.</p></div>
      <div><span>Regresion logistica</span><strong>Probabilidad de riesgo: ${Math.round(analysis.risk_probability * 100)}%</strong><p>Convierte los signos vitales en una probabilidad de riesgo clinico.</p></div>
      <div><span>Arbol de decision</span><strong>Prioridad: ${escapeHtml(analysis.priority)}</strong><p>Define la prioridad operativa para ordenar la atencion.</p></div>
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
    [
      "PA",
      `${vitals.blood_pressure_systolic ?? "--"}/${vitals.blood_pressure_diastolic ?? "--"}`,
    ],
    ["Peso", `${vitals.weight ?? "--"} kg`],
    ["Talla", `${vitals.height ?? "--"} cm`],
  ];
  html(
    targetId,
    items
      .map(
        ([label, valueText]) =>
          `<div class="vital-chip"><span>${label}</span><strong>${valueText}</strong></div>`,
      )
      .join(""),
  );
}

function metric(label, valueText) {
  return `<div class="metric-card"><span>${label}</span><strong>${valueText}</strong></div>`;
}

function totalRevenue() {
  // Use transacciones table directly for consistency with Admin TRANSACCIONES
  // Only count 'paid' transactions (both cash register and pharmacy)
  const transactions = appState.transactions || [];
  return transactions
    .filter((t) => t.status === "paid")
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
}

function matchesAppointment(item, query) {
  return (
    !query ||
    [
      item.ticket,
      item.patient.full_name,
      item.patient.document,
      item.specialty.name,
    ]
      .join(" ")
      .toLowerCase()
      .includes(query)
  );
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

function paymentMethodSelect(name = "payment_method", defaultValue = "Efectivo") {
  return `<label class="payment-select">Metodo
    <select name="${name}">
      ${PAYMENT_METHODS.map((method) => `<option value="${escapeHtml(method)}" ${method === defaultValue ? 'selected' : ''}>${escapeHtml(method)}</option>`).join("")}
    </select>
  </label>`;
}

function selectedPaymentMethod(button) {
  return (
    button
      .closest(".queue-card")
      ?.querySelector('select[name="payment_method"]')?.value || "Efectivo"
  );
}

function transactionFor(module, referenceType, referenceId) {
  return appState.transactions.find((item) => {
    return (
      item.module === module &&
      item.reference_type === referenceType &&
      Number(item.reference_id) === Number(referenceId)
    );
  });
}

function statusText(valueText) {
  return (
    {
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
    }[valueText] ||
    valueText ||
    "--"
  );
}

function statusLabel(valueText) {
  const good = ["paid", "done", "completed", "dispensed"];
  const warn = ["pending", "waiting", "registered", "prescription_pending"];
  const type = good.includes(valueText)
    ? "ok"
    : warn.includes(valueText)
      ? "pending"
      : "info";
  return `<span class="status-label status-${type}">${statusText(valueText)}</span>`;
}

// Verificar stock bajo de medicamentos (solo para admin y pharmacy)
let lastLowStockCheck = 0;
function checkLowStock() {
  const now = Date.now();
  if (now - lastLowStockCheck < 30000) return; // Evitar spam cada 30 segundos
  lastLowStockCheck = now;

  const role = currentUser?.role;
  if (role !== "admin" && role !== "pharmacy") return;

  const lowStockMeds = appState.medications.filter((m) => m.stock < 10 && m.active === 1);
  if (lowStockMeds.length === 0) return;

  const names = lowStockMeds.map((m) => `${m.name} (${m.stock})`).join(", ");
  showToast(`Stock bajo: ${names}`, "warning");
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
  if (!identity.age && identity.birth_date)
    identity.age = calculateAge(identity.birth_date) || "";
  API_IDENTITY_FIELDS.forEach((fieldName) => {
    const field = form.elements[fieldName];
    const nextValue = identity[fieldName];
    if (
      !field ||
      nextValue === undefined ||
      nextValue === null ||
      nextValue === ""
    )
      return;
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
  const allowedKeys = [
    "Tab",
    "Shift",
    "Control",
    "Alt",
    "Meta",
    "Escape",
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "ArrowDown",
    "Home",
    "End",
  ];
  return (
    allowedKeys.includes(event.key) ||
    event.ctrlKey ||
    event.metaKey ||
    event.altKey
  );
}

function updateWorkerSpecialtyState() {
  const form = document.getElementById("worker-form");
  if (!form) return;
  const field = form.querySelector(".worker-specialty-field");
  const specialty = form.elements.specialty;
  const isDoctor = form.elements.role.value === "medico";
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
    ? appState.specialties
        .map(
          (item) =>
            `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`,
        )
        .join("")
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
  if (
    form.id === "worker-form" &&
    form.elements.role.value === "medico" &&
    !form.elements.specialty.value
  ) {
    throw new Error("Seleccione especialidad para el medico.");
  }
  if (!form.checkValidity()) {
    form.reportValidity();
    throw new Error("Complete los campos obligatorios correctamente.");
  }
}

function renderBarChart(targetId, items) {
  const total = Math.max(
    1,
    items.reduce((sum, item) => sum + Number(item.value || 0), 0),
  );
  html(
    targetId,
    items
      .map((item) => {
        const percent = Math.round((Number(item.value || 0) / total) * 100);
        return `<div class="bar-row">
      <span>${escapeHtml(item.label)}</span>
      <div class="bar-track"><i style="width:${percent}%"></i></div>
      <strong>${item.value}</strong>
    </div>`;
      })
      .join("") || empty("Sin datos"),
  );
}

function renderRegressionChart(targetId, points) {
  if (!points.length) {
    html(targetId, empty("Sin datos"));
    return;
  }
  const maxValue = Math.max(
    ...points.flatMap((point) => [
      point.actual_systolic,
      point.predicted_systolic,
      1,
    ]),
  );
  html(
    targetId,
    `<div class="paired-bars">${points
      .map((point) => {
        const actual = Math.round((point.actual_systolic / maxValue) * 100);
        const predicted = Math.round(
          (point.predicted_systolic / maxValue) * 100,
        );
        return `<div class="paired-bar">
      <small>FC ${Math.round(point.heart_rate)}</small>
      <span class="actual" style="height:${actual}%"></span>
      <span class="predicted" style="height:${predicted}%"></span>
    </div>`;
      })
      .join("")}</div>
  <div class="chart-legend"><span class="dot actual"></span> Real <span class="dot predicted"></span> Predicha</div>`,
  );
}

function renderAttentionChart(targetId, points) {
  if (!points.length) {
    html(targetId, empty("Sin datos"));
    return;
  }
  const maxMinutes = Math.max(
    ...points.map((point) => Number(point.minutes || 0)),
    1,
  );
  html(
    targetId,
    `<div class="attention-chart">${points
      .map((point) => {
        const height = Math.round(
          (Number(point.minutes || 0) / maxMinutes) * 100,
        );
        return `<div class="attention-point">
      <span style="height:${height}%"></span>
      <small>${Math.round(point.risk)}%</small>
    </div>`;
      })
      .join("")}</div>
  <div class="chart-legend">Barras: minutos estimados. Etiqueta: riesgo logistico.</div>`,
  );
}

// Gráfico de Matriz de Confusión (como parte2.py del profesor)
function renderConfusionMatrix(targetId, matrix) {
  if (!matrix || matrix.length < 2) {
    html(targetId, empty("Sin datos de matriz"));
    return;
  }
  const labels = matrix.map((row) => row.label || "Clase");
  html(
    targetId,
    `<div class="confusion-matrix">
      <div class="matrix-header">${labels.map((l) => `<span>${l}</span>`).join("")}</div>
      ${matrix.map((row, i) => `
        <div class="matrix-row">
          <span class="matrix-label">${row.label || labels[i]}</span>
          ${row.values.map((val, j) => {
            const max = Math.max(...matrix.flatMap((r) => r.values));
            const intensity = Math.round((val / max) * 100);
            const isDiagonal = i === j;
            return `<span class="matrix-cell ${isDiagonal ? "correct" : "incorrect"}" style="opacity:${intensity / 100}">${val}</span>`;
          }).join("")}
        </div>
      `).join("")}
    </div>
    <div class="chart-legend">Diagonal: predicciones correctas</div>`,
  );
}

// Gráfico de Curva ROC (como parte2.py del profesor)
function renderRocCurve(targetId, points) {
  if (!points || points.length < 2) {
    html(targetId, empty("Sin datos para curva ROC"));
    return;
  }
  // points: [{fpr, tpr}, ...]
  const maxX = Math.max(...points.map((p) => p.fpr || 0), 1);
  const maxY = Math.max(...points.map((p) => p.tpr || 0), 1);
  const auc = points.reduce((sum, p, i) => {
    if (i === 0) return 0;
    const prev = points[i - 1];
    return sum + ((p.tpr || 0) + (prev.tpr || 0)) * ((p.fpr || 0) - (prev.fpr || 0)) / 2;
  }, 0);
  const pathData = points.map((p, i) => {
    const x = Math.round(((p.fpr || 0) / maxX) * 100);
    const y = 100 - Math.round(((p.tpr || 0) / maxY) * 100);
    return `${i === 0 ? "M" : "L"}${x},${y}`;
  }).join(" ");
  html(
    targetId,
    `<div class="roc-chart">
      <svg viewBox="0 0 120 120" class="roc-svg">
        <line x1="10" y1="110" x2="110" y2="10" class="diagonal" />
        <path d="${pathData}" class="roc-path" />
        <circle cx="10" cy="110" r="2" class="roc-point" />
        <circle cx="110" cy="10" r="2" class="roc-point" />
      </svg>
      <div class="roc-labels">
        <span>FPR</span>
        <span class="roc-title">TPR</span>
      </div>
    </div>
    <div class="chart-legend">AUC = ${Math.round(auc * 100) / 100}</div>`,
  );
}

// Gráfico de Comparación de Algoritmos (como parte2.py del profesor)
function renderAlgorithmComparison(targetId, algorithms) {
  if (!algorithms || algorithms.length < 2) {
    html(targetId, empty("Sin datos para comparar"));
    return;
  }
  const maxAccuracy = Math.max(...algorithms.map((a) => a.accuracy || 0), 1);
  html(
    targetId,
    `<div class="algorithm-comparison">${algorithms
      .map((alg) => {
        const width = Math.round(((alg.accuracy || 0) / maxAccuracy) * 100);
        const color = (alg.accuracy || 0) >= 0.8 ? "#22c55e" : (alg.accuracy || 0) >= 0.6 ? "#f59e0b" : "#ef4444";
        return `<div class="alg-bar">
          <span class="alg-name">${alg.name}</span>
          <div class="alg-track"><i style="width:${width}%;background:${color}"></i></div>
          <span class="alg-acc">${((alg.accuracy || 0) * 100).toFixed(1)}%</span>
        </div>`;
      })
      .join("")}</div>
    <div class="chart-legend">Accuracy (validación cruzada 5-fold)</div>`,
  );
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
  if (
    monthDelta < 0 ||
    (monthDelta === 0 && today.getDate() < birthDate.getDate())
  )
    age -= 1;
  return Math.max(0, age);
}

// Field name mapping: frontend HTML -> backend API
const FIELD_MAP = {
  document: "documento",
  first_name: "nombre",
  last_name: "apellido",
  age: "edad",
  sex: "sexo",
  phone: "telefono",
  birth_date: "fecha_nacimiento",
  specialty_id: "id_especialidad",
  tratamiento_notas: "tratamiento",
};

function formData(form) {
  const data = {};
  Array.from(form.elements).forEach((field) => {
    if (!field.name || ["button", "submit", "reset"].includes(field.type))
      return;
    const valueText = field.value;
    const key = FIELD_MAP[field.name] || field.name;
    data[key] = ["document", "phone"].includes(field.name)
      ? onlyDigits(valueText)
      : valueText;
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
  if (!response.ok) {
    const message = data.message || data.error || "Error del servidor";
    const fullError = data.trace ? message + "\n" + data.trace : message;
    console.error("API Error:", fullError);
    throw new Error(fullError);
  }
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
  return String(valueText ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[char],
  );
}

function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  const label =
    {
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














