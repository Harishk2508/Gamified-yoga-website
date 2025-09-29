const QUESTION_TIME = 30;
let questions = [];
let rawQuestions = [];
let currentIndex = 0;
let userAnswers = [];
let timerInterval;

const welcomeScreen = document.getElementById('welcomeScreen');
const questionScreen = document.getElementById('questionScreen');
const resultsScreen = document.getElementById('resultsScreen');

const poseImage = document.getElementById('poseImage');
const answerOptions = document.getElementById('answerOptions');

const currentQuestionElem = document.getElementById('currentQuestion');
const totalQuestionsElem = document.getElementById('totalQuestions');
const scoreDisplay = document.getElementById('scoreDisplay') || document.getElementById('currentScore'); // handling id differences

const feedbackBox = document.getElementById('feedbackBox') || document.getElementById('questionFeedback');
const feedbackIcon = document.getElementById('feedbackIcon');
const feedbackText = document.getElementById('feedbackText');

const nextBtn = document.getElementById('nextBtn');
const timerElem = document.getElementById('timer');

const finalScoreElem = document.getElementById('finalScore');
const maxScoreElem = document.getElementById('maxScore');

const performanceTitle = document.getElementById('performanceTitle') || document.getElementById('levelTitle');
const performanceDesc = document.getElementById('performanceDesc') || document.getElementById('levelDescription');

const breakdownList = document.getElementById('breakdownList');
const loadingOverlay = document.getElementById('loadingOverlay');
const imageLoading = document.getElementById('imageLoading');

const brainScoreElem = document.getElementById('brainScore'); // Element in dashboard to update brain score

function normalize(text) {
  return text.trim().toLowerCase().replace(/\s+/g, '').replace(/_/g, '');
}

function shuffle(array) {
  return array.sort(() => Math.random() - 0.5);
}

function getPerformance(score, max) {
  let percent = (score / max) * 100;
  if (percent >= 80) return ["Yoga Master", "Excellent knowledge!"];
  if (percent >= 60) return ["Advanced Yogi", "Great job!"];
  if (percent >= 40) return ["Intermediate Yogi", "Good effort!"];
  if (percent > 0) return ["Yoga Novice", "Keep practicing!"];
  return ["Beginner", "Let's start your journey!"];
}

function toggleLoading(show, message = "Preparing your quiz... please wait") {
  if (!loadingOverlay) return;
  if (show) {
    loadingOverlay.classList.remove('hidden');
    const msgElem = loadingOverlay.querySelector('.loading-message') || loadingOverlay.querySelector('.loading-content p');
    if (msgElem) msgElem.textContent = message;
  } else {
    loadingOverlay.classList.add('hidden');
  }
}

async function fetchQuestions() {
    toggleLoading(true);
    try {
        const response = await fetch('/api/quiz/questions', { credentials: 'include' });
        if (!response.ok) throw new Error("Failed to load questions");
        const data = await response.json();
        questions = data.questions;
        rawQuestions = data.raw_questions;
        userAnswers = [];
        currentIndex = 0;
        totalQuestionsElem.textContent = questions.length;
        scoreDisplay.textContent = '0';
        showQuestion();
        toggleLoading(false);
    } catch (err) {
        // Just hide the overlay, do not display any new alert or message
        toggleLoading(false);
        // Optionally: console.error(err);
    }
}


// Generates answer options with 1 correct + 3 random incorrect
function createOptions() {
  answerOptions.innerHTML = '';
  let correct = rawQuestions[currentIndex].folder;
  let pool = rawQuestions.map(q => q.folder).filter(f => f !== correct);
  let incorrectOptions = shuffle(pool).slice(0, 3);
  
  let options = shuffle([correct, ...incorrectOptions]);
  options.forEach(opt => {
    let btn = document.createElement('button');
    btn.className = 'answer-option';
    btn.textContent = opt.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    btn.onclick = () => selectAnswer(opt, btn);
    answerOptions.appendChild(btn);
  });
}

function showQuestion() {
  clearFeedback();
  let q = questions[currentIndex];
  
  currentQuestionElem.textContent = currentIndex + 1;
  totalQuestionsElem.textContent = questions.length;
  
  poseImage.src = q.image;
  poseImage.alt = "Yoga Pose";
  if (imageLoading) imageLoading.style.display = '';
  
  poseImage.onload = () => { if(imageLoading) imageLoading.style.display = 'none'; };
  poseImage.onerror = () => { if(imageLoading) imageLoading.style.display = ''; };
  
  createOptions();
  
  nextBtn.classList.add('hidden');
  if (feedbackBox) feedbackBox.classList.add('hidden');
  
  timerElem.textContent = `Time: ${QUESTION_TIME}s`;
  timerElem.style.display = '';
  
  startTimer();
  enableOptions(true);
  
  questionScreen.classList.add('active');
  if (welcomeScreen) welcomeScreen.classList.remove('active');
  if (resultsScreen) resultsScreen.classList.remove('active');
}

function selectAnswer(selected, button) {
  stopTimer();
  enableOptions(false);
  
  let correct = rawQuestions[currentIndex].folder;
  let isCorrect = normalize(selected) === normalize(correct);

  button.classList.add(isCorrect ? 'correct' : 'incorrect');

  //if (feedbackIcon) feedbackIcon.textContent = isCorrect ? '✔️' : '❌';
  //if (feedbackText) feedbackText.textContent = isCorrect ? 'Correct!' : 'Wrong! Correct: ' + correct;

  if (feedbackBox) feedbackBox.classList.remove('hidden');

  userAnswers[currentIndex] = { question_id: currentIndex, user_answer: selected };
  updateScore();

  nextBtn.classList.remove('hidden');
  nextBtn.textContent = currentIndex < questions.length - 1 ? 'Next Question' : 'See Results';
}

