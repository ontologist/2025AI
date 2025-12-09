// AI-300 Quiz Interface
// Handles quiz generation, display, and submission

let currentQuiz = null;
let quizStartTime = null;
let selectedAnswers = {};

async function startQuiz() {
    const weekSelect = document.getElementById('quiz-week');
    const questionsSelect = document.getElementById('quiz-questions');
    const startBtn = document.getElementById('start-quiz-btn');
    
    const weekNumber = weekSelect.value ? parseInt(weekSelect.value) : null;
    const numQuestions = parseInt(questionsSelect.value);
    
    // Show loading state
    startBtn.disabled = true;
    startBtn.innerHTML = '⏳ Generating quiz... / クイズ生成中...';
    
    try {
        const quiz = await window.progressTracker?.generateQuiz(weekNumber, numQuestions);
        
        if (quiz && quiz.questions) {
            currentQuiz = quiz;
            selectedAnswers = {};
            quizStartTime = Date.now();
            
            displayQuiz(quiz);
        } else {
            alert('Failed to generate quiz. Please try again.\nクイズの生成に失敗しました。もう一度お試しください。');
        }
    } catch (error) {
        console.error('Error starting quiz:', error);
        alert('Error generating quiz. Please try again.\nエラーが発生しました。もう一度お試しください。');
    } finally {
        startBtn.disabled = false;
        startBtn.innerHTML = '🚀 Start Quiz / クイズ開始';
    }
}

