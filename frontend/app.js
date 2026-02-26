const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const bubbleTemplate = document.getElementById("bubbleTemplate");
const collegeSearchInput = document.getElementById("collegeSearchInput");
const collegeSearchBtn = document.getElementById("collegeSearchBtn");
const directoryStatus = document.getElementById("directoryStatus");
const schoolResults = document.getElementById("schoolResults");
const majorInput = document.getElementById("majorInput");
const yearInput = document.getElementById("yearInput");
const interestsInput = document.getElementById("interestsInput");
const completedInput = document.getElementById("completedInput");
const quickButtons = document.querySelectorAll(".quick-btn");

const history = [];
let collegeOptions = [];
let directoryEnabled = false;
let schoolSearchDebounce = null;
let schoolSearchRequestSeq = 0;
let selectedCollege = null;

const openingMessage =
  "Hi, I am your AI academic advisor. I can build a 4-year schedule, check prerequisites, suggest electives, and warn about graduation requirements.";
appendMessage("assistant", openingMessage);

loadProgramOptions();

quickButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    chatInput.value = btn.dataset.message || "";
    chatInput.focus();
  });
});

collegeSearchBtn.addEventListener("click", () => {
  searchSchools(collegeSearchInput.value.trim());
});

collegeSearchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchSchools(collegeSearchInput.value.trim());
  }
});

collegeSearchInput.addEventListener("input", () => {
  if (!directoryEnabled) {
    directoryStatus.textContent =
      "School directory API not configured. Set COLLEGESCORECARD_API_KEY and restart backend.";
    return;
  }
  const query = collegeSearchInput.value.trim();
  if (schoolSearchDebounce) clearTimeout(schoolSearchDebounce);

  // Avoid hammering the API while typing; empty input is allowed only via explicit Search click.
  if (query.length > 0 && query.length < 2) {
    directoryStatus.textContent = "Type at least 2 letters to search, or click Search to load all schools";
    return;
  }

  if (!query) {
    directoryStatus.textContent = "US directory connected. Type to search, or click Search to load all schools";
    return;
  }

  schoolSearchDebounce = setTimeout(() => {
    searchSchools(query);
  }, 300);
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  history.push({ role: "user", content: message });
  chatInput.value = "";
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        history,
        profile: {
          college: selectedCollege?.raw_name || "",
          college_id: selectedCollege?.school_id || "",
          major: majorInput.value.trim(),
          year: yearInput.value.trim(),
          interests: interestsInput.value.trim(),
          completed_courses: completedInput.value.trim(),
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Server error (${response.status})`);
    }

    const data = await response.json();
    const reply = data.reply || "Please share a bit more detail so I can help.";
    const mode = data.mode ? ` [mode: ${data.mode}]` : "";
    const renderedReply = `${reply}${mode}`;
    appendMessage("assistant", renderedReply);
    history.push({ role: "assistant", content: reply });
  } catch (error) {
    appendMessage(
      "assistant",
      "I am having trouble connecting right now. Please try again in a moment."
    );
  } finally {
    setBusy(false);
    chatInput.focus();
  }
});

function appendMessage(role, text) {
  const node = bubbleTemplate.content.cloneNode(true);
  const wrap = node.querySelector(".bubble-wrap");
  const bubble = node.querySelector(".bubble");
  wrap.classList.add(role);
  bubble.textContent = text;
  chatLog.appendChild(node);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  sendBtn.textContent = busy ? "Sending..." : "Send";
  chatInput.disabled = busy;
}

async function loadProgramOptions() {
  await loadDirectoryStatus();
  if (directoryEnabled) {
    directoryStatus.textContent =
      "US directory connected. Type at least 2 letters to search, or click Search to load all schools";
    return;
  }
  try {
    const response = await fetch("/api/options");
    if (!response.ok) return;
    const data = await response.json();
    collegeOptions = (data.colleges || []).map((c) => ({
      name: c.name,
      raw_name: c.name,
      school_id: "",
      majors: c.majors || [],
    }));
    schoolResults.innerHTML = "";
    selectedCollege = null;
    populateMajors(data.default_college || "", data.default_major || "", false);
    directoryStatus.textContent = "Directory API not configured (using local sample programs)";
  } catch (error) {
    appendMessage(
      "assistant",
      "Could not load college/major options from /api/options. Restart the backend and refresh the page."
    );
  }
}

async function loadDirectoryStatus() {
  try {
    const response = await fetch("/api/directory/status");
    if (!response.ok) return;
    const data = await response.json();
    directoryEnabled = Boolean(data.enabled);
    directoryStatus.textContent = directoryEnabled
      ? "US directory connected"
      : "Directory API not configured";
  } catch (error) {
    directoryStatus.textContent = "Directory status unavailable";
  }
}

async function searchSchools(query) {
  if (!directoryEnabled) {
    directoryStatus.textContent =
      "School directory API not configured. Set COLLEGESCORECARD_API_KEY and restart backend.";
    schoolResults.innerHTML = "";
    return;
  }

  if (directoryEnabled && query.length > 0 && query.length < 2) {
    directoryStatus.textContent = "Type at least 2 letters to search";
    return;
  }

  const requestSeq = ++schoolSearchRequestSeq;
  directoryStatus.textContent = query
    ? `Searching schools for "${query}"...`
    : "Loading all U.S. schools (this may take a few seconds)...";

  try {
    const response = await fetch(`/api/schools/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error("School search failed");
    const data = await response.json();
    if (requestSeq !== schoolSearchRequestSeq) return;
    const results = data.results || [];

    if (!results.length) {
      directoryStatus.textContent = directoryEnabled
        ? "No schools found. Try a different search."
        : "Directory API not configured";
      return;
    }

    collegeOptions = results.map((s) => ({
      name: s.label || s.name,
      raw_name: s.name,
      school_id: String(s.school_id || ""),
      majors: [],
    }));
    renderSchoolResults(collegeOptions, collegeOptions[0]?.name || "", "", true);
    directoryStatus.textContent = query
      ? `Loaded ${results.length} schools for "${query}"`
      : `Loaded ${results.length} schools`;
  } catch (error) {
    if (requestSeq !== schoolSearchRequestSeq) return;
    directoryStatus.textContent = "School search failed";
  }
}

function renderSchoolResults(results, defaultCollegeName, defaultMajor, loadMajorsFromApi) {
  schoolResults.innerHTML = "";

  if (!results.length) {
    selectedCollege = null;
    populateMajors("", "", false);
    return;
  }

  const maxVisible = 80;
  const visibleResults = results.slice(0, maxVisible);
  visibleResults.forEach((college) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "school-result-btn";
    button.textContent = college.name;
    button.dataset.collegeName = college.name;
    button.addEventListener("click", () => {
      setSelectedCollege(college, "", loadMajorsFromApi);
    });
    schoolResults.appendChild(button);
  });

  if (results.length > maxVisible) {
    const more = document.createElement("div");
    more.className = "school-results-more";
    more.textContent = `Showing first ${maxVisible} of ${results.length} schools. Refine your search to narrow results.`;
    schoolResults.appendChild(more);
  }

  const initialCollege =
    results.find((c) => c.name === defaultCollegeName) ||
    results.find((c) => c.raw_name === defaultCollegeName) ||
    results[0];
  setSelectedCollege(initialCollege, defaultMajor, loadMajorsFromApi);
}