nextBtn.onclick = () => nextQuestion();

function updateScore() {
  let score = 0;
  userAnswers.forEach(ans => {
    if (!ans) return;
    let correct = normalize(rawQuestions[ans.question_id].folder);
    let answer = normalize(ans.user_answer);
    score += answer === correct ? 10 : -5;
  });
  if (score < 0) score = 0;
  scoreDisplay.textContent = score;
}

function enableOptions(enable) {
  answerOptions.querySelectorAll('button').forEach(btn => btn.disabled = !enable);
}

function startTimer() {
  let timeLeft = QUESTION_TIME;
  timerElem.textContent = `Time: ${timeLeft}s`;
  timerElem.style.display = '';
  timerInterval = setInterval(() => {
    timeLeft -= 1;
    if(timeLeft >= 0) timerElem.textContent = `Time: ${timeLeft}s`;
    if(timeLeft < 0){
      clearInterval(timerInterval);
      timeUp();
    }
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
}

function timeUp() {
  enableOptions(false);
  userAnswers[currentIndex] = { question_id: currentIndex, user_answer: "" };
  if(feedbackIcon) feedbackIcon.textContent = '⌛';
  if(feedbackText) feedbackText.textContent = "Time's up!";
  if(feedbackBox) feedbackBox.classList.remove('hidden');
  nextBtn.classList.remove('hidden');
  nextBtn.textContent = currentIndex < questions.length - 1 ? 'Next Question' : 'See Results';
}

function nextQuestion() {
  if (currentIndex < questions.length -1) {
    currentIndex++;
    showQuestion();
  } else {
    submitQuiz();
  }
}

async function submitQuiz() {
    stopTimer();
    toggleLoading(true, "Submitting your quiz...");
    try {
        const response = await fetch('/api/quiz/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ answers: userAnswers, raw_questions: rawQuestions })
        });
        if (!response.ok) throw new Error("Failed to submit quiz");
        const result = await response.json();
        showResults(result);

        // Dynamically update brain score if element is on page
        if (result.new_brain_score !== undefined) {
            const brainScoreElem = document.getElementById('brainScore');
            if (brainScoreElem) {
                brainScoreElem.textContent = result.new_brain_score;
            }
        }
    } catch (error) {
        toggleLoading(true, "Failed to submit quiz. Please try again.");
        console.error(error);
    } finally {
        if (resultsScreen.classList.contains('active')) toggleLoading(false);
    }
}
async function updateBrainScore() {
    try {
        const response = await fetch('/api/user/brain_score', { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            const brainScoreElem = document.getElementById('brainScore');
            if (brainScoreElem && data.brain_score !== undefined) {
                brainScoreElem.textContent = data.brain_score;
            }
        }
    } catch (e) {
        // Optionally handle error or remain silent
    }
}
window.addEventListener('DOMContentLoaded', updateBrainScore);


function showResults(result) {
  if (resultsScreen) resultsScreen.classList.add('active');
  if (questionScreen) questionScreen.classList.remove('active');
  if (welcomeScreen) welcomeScreen.classList.remove('active');

  finalScoreElem.textContent = result.score;
  maxScoreElem.textContent = questions.length * 10;

  const [title, desc] = getPerformance(result.score, maxScoreElem.textContent);
  performanceTitle.textContent = title;
  performanceDesc.textContent = desc;

  breakdownList.innerHTML = "";
  result.breakdown.forEach(item => {
    let div = document.createElement('div');
    div.className = `breakdown-item ${item.correct ? "correct" : "incorrect"}`;
    div.innerHTML = `<div>Q${item.question_id + 1}: ${item.correct_answer}</div><div>${item.user_answer} - ${item.mark} pts</div>`;
    breakdownList.appendChild(div);
  });

  nextBtn.classList.remove('hidden');
  nextBtn.textContent = "Try Again";
  nextBtn.onclick = () => {
    resetQuiz();
  };
}

function resetQuiz() {
  currentIndex = 0;
  userAnswers = [];
  scoreDisplay.textContent = "0";
  if (welcomeScreen) welcomeScreen.classList.add("active");
  if (questionScreen) questionScreen.classList.remove("active");
  if (resultsScreen) resultsScreen.classList.remove("active");
  toggleLoading(false);
  clearFeedback();
}

function clearFeedback() {
  if(feedbackBox) feedbackBox.classList.add("hidden");
  if(feedbackIcon) feedbackIcon.textContent = "";
  if(feedbackText) feedbackText.textContent = "";
}

// Start quiz button behavior, assume <button class="start-btn" onclick="startQuiz()">
window.startQuiz = () => {
  fetchQuestions();
  if (welcomeScreen) welcomeScreen.classList.remove("active");
  if (questionScreen) questionScreen.classList.add("active");
  if (resultsScreen) resultsScreen.classList.remove("active");
};

// Back to dashboard
// Back to dashboard
window.goHome = () => {
    window.location.href = "/home";
    // Or if you want to update the score immediately on the current page:
    if (window.loadBrainScore) {
        window.loadBrainScore();
    }
};