function displayQuiz(quiz) {
    const startSection = document.getElementById('quiz-start');
    const contentSection = document.getElementById('quiz-content');
    const resultsSection = document.getElementById('quiz-results');
    
    startSection.style.display = 'none';
    contentSection.style.display = 'block';
    resultsSection.style.display = 'none';
    
    let html = `
        <div class="quiz-info">
            <span class="quiz-topic">📖 ${quiz.topic}</span>
            <span class="quiz-difficulty">🎚️ ${quiz.difficulty}</span>
            <span class="quiz-timer" id="quiz-timer">⏱️ 00:00</span>
        </div>
    `;
    
    quiz.questions.forEach((q, index) => {
        html += `
            <div class="quiz-question" id="question-${index}">
                <div class="question-number">Question ${index + 1} / 問題 ${index + 1}</div>
                <div class="question-text">
                    <p class="question-ja">${q.question_ja || q.question}</p>
                    <p class="question-en">${q.question}</p>
                </div>
                <div class="question-options">
        `;
        
        const options = q.options || {};
        const optionsJa = q.options_ja || {};
        
        ['A', 'B', 'C', 'D'].forEach(letter => {
            if (options[letter]) {
                html += `
                    <label class="option-label" onclick="selectAnswer(${index}, '${letter}')">
                        <input type="radio" name="q${index}" value="${letter}" 
                               onchange="selectAnswer(${index}, '${letter}')">
                        <span class="option-letter">${letter}</span>
                        <span class="option-text">
                            <span class="option-ja">${optionsJa[letter] || options[letter]}</span>
                            <span class="option-en">${options[letter]}</span>
                        </span>
                    </label>
                `;
            }
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += `
        <div class="quiz-submit">
            <button class="btn btn-secondary" onclick="cancelQuiz()">
                ❌ Cancel / キャンセル
            </button>
            <button class="btn btn-primary btn-large" onclick="submitQuiz()">
                ✅ Submit Quiz / 提出
            </button>
        </div>
    `;
    
    contentSection.innerHTML = html;
    
    // Start timer
    startQuizTimer();
    
    // Scroll to quiz
    contentSection.scrollIntoView({ behavior: 'smooth' });
}

function selectAnswer(questionIndex, answer) {
    selectedAnswers[questionIndex] = answer;
    
    // Update UI to show selection
    const questionDiv = document.getElementById(`question-${questionIndex}`);
    if (questionDiv) {
        questionDiv.querySelectorAll('.option-label').forEach(label => {
            label.classList.remove('selected');
        });
        const selectedLabel = questionDiv.querySelector(`input[value="${answer}"]`)?.closest('.option-label');
        if (selectedLabel) {
            selectedLabel.classList.add('selected');
        }
    }
}

let timerInterval = null;

function startQuizTimer() {
    if (timerInterval) clearInterval(timerInterval);
    
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - quizStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        
        const timerEl = document.getElementById('quiz-timer');
        if (timerEl) {
            timerEl.textContent = `⏱️ ${minutes}:${seconds}`;
        }
    }, 1000);
}

function stopQuizTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function cancelQuiz() {
    if (confirm('Cancel this quiz? Your progress will be lost.\nこのクイズをキャンセルしますか？進行状況は失われます。')) {
        stopQuizTimer();
        resetQuizUI();
    }
}

function resetQuizUI() {
    const startSection = document.getElementById('quiz-start');
    const contentSection = document.getElementById('quiz-content');
    const resultsSection = document.getElementById('quiz-results');
    
    startSection.style.display = 'block';
    contentSection.style.display = 'none';
    resultsSection.style.display = 'none';
    
    currentQuiz = null;
    selectedAnswers = {};
}

async function submitQuiz() {
    if (!currentQuiz) return;
    
    // Check if all questions answered
    const totalQuestions = currentQuiz.questions.length;
    const answeredQuestions = Object.keys(selectedAnswers).length;
    
    if (answeredQuestions < totalQuestions) {
        const confirm_submit = confirm(
            `You have only answered ${answeredQuestions}/${totalQuestions} questions. Submit anyway?\n` +
            `${answeredQuestions}/${totalQuestions}問しか回答していません。このまま提出しますか？`
        );
        if (!confirm_submit) return;
    }
    
    stopQuizTimer();
    const timeTaken = Math.floor((Date.now() - quizStartTime) / 1000);
    
    // Convert answers to string keys for API
    const answersForApi = {};
    Object.entries(selectedAnswers).forEach(([key, value]) => {
        answersForApi[key.toString()] = value;
    });
    
    try {
        const result = await window.progressTracker?.submitQuiz(
            currentQuiz.quiz_id,
            answersForApi,
            timeTaken
        );
        
        if (result) {
            displayResults(result);
        } else {
            alert('Failed to submit quiz. Please try again.\nクイズの提出に失敗しました。');
        }
    } catch (error) {
        console.error('Error submitting quiz:', error);
        alert('Error submitting quiz.\nエラーが発生しました。');
    }
}

function displayResults(result) {
    const startSection = document.getElementById('quiz-start');
    const contentSection = document.getElementById('quiz-content');
    const resultsSection = document.getElementById('quiz-results');
    
    startSection.style.display = 'none';
    contentSection.style.display = 'none';
    resultsSection.style.display = 'block';
    
    const passedClass = result.passed ? 'passed' : 'failed';
    const passedText = result.passed ? '🎉 Passed! / 合格！' : '📚 Keep studying! / もっと勉強しよう！';
    
    let html = `
        <div class="results-summary ${passedClass}">
            <div class="results-score">
                <span class="score-number">${result.score}/${result.max_score}</span>
                <span class="score-percentage">${result.percentage}%</span>
            </div>
            <div class="results-status">${passedText}</div>
            <div class="results-time">⏱️ Time: ${formatTime(result.time_taken_seconds)}</div>
        </div>
        
        <div class="results-details">
            <h4>Question Review / 問題の復習</h4>
    `;
    
    result.results.forEach((r, index) => {
        const question = currentQuiz.questions[index];
        const correctClass = r.is_correct ? 'correct' : 'incorrect';
        const icon = r.is_correct ? '✅' : '❌';
        
        html += `
            <div class="result-item ${correctClass}">
                <div class="result-header">
                    <span>${icon} Question ${index + 1}</span>
                    <span>Your answer: ${r.student_answer || 'No answer'} | Correct: ${r.correct_answer}</span>
                </div>
                <div class="result-question">${question.question_ja || question.question}</div>
                <div class="result-explanation">
                    <strong>Explanation / 解説:</strong><br>
                    ${r.explanation_ja || r.explanation || 'No explanation available.'}
                </div>
            </div>
        `;
    });
    
    html += `
        </div>
        
        <div class="results-actions">
            <button class="btn btn-primary" onclick="resetQuizUI()">
                🔄 Take Another Quiz / 別のクイズに挑戦
            </button>
        </div>
    `;
    
    resultsSection.innerHTML = html;
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

