// ==============================================================================
// WINTER ARC // FLASHCARDS & VOCABULARY ENGINE JS
// ==============================================================================

let allDecks = [];
let currentDeck = null;
let currentDeckCards = [];
let currentFlipIndex = 0;
let isFlipped = false;

// Quiz State
let quizCards = [];
let quizIndex = 0;
let quizScore = 0;
let quizAnswered = false;

// -----------------------------------------------------------------------------
// API Interface
// -----------------------------------------------------------------------------
function getApi() {
  if (window.pywebview && window.pywebview.api) {
    return window.pywebview.api;
  }
  return {
    get_flashcard_decks: async () => [
      {
        id: "deck_demo",
        name: "Demo Vocab Deck",
        description: "Demo deck for browser preview",
        cards: [
          { id: "c1", word: "Resilient", phonetic: "/rɪˈzɪl.jənt/", pos: "adjective", meaning: "Kiên cường, có khả năng phục hồi nhanh", example: "He is remarkably resilient.", learned: false },
          { id: "c2", word: "Ubiquitous", phonetic: "/juːˈbɪk.wə.təs/", pos: "adjective", meaning: "Phổ biến khắp nơi, đâu đâu cũng thấy", example: "Smartphones are ubiquitous.", learned: false },
          { id: "c3", word: "Mitigate", phonetic: "/ˈmɪt.ɪ.ɡeɪt/", pos: "verb", meaning: "Làm dịu bớt, giảm nhẹ mức độ nghiêm trọng", example: "Action was taken to mitigate risks.", learned: false },
          { id: "c4", word: "Pragmatic", phonetic: "/præɡˈmæt.ɪk/", pos: "adjective", meaning: "Thực tế, thực dụng, dựa trên thực tiễn", example: "A pragmatic approach works best.", learned: false }
        ]
      }
    ],
    create_deck: async (name, desc) => ({ id: "deck_" + Date.now(), name, description: desc, cards: [] }),
    delete_deck: async (id) => true,
    add_card_to_deck: async (dId, w, m, ex, ph, pos) => ({ id: "c_" + Date.now(), word: w, meaning: m, example: ex, phonetic: ph, pos, learned: false }),
    update_card_in_deck: async (dId, cId, w, m, ex, ph, pos, l) => ({ id: cId, word: w, meaning: m, example: ex, phonetic: ph, pos, learned: l }),
    delete_card_from_deck: async (dId, cId) => true,
    toggle_card_learned: async (dId, cId) => true,
    ai_suggest_vocab_card: async (w) => ({
      success: true,
      word: w,
      phonetic: "/.../",
      pos: "adjective",
      meaning: "Nghĩa tiếng Việt gợi ý bởi AI",
      example: `This is a sample sentence with ${w}.`
    })
  };
}

// -----------------------------------------------------------------------------
// Audio Pronunciation (Multi-tier: Native Audio Stream + SpeechSynthesis Fallback)
// -----------------------------------------------------------------------------
let currentAudioPlayer = null;

function speakWord(text) {
  if (!text) return;
  const clean = text.trim();

  // Tier 1: High-fidelity Native American English Dictionary Audio Stream
  try {
    if (currentAudioPlayer) {
      currentAudioPlayer.pause();
      currentAudioPlayer = null;
    }
    const audioUrl = "https://dict.youdao.com/dictvoice?audio=" + encodeURIComponent(clean) + "&type=2";
    currentAudioPlayer = new Audio(audioUrl);
    
    // Add visual feedback to speaker icon
    const activeSpeakers = document.querySelectorAll(".btn-speak");
    activeSpeakers.forEach(s => s.classList.add("speaking"));
    currentAudioPlayer.onended = () => {
      activeSpeakers.forEach(s => s.classList.remove("speaking"));
    };
    currentAudioPlayer.onerror = () => {
      activeSpeakers.forEach(s => s.classList.remove("speaking"));
      fallbackGoogleTTS(clean);
    };

    const playPromise = currentAudioPlayer.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        fallbackGoogleTTS(clean);
      });
    }
    return;
  } catch (err) {
    fallbackGoogleTTS(clean);
  }
}