async function setSelectedCollege(college, preferredMajor = "", loadMajorsFromApi = false) {
  selectedCollege = college || null;

  Array.from(schoolResults.querySelectorAll(".school-result-btn")).forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.collegeName === (college?.name || ""));
  });

  await populateMajors(college?.name || "", preferredMajor, loadMajorsFromApi);
}

async function populateMajors(collegeName, preferredMajor, loadFromApi = false) {
  majorInput.innerHTML = "";
  const college = collegeOptions.find((item) => item.name === collegeName);
  let majors = college?.majors || [];

  if (loadFromApi && college?.school_id) {
    majors = await fetchMajorsForSchool(college.school_id);
    college.majors = majors;
  }

  majors.forEach((major) => {
    const option = document.createElement("option");
    option.value = major;
    option.textContent = major;
    majorInput.appendChild(option);
  });

  if (majors.length === 0) {
    const fallback = document.createElement("option");
    fallback.value = "";
    fallback.textContent = "No majors available";
    majorInput.appendChild(fallback);
    return;
  }

  if (preferredMajor && majors.includes(preferredMajor)) {
    majorInput.value = preferredMajor;
  } else {
    majorInput.value = majors[0];
  }
}

async function fetchMajorsForSchool(schoolId) {
  try {
    majorInput.innerHTML = "";
    const loading = document.createElement("option");
    loading.value = "";
    loading.textContent = "Loading majors...";
    majorInput.appendChild(loading);
    const response = await fetch(`/api/majors/search?school_id=${encodeURIComponent(schoolId)}`);
    if (!response.ok) throw new Error("Major search failed");
    const data = await response.json();
    const majors = (data.results || []).filter(Boolean);
    if (majors.length) {
      directoryStatus.textContent = `Loaded ${majors.length} majors/programs`;
    }
    return majors.length ? majors : ["No majors found from directory"];
  } catch (error) {
    directoryStatus.textContent = "Major lookup failed";
    return ["Major list unavailable"];
  }
}
