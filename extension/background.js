importScripts("api.js");

// Automatic checking sends every visited page URL to the backend, so it is
// opt-in. Toggle it from the popup.
chrome.tabs.onUpdated.addListener(async (tabId, change, tab) => {
  if (change.status !== "complete" || !isCheckable(tab.url)) return;
  const { autoCheck } = await chrome.storage.local.get("autoCheck");
  if (!autoCheck) return;

  try {
    const result = await checkUrl(tab.url);
    const bad = result.prediction === "MALICIOUS";
    chrome.action.setBadgeText({ tabId, text: bad ? "!" : "OK" });
    chrome.action.setBadgeBackgroundColor({ tabId, color: bad ? "#d93025" : "#188038" });
  } catch {
    chrome.action.setBadgeText({ tabId, text: "" });
  }
});