function fallbackGoogleTTS(clean) {
  try {
    const gUrl = "https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q=" + encodeURIComponent(clean);
    currentAudioPlayer = new Audio(gUrl);
    const p = currentAudioPlayer.play();
    if (p !== undefined) {
      p.catch(() => fallbackSpeechSynthesis(clean));
    }
  } catch (e) {
    fallbackSpeechSynthesis(clean);
  }
}

function fallbackSpeechSynthesis(clean) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  }
}

// -----------------------------------------------------------------------------
// Load & Switch Decks
// -----------------------------------------------------------------------------
async function loadDecks() {
  const api = getApi();
  try {
    allDecks = await api.get_flashcard_decks();
    renderDeckSelect();
    if (allDecks.length > 0) {
      selectDeck(allDecks[0].id);
    }
  } catch (err) {
    console.error("Error loading decks:", err);
  }
}

function renderDeckSelect() {
  const selectEl = document.getElementById("deck-select");
  if (!selectEl) return;
  selectEl.innerHTML = "";
  allDecks.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.innerText = `${d.name} (${(d.cards || []).length} words)`;
    selectEl.appendChild(opt);
  });
}

function selectDeck(deckId) {
  currentDeck = allDecks.find(d => d.id === deckId);
  const selectEl = document.getElementById("deck-select");
  if (selectEl && currentDeck) {
    selectEl.value = currentDeck.id;
  }
  currentDeckCards = currentDeck ? (currentDeck.cards || []) : [];
  currentFlipIndex = 0;
  isFlipped = false;
  
  // Render sub-modes
  renderFlipCard();
  initQuiz();
  renderWordsTable();
}

// -----------------------------------------------------------------------------
// MODE 1: Flashcard Flip Logic
// -----------------------------------------------------------------------------
function renderFlipCard() {
  const cardScene = document.getElementById("card-scene");
  const cardObj = document.getElementById("card-object");
  const counterEl = document.getElementById("flip-counter");
  const progressEl = document.getElementById("flip-progress-bar");

  if (!currentDeckCards || currentDeckCards.length === 0) {
    document.getElementById("card-front-word").innerText = "No Cards Yet";
    document.getElementById("card-front-phonetic").innerText = "Add cards in Word Manager";
    document.getElementById("card-front-pos").innerText = "EMPTY";
    document.getElementById("card-back-meaning").innerText = "Chưa có từ vựng nào trong bộ này.";
    document.getElementById("card-back-example").innerText = "Chuyển sang tab Word Manager để thêm từ!";
    if (counterEl) counterEl.innerText = "0 of 0";
    if (progressEl) progressEl.style.width = "0%";
    return;
  }

  if (currentFlipIndex >= currentDeckCards.length) currentFlipIndex = 0;
  if (currentFlipIndex < 0) currentFlipIndex = currentDeckCards.length - 1;

  const card = currentDeckCards[currentFlipIndex];

  // Unflip whenever card changes
  if (cardObj) {
    cardObj.classList.remove("is-flipped");
    isFlipped = false;
  }

  // Populate Front
  document.getElementById("card-front-word").innerText = card.word || "";
  document.getElementById("card-front-phonetic").innerText = card.phonetic || "";
  document.getElementById("card-front-pos").innerText = (card.pos || "vocab").toUpperCase();

  // Populate Back
  document.getElementById("card-back-meaning").innerText = card.meaning || "";
  document.getElementById("card-back-example").innerText = card.example ? `"${card.example}"` : "";

  const starBtn = document.getElementById("btn-toggle-learned");
  if (starBtn) {
    starBtn.classList.toggle("active", Boolean(card.learned));
  }

  if (counterEl) {
    counterEl.innerText = `Card ${currentFlipIndex + 1} of ${currentDeckCards.length}`;
  }
  if (progressEl) {
    const pct = Math.round(((currentFlipIndex + 1) / currentDeckCards.length) * 100);
    progressEl.style.width = `${pct}%`;
  }
}

