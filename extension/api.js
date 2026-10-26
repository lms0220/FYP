// Shared by the popup and the background worker.
const API_URL = "http://localhost:5000/api/check-url";
const CACHE_MS = 10 * 60 * 1000;

async function checkUrl(url) {
  const key = "cache:" + url;
  const cached = (await chrome.storage.session.get(key))[key];
  if (cached && Date.now() - cached.at < CACHE_MS) return cached.result;

  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) throw new Error("Backend returned " + response.status);
  const result = await response.json();
  await chrome.storage.session.set({ [key]: { at: Date.now(), result } });
  return result;
}

function isCheckable(url) {
  return /^https?:\/\//i.test(url || "") && !/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(url);
}
