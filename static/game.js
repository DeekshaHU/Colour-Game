(() => {
  const colours = {
    RED: "#ff5f76",
    BLUE: "#5e9bff",
    GREEN: "#41d6a3",
    YELLOW: "#ffd166"
  };
  const colourNames = Object.keys(colours);
  const timerEl = document.getElementById("timer");
  if (!timerEl) return;

  const scoreEl = document.getElementById("score");
  const streakEl = document.getElementById("streak");
  const wordEl = document.getElementById("colour-word");
  const statusEl = document.getElementById("game-status");
  const progressEl = document.getElementById("time-progress");
  const startBtn = document.getElementById("start-btn");
  const answerButtons = [...document.querySelectorAll(".answer-btn")];
  const resultPanel = document.getElementById("result-panel");
  const nonceMeta = document.querySelector('meta[name="game-nonce"]');
  let nonce = nonceMeta ? nonceMeta.content : "";
  let running = false;
  let timeLeft = 30;
  let score = 0;
  let streak = 0;
  let correct = 0;
  let total = 0;
  let targetColour = "";
  let timerInterval = null;
  let accepting = false;

  function randomItem(items) {
    return items[Math.floor(Math.random() * items.length)];
  }

  function setButtonsEnabled(enabled) {
    answerButtons.forEach(button => { button.disabled = !enabled; });
  }

  function showChallenge() {
    const word = randomItem(colourNames);
    targetColour = randomItem(colourNames);
    // Avoid matching the word and its font colour so every challenge is unambiguous.
    while (targetColour === word) targetColour = randomItem(colourNames);
    wordEl.textContent = word;
    wordEl.style.color = colours[targetColour];
    accepting = true;
    statusEl.textContent = "Which colour are the letters?";
    statusEl.className = "game-status";
  }

  function updateTimer() {
    timerEl.textContent = `00:${String(timeLeft).padStart(2, "0")}`;
    progressEl.style.width = `${(timeLeft / 30) * 100}%`;
    progressEl.classList.toggle("low-time", timeLeft <= 10);
  }

  function startGame() {
    clearInterval(timerInterval);
    running = true;
    timeLeft = 30;
    score = 0;
    streak = 0;
    correct = 0;
    total = 0;
    accepting = false;
    scoreEl.textContent = score;
    streakEl.textContent = `${streak} ✦`;
    resultPanel.classList.add("hidden");
    startBtn.classList.add("hidden");
    updateTimer();
    setButtonsEnabled(true);
    showChallenge();
    timerInterval = setInterval(() => {
      timeLeft -= 1;
      updateTimer();
      if (timeLeft <= 0) finishGame();
    }, 1000);
  }

  function chooseColour(selected) {
    if (!running || !accepting) return;
    accepting = false;
    total += 1;
    if (selected === targetColour) {
      correct += 1;
      streak += 1;
      score += 10;
      statusEl.textContent = "Correct! +10 points";
      statusEl.className = "game-status good";
    } else {
      streak = 0;
      statusEl.textContent = `Not quite — the colour was ${targetColour}.`;
      statusEl.className = "game-status bad";
    }
    scoreEl.textContent = score;
    streakEl.textContent = `${streak} ✦`;
    // Brief feedback, then show the next challenge.
    setTimeout(() => {
      if (running) showChallenge();
    }, 260);
  }

  async function finishGame() {
    if (!running) return;
    running = false;
    accepting = false;
    clearInterval(timerInterval);
    timeLeft = 0;
    updateTimer();
    setButtonsEnabled(false);
    startBtn.classList.remove("hidden");
    startBtn.textContent = "Play again ↻";
    statusEl.textContent = "Round complete. Your result is ready.";
    statusEl.className = "game-status";
    document.getElementById("final-score").textContent = score;
    document.getElementById("final-correct").textContent = `${correct} / ${total}`;
    document.getElementById("final-accuracy").textContent = `${total ? Math.round((correct / total) * 100) : 0}%`;
    document.getElementById("result-summary").textContent =
      score >= 200 ? "Amazing focus! You were on fire." :
      score >= 100 ? "Great effort. Can you beat this score?" :
      "Good start. Keep practising to improve your focus.";
    resultPanel.classList.remove("hidden");
    const saveStatus = document.getElementById("save-status");
    saveStatus.textContent = "Saving your score…";
    try {
      const response = await fetch("/api/scores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_nonce: nonce,
          score,
          correct_answers: correct,
          total_answers: total,
          duration_seconds: 30
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not save score.");
      saveStatus.textContent = "✓ " + data.message;
      // Reloading the game page gives the next round a fresh one-time nonce.
      document.getElementById("play-again").onclick = () => window.location.reload();
    } catch (error) {
      saveStatus.textContent = "Score could not be saved: " + error.message + " Refresh the page and try again.";
      document.getElementById("play-again").onclick = () => window.location.reload();
    }
  }

  startBtn.addEventListener("click", startGame);
  answerButtons.forEach(button => {
    button.addEventListener("click", () => chooseColour(button.dataset.colour));
  });
  document.getElementById("play-again").addEventListener("click", () => window.location.reload());
  setButtonsEnabled(false);
  updateTimer();
})();