function flipCard() {
  const cardObj = document.getElementById("card-object");
  if (!cardObj) return;
  isFlipped = !isFlipped;
  cardObj.classList.toggle("is-flipped", isFlipped);
}

function prevCard() {
  if (currentDeckCards.length <= 1) return;
  currentFlipIndex--;
  renderFlipCard();
}

function nextCard() {
  if (currentDeckCards.length <= 1) return;
  currentFlipIndex++;
  renderFlipCard();
}

function shuffleCards() {
  if (currentDeckCards.length <= 1) return;
  for (let i = currentDeckCards.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [currentDeckCards[i], currentDeckCards[j]] = [currentDeckCards[j], currentDeckCards[i]];
  }
  currentFlipIndex = 0;
  renderFlipCard();
}

// -----------------------------------------------------------------------------
// MODE 2: Multiple Choice Quiz Logic
// -----------------------------------------------------------------------------
function initQuiz() {
  document.getElementById("quiz-feedback-box")?.classList.add("hidden");
  document.getElementById("quiz-finish-box")?.classList.add("hidden");
  document.querySelector(".quiz-question-box")?.classList.remove("hidden");
  document.getElementById("quiz-choices-grid")?.classList.remove("hidden");

  if (!currentDeckCards || currentDeckCards.length === 0) {
    document.getElementById("quiz-q-word").innerText = "No Words Available";
    document.getElementById("quiz-q-phonetic").innerText = "";
    document.getElementById("quiz-choices-grid").innerHTML = "<div style='color: var(--text-muted); padding: 20px; text-align: center; grid-column: 1/-1;'>Please add vocabulary cards first!</div>";
    return;
  }

  // Clone and shuffle for quiz
  quizCards = [...currentDeckCards].sort(() => Math.random() - 0.5);
  quizIndex = 0;
  quizScore = 0;
  quizAnswered = false;

  updateQuizScoreUi();
  renderQuizQuestion();
}

function updateQuizScoreUi() {
  const scoreEl = document.getElementById("quiz-score-val");
  const totalEl = document.getElementById("quiz-total-val");
  const qCountEl = document.getElementById("quiz-q-counter");
  if (scoreEl) scoreEl.innerText = quizScore;
  if (totalEl) totalEl.innerText = quizCards.length;
  if (qCountEl) qCountEl.innerText = `Question ${quizIndex + 1} of ${quizCards.length}`;
}

function renderQuizQuestion() {
  quizAnswered = false;
  document.getElementById("quiz-feedback-box")?.classList.add("hidden");

  if (quizIndex >= quizCards.length) {
    showQuizFinished();
    return;
  }

  updateQuizScoreUi();

  const currentQ = quizCards[quizIndex];
  document.getElementById("quiz-q-word").innerText = currentQ.word;
  document.getElementById("quiz-q-phonetic").innerText = currentQ.phonetic || "";
  document.getElementById("quiz-q-pos").innerText = (currentQ.pos || "vocab").toUpperCase();

  // Create 4 choices: 1 correct + 3 random distractors
  const distractors = currentDeckCards
    .filter(c => c.id !== currentQ.id && c.meaning !== currentQ.meaning)
    .map(c => c.meaning);

  // Shuffle distractors
  distractors.sort(() => Math.random() - 0.5);
  const options = [currentQ.meaning, ...distractors.slice(0, 3)];

  // Fallbacks if deck has < 4 cards
  const genericFallbacks = [
    "Cải thiện khả năng thích nghi và tư duy",
    "Đặt mục tiêu rõ ràng và kiên định",
    "Phân tích dữ liệu thực tế khách quan",
    "Duy trì thói quen kỷ luật cao độ"
  ];
  while (options.length < 4) {
    const fb = genericFallbacks.pop();
    if (!options.includes(fb)) options.push(fb);
  }

  // Shuffle the final 4 options
  options.sort(() => Math.random() - 0.5);

  const gridEl = document.getElementById("quiz-choices-grid");
  if (!gridEl) return;
  gridEl.innerHTML = "";

  const keys = ["1", "2", "3", "4"];
  options.forEach((optText, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-quiz-choice";
    btn.dataset.choice = optText;
    btn.innerHTML = `
      <span class="choice-key">${keys[idx]}</span>
      <span>${escapeHtml(optText)}</span>
    `;
    btn.addEventListener("click", () => handleQuizChoice(optText, currentQ));
    gridEl.appendChild(btn);
  });
}

