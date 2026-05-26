const form = document.querySelector("#classifyForm");
const input = document.querySelector("#claimInput");
const button = document.querySelector("#analyzeButton");
const buttonText = document.querySelector("#buttonText");
const dashboard = document.querySelector(".dashboard");
const resultPanel = document.querySelector(".result-panel");
const statusText = document.querySelector("#statusText");
const resultMessage = document.querySelector("#resultMessage");
const confidenceText = document.querySelector("#confidenceText");
const meterFill = document.querySelector("#meterFill");
const bulbs = document.querySelectorAll(".bulb");

const states = {
  True: {
    state: "true",
    status: "VERDADEIRO",
    message: "A afirmação parece verdadeira.",
    icon: "V",
  },
  Fake: {
    state: "fake",
    status: "FAKE",
    message: "A afirmação parece falsa.",
    icon: "!",
  },
  Inconclusiva: {
    state: "inconclusive",
    status: "INDEFINIDO...",
    message: "Não dá para saber.",
    icon: "?",
  },
};

function setBulb(state) {
  bulbs.forEach((bulb) => bulb.classList.remove("is-on"));

  const target = {
    true: ".bulb-true",
    fake: ".bulb-fake",
    inconclusive: ".bulb-inconclusive",
  }[state];

  if (target) {
    document.querySelector(target).classList.add("is-on");
  }
}

function setResult(classification, confidence) {
  const result = states[classification] || states.Inconclusiva;
  const safeConfidence = Math.max(0, Math.min(100, Number(confidence) || 0));

  dashboard.dataset.state = result.state;
  dashboard.classList.remove("is-loading");
  resultPanel.classList.add("has-output");
  setBulb(result.state);

  statusText.textContent = result.status;
  document.querySelector(".status-icon").textContent = result.icon;
  resultMessage.textContent = result.message;
  confidenceText.textContent = `${safeConfidence}%`;
  meterFill.style.width = `${safeConfidence}%`;
}

function setLoading() {
  dashboard.dataset.state = "idle";
  dashboard.classList.add("is-loading");
  resultPanel.classList.add("has-output");
  statusText.textContent = "ANALISANDO...";
  document.querySelector(".status-icon").textContent = "...";
  resultMessage.textContent = "Consultando o modelo treinado.";
  confidenceText.textContent = "--";
  meterFill.style.width = "100%";
  button.disabled = true;
  buttonText.textContent = "ANALISANDO";
}

function resetButton() {
  button.disabled = false;
  buttonText.textContent = "ANALISAR";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();

  if (!text) {
    input.focus();
    return;
  }

  setLoading();

  try {
    const response = await fetch("/api/classify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Não foi possível analisar.");
    }

    setResult(data.classification, data.confidence);
  } catch (error) {
    setResult("Inconclusiva", 0);
    resultMessage.textContent = error.message;
  } finally {
    resetButton();
  }
});

input.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    form.requestSubmit();
  }
});
