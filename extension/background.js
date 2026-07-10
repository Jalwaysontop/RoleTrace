// RoleTrace Background Service Worker
// Opens the side panel automatically when user is on an apply page

const APPLY_PATTERNS = [
  "roletrace.duckdns.org/apply",
  "localhost:8000/apply"
];

function isApplyPage(url) {
  if (!url) return false;
  return APPLY_PATTERNS.some(p => url.includes(p));
}

// Open side panel when tab navigates to apply page
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && isApplyPage(tab.url)) {
    chrome.sidePanel.open({ tabId }).catch(() => {});
  }
});

// Also open side panel when extension icon is clicked
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id }).catch(() => {});
});

// Set side panel behavior: open on action click
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