function handleQuizChoice(selectedMeaning, currentQ) {
  if (quizAnswered) return;
  quizAnswered = true;

  const isCorrect = selectedMeaning === currentQ.meaning;
  if (isCorrect) quizScore++;

  // Highlight choices
  const choiceBtns = document.querySelectorAll(".btn-quiz-choice");
  choiceBtns.forEach(btn => {
    btn.disabled = true;
    if (btn.dataset.choice === currentQ.meaning) {
      btn.classList.add("correct");
    } else if (btn.dataset.choice === selectedMeaning && !isCorrect) {
      btn.classList.add("wrong");
    }
  });

  // Show Feedback Box
  const feedbackBox = document.getElementById("quiz-feedback-box");
  const feedbackMsg = document.getElementById("quiz-feedback-msg");
  const feedbackEx = document.getElementById("quiz-feedback-example");

  if (feedbackBox && feedbackMsg) {
    feedbackBox.classList.remove("hidden");
    if (isCorrect) {
      feedbackMsg.className = "quiz-feedback-msg correct-text";
      feedbackMsg.innerText = "✓ Chính xác! Rất xuất sắc.";
    } else {
      feedbackMsg.className = "quiz-feedback-msg wrong-text";
      feedbackMsg.innerText = `✗ Chưa đúng. Nghĩa chuẩn: "${currentQ.meaning}"`;
    }
    if (feedbackEx && currentQ.example) {
      feedbackEx.innerText = `Ví dụ: "${currentQ.example}"`;
    } else if (feedbackEx) {
      feedbackEx.innerText = "";
    }
  }

  updateQuizScoreUi();
}

function nextQuizQuestion() {
  quizIndex++;
  renderQuizQuestion();
}

function showQuizFinished() {
  document.querySelector(".quiz-question-box")?.classList.add("hidden");
  document.getElementById("quiz-choices-grid")?.classList.add("hidden");
  document.getElementById("quiz-feedback-box")?.classList.add("hidden");

  const finishBox = document.getElementById("quiz-finish-box");
  if (!finishBox) return;
  finishBox.classList.remove("hidden");

  const total = quizCards.length;
  const pct = total > 0 ? Math.round((quizScore / total) * 100) : 0;

  document.getElementById("finish-score").innerText = `${quizScore}/${total}`;
  document.getElementById("finish-accuracy").innerText = `${pct}%`;
}

