const healthCard = document.querySelector("#health-card");
const healthIndicator = document.querySelector("#health-indicator");
const healthLabel = document.querySelector("#health-label");
const healthMessage = document.querySelector("#health-message");
const serviceName = document.querySelector("#service-name");
const serviceVersion = document.querySelector("#service-version");
const checkedAt = document.querySelector("#checked-at");
const checkButton = document.querySelector("#check-again");

function setHealthState(state, label, message) {
  healthIndicator.className = `health-indicator ${state}`;
  healthLabel.textContent = label;
  healthMessage.textContent = message;
}

async function checkHealth() {
  checkButton.disabled = true;
  healthCard.setAttribute("aria-busy", "true");
  setHealthState("pending", "Verificando servicio", "Consultando el estado actual de la API...");

  try {
    const response = await fetch("/healthz", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`La API respondió con el código ${response.status}.`);
    }

    const health = await response.json();
    const isHealthy = health.status === "healthy";
    serviceName.textContent = health.service;
    serviceVersion.textContent = health.version;
    setHealthState(
      isHealthy ? "healthy" : "unhealthy",
      isHealthy ? "Todos los sistemas operativos" : "Servicio con inconvenientes",
      isHealthy ? "La API está respondiendo correctamente." : "La API respondió, pero reportó un estado no saludable.",
    );
  } catch (error) {
    setHealthState("unhealthy", "Servicio no disponible", error.message);
  } finally {
    checkedAt.textContent = new Intl.DateTimeFormat("es-AR", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date());
    healthCard.setAttribute("aria-busy", "false");
    checkButton.disabled = false;
  }
}

checkButton.addEventListener("click", checkHealth);
window.setInterval(checkHealth, 30_000);
checkHealth();
