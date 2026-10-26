const verdictEl = document.getElementById("verdict");
const detailEl = document.getElementById("detail");

async function run() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  document.getElementById("url").textContent = tab?.url || "";

  if (!isCheckable(tab?.url)) {
    verdictEl.textContent = "This page cannot be checked.";
    return;
  }

  try {
    const result = await checkUrl(tab.url);
    const bad = result.prediction === "MALICIOUS";
    verdictEl.textContent = `${bad ? "Likely malicious" : "Looks safe"} · ${result.risk_level} risk · score ${Math.round(result.score)}`;
    verdictEl.className = "verdict " + (bad ? "bad" : "good");
    detailEl.textContent = result.llm_analysis?.explanation || "";
  } catch {
    verdictEl.textContent = "Cannot reach the backend. Is it running on localhost:5000?";
  }
}

const auto = document.getElementById("auto");
chrome.storage.local.get("autoCheck").then(({ autoCheck }) => { auto.checked = !!autoCheck; });
auto.addEventListener("change", () => chrome.storage.local.set({ autoCheck: auto.checked }));

run();