// -----------------------------------------------------------------------------
// MODE 3: Word Manager & AI Auto-fill
// -----------------------------------------------------------------------------
function renderWordsTable(filterQuery = "") {
  const container = document.getElementById("words-table-container");
  const countBadge = document.getElementById("deck-card-count-badge");
  if (!container) return;

  const cards = (currentDeckCards || []).filter(c => {
    if (!filterQuery) return true;
    const q = filterQuery.toLowerCase();
    return (c.word || "").toLowerCase().includes(q) || (c.meaning || "").toLowerCase().includes(q);
  });

  if (countBadge) {
    countBadge.innerText = `${cards.length} cards`;
  }

  if (cards.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 24px;">No vocabulary cards found.</div>`;
    return;
  }

  container.innerHTML = "";
  cards.forEach(card => {
    const cardEl = document.createElement("div");
    cardEl.className = "word-row-card";
    cardEl.innerHTML = `
      <div class="word-row-left">
        <div class="word-row-title-bar">
          <span class="word-row-text">${escapeHtml(card.word)}</span>
          <span class="word-row-pos">${escapeHtml(card.pos || '')}</span>
          <span class="word-row-phonetic">${escapeHtml(card.phonetic || '')}</span>
        </div>
        <div class="word-row-meaning">${escapeHtml(card.meaning)}</div>
      </div>
      <div class="word-row-actions">
        <button type="button" class="btn-row-action btn-speak-row" title="Listen (S)" data-word="${escapeHtml(card.word)}">Audio</button>
        <button type="button" class="btn-row-action btn-edit-row" title="Edit" data-id="${card.id}">Edit</button>
        <button type="button" class="btn-row-action btn-del btn-del-row" title="Delete" data-id="${card.id}">Delete</button>
      </div>
    `;

    cardEl.querySelector(".btn-speak-row")?.addEventListener("click", () => speakWord(card.word));
    cardEl.querySelector(".btn-edit-row")?.addEventListener("click", () => editCard(card));
    cardEl.querySelector(".btn-del-row")?.addEventListener("click", () => deleteCard(card.id));

    container.appendChild(cardEl);
  });
}

function editCard(card) {
  document.getElementById("editing-card-id").value = card.id;
  document.getElementById("input-card-word").value = card.word || "";
  document.getElementById("input-card-phonetic").value = card.phonetic || "";
  document.getElementById("input-card-pos").value = card.pos || "adjective";
  document.getElementById("input-card-meaning").value = card.meaning || "";
  document.getElementById("input-card-example").value = card.example || "";
  
  document.getElementById("card-form-title").innerText = `EDIT: ${card.word}`;
  document.getElementById("btn-submit-card").innerText = "UPDATE CARD";
  document.getElementById("btn-cancel-card-edit").classList.remove("hidden");
}

function cancelCardEdit() {
  document.getElementById("editing-card-id").value = "";
  document.getElementById("card-crud-form").reset();
  document.getElementById("card-form-title").innerText = "ADD VOCABULARY CARD";
  document.getElementById("btn-submit-card").innerText = "SAVE CARD";
  document.getElementById("btn-cancel-card-edit").classList.add("hidden");
}

async function saveCardForm() {
  if (!currentDeck) {
    alert("Please select or create a deck first!");
    return;
  }
  const editId = document.getElementById("editing-card-id").value.trim();
  const word = document.getElementById("input-card-word").value.trim();
  const phonetic = document.getElementById("input-card-phonetic").value.trim();
  const pos = document.getElementById("input-card-pos").value;
  const meaning = document.getElementById("input-card-meaning").value.trim();
  const example = document.getElementById("input-card-example").value.trim();

  if (!word || !meaning) {
    alert("Please enter both Word and Vietnamese Meaning!");
    return;
  }

  const api = getApi();
  try {
    if (editId) {
      await api.update_card_in_deck(currentDeck.id, editId, word, meaning, example, phonetic, pos, false);
    } else {
      await api.add_card_to_deck(currentDeck.id, word, meaning, example, phonetic, pos);
    }
    cancelCardEdit();
    // Reload active deck
    await loadDecks();
  } catch (err) {
    alert("Error saving card: " + err.message);
  }
}

async function deleteCard(cardId) {
  if (!confirm("Are you sure you want to delete this card?")) return;
  const api = getApi();
  try {
    await api.delete_card_from_deck(currentDeck.id, cardId);
    await loadDecks();
  } catch (err) {
    alert("Error deleting card: " + err.message);
  }
}

async function triggerAiAutoFill() {
  const wordInput = document.getElementById("input-card-word");
  const word = (wordInput?.value || "").trim();
  if (!word) {
    alert("Please enter an English word first!");
    return;
  }

  const btn = document.getElementById("btn-ai-suggest-vocab");
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Generating...";
  }

  try {
    const api = getApi();
    const res = await api.ai_suggest_vocab_card(word);
    if (res && res.success) {
      if (res.phonetic) document.getElementById("input-card-phonetic").value = res.phonetic;
      if (res.meaning) document.getElementById("input-card-meaning").value = res.meaning;
      if (res.example) document.getElementById("input-card-example").value = res.example;
      if (res.pos) {
        const posEl = document.getElementById("input-card-pos");
        const low = res.pos.toLowerCase();
        for (let opt of posEl.options) {
          if (low.includes(opt.value)) {
            posEl.value = opt.value;
            break;
          }
        }
      }
    } else {
      alert("AI Suggestion: " + (res.error || "Please check Gemini API key"));
    }
  } catch (err) {
    alert("AI Auto-fill error: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "AI Auto-fill";
    }
  }
}

// -----------------------------------------------------------------------------
// Keyboard Shortcuts & Global Events
// -----------------------------------------------------------------------------
function setupEventListeners() {
  // Mode Tabs
  document.querySelectorAll(".fc-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".fc-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".fc-view").forEach(v => v.classList.remove("active"));
      btn.classList.add("active");
      const tabId = btn.dataset.tab;
      document.getElementById(`view-${tabId}`)?.classList.add("active");

      // Auto initialize or re-render
      if (tabId === "flip") renderFlipCard();
      if (tabId === "quiz") initQuiz();
      if (tabId === "list") renderWordsTable();
    });
  });

  // Deck selector
  document.getElementById("deck-select")?.addEventListener("change", (e) => {
    selectDeck(e.target.value);
  });

  // Flip Mode interactions
  document.getElementById("card-scene")?.addEventListener("click", flipCard);
  document.getElementById("btn-flip-trigger")?.addEventListener("click", (e) => {
    e.stopPropagation();
    flipCard();
  });
  document.getElementById("btn-prev-card")?.addEventListener("click", (e) => {
    e.stopPropagation();
    prevCard();
  });
  document.getElementById("btn-next-card")?.addEventListener("click", (e) => {
    e.stopPropagation();
    nextCard();
  });
  document.getElementById("btn-shuffle-cards")?.addEventListener("click", shuffleCards);
  document.getElementById("btn-speak-front")?.addEventListener("click", (e) => {
    e.stopPropagation();
    if (currentDeckCards[currentFlipIndex]) speakWord(currentDeckCards[currentFlipIndex].word);
  });
  document.getElementById("btn-toggle-learned")?.addEventListener("click", async (e) => {
    e.stopPropagation();
    if (!currentDeck || !currentDeckCards[currentFlipIndex]) return;
    const card = currentDeckCards[currentFlipIndex];
    const api = getApi();
    const newStatus = await api.toggle_card_learned(currentDeck.id, card.id);
    card.learned = newStatus;
    document.getElementById("btn-toggle-learned")?.classList.toggle("active", newStatus);
  });

  // Quiz Mode interactions
  document.getElementById("btn-restart-quiz")?.addEventListener("click", initQuiz);
  document.getElementById("btn-quiz-speak")?.addEventListener("click", () => {
    if (quizCards[quizIndex]) speakWord(quizCards[quizIndex].word);
  });
  document.getElementById("btn-quiz-next")?.addEventListener("click", nextQuizQuestion);
  document.getElementById("btn-finish-restart")?.addEventListener("click", initQuiz);
  document.getElementById("btn-finish-to-flip")?.addEventListener("click", () => {
    document.querySelector('.fc-tab-btn[data-tab="flip"]')?.click();
  });

  // Word Manager Form interactions
  document.getElementById("btn-ai-suggest-vocab")?.addEventListener("click", triggerAiAutoFill);
  document.getElementById("btn-submit-card")?.addEventListener("click", saveCardForm);
  document.getElementById("btn-cancel-card-edit")?.addEventListener("click", cancelCardEdit);
  document.getElementById("input-search-words")?.addEventListener("input", (e) => {
    renderWordsTable(e.target.value.trim());
  });

  // New Deck Modal
  document.getElementById("btn-new-deck")?.addEventListener("click", () => {
    document.getElementById("modal-new-deck")?.classList.remove("hidden");
  });
  document.getElementById("btn-modal-cancel-deck")?.addEventListener("click", () => {
    document.getElementById("modal-new-deck")?.classList.add("hidden");
  });
  document.getElementById("btn-modal-save-deck")?.addEventListener("click", async () => {
    const name = document.getElementById("input-new-deck-name")?.value.trim();
    const desc = document.getElementById("input-new-deck-desc")?.value.trim();
    if (!name) {
      alert("Please enter a deck name!");
      return;
    }
    const api = getApi();
    const newDeck = await api.create_deck(name, desc);
    document.getElementById("modal-new-deck")?.classList.add("hidden");
    document.getElementById("input-new-deck-name").value = "";
    document.getElementById("input-new-deck-desc").value = "";
    await loadDecks();
    if (newDeck) selectDeck(newDeck.id);
  });

  document.getElementById("btn-delete-deck")?.addEventListener("click", async () => {
    if (!currentDeck) return;
    if (!confirm(`Are you sure you want to delete deck "${currentDeck.name}"?`)) return;
    const api = getApi();
    await api.delete_deck(currentDeck.id);
    await loadDecks();
  });

  // Global Keyboard Navigation
  window.addEventListener("keydown", (e) => {
    // If user is typing in an input or textarea, ignore shortcuts
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
      return;
    }

    const activeTab = document.querySelector(".fc-tab-btn.active")?.dataset.tab;

    // Flip Mode Shortcuts
    if (activeTab === "flip") {
      if (e.code === "Space") {
        e.preventDefault();
        flipCard();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        prevCard();
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        nextCard();
      } else if (e.code === "KeyS") {
        if (currentDeckCards[currentFlipIndex]) speakWord(currentDeckCards[currentFlipIndex].word);
      }
    }

    // Quiz Mode Shortcuts
    if (activeTab === "quiz") {
      if (["Digit1", "Digit2", "Digit3", "Digit4"].includes(e.code)) {
        const choiceIdx = parseInt(e.code.replace("Digit", ""), 10) - 1;
        const choiceBtns = document.querySelectorAll(".btn-quiz-choice");
        if (choiceBtns[choiceIdx] && !choiceBtns[choiceIdx].disabled) {
          choiceBtns[choiceIdx].click();
        }
      } else if (e.code === "Enter" || e.code === "Space") {
        const nextBtn = document.getElementById("btn-quiz-next");
        const feedbackBox = document.getElementById("quiz-feedback-box");
        if (feedbackBox && !feedbackBox.classList.contains("hidden")) {
          e.preventDefault();
          nextQuizQuestion();
        }
      }
    }
  });
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

// -----------------------------------------------------------------------------
// Theme Management (Warm Amber / Warm Daylight / Ice Frost)
// -----------------------------------------------------------------------------
function applyTheme(themeName) {
  const validThemes = ["warm-amber", "warm-daylight", "ice-frost"];
  const targetTheme = validThemes.includes(themeName) ? themeName : "warm-amber";
  
  document.body.classList.remove("theme-warm-amber", "theme-warm-daylight", "theme-ice-frost");
  document.body.classList.add(`theme-${targetTheme}`);
  localStorage.setItem("fc_theme", targetTheme);

  const themeSelect = document.getElementById("theme-select");
  if (themeSelect && themeSelect.value !== targetTheme) {
    themeSelect.value = targetTheme;
  }
}

function initTheme() {
  const savedTheme = localStorage.getItem("fc_theme") || "warm-amber";
  applyTheme(savedTheme);

  const themeSelect = document.getElementById("theme-select");
  if (themeSelect) {
    themeSelect.value = savedTheme;
    themeSelect.addEventListener("change", (e) => {
      applyTheme(e.target.value);
    });
  }
}

// -----------------------------------------------------------------------------
// Initialize
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupEventListeners();
  loadDecks();
});

window.addEventListener("pywebviewready", () => {
  loadDecks();
});
