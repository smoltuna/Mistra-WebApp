document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const quizContainer = document.getElementById('quiz-container');
    const quizTitleDisplay = document.getElementById('quiz-title-display');
    const quizDescriptionDisplay = document.getElementById('quiz-description-display');
    const quizStartForm = document.getElementById('quiz-start-form');
    const ageInput = document.getElementById('age');
    const sexSelect = document.getElementById('sex');

    const quizQuestionsDiv = document.getElementById('quiz-questions');
    const progressIndicatorDiv = document.getElementById('quiz-progress-indicator');
    const questionNumberElement = document.getElementById('question-number');
    const questionTextElement = document.getElementById('question-text');
    const answerOptionsDiv = document.getElementById('answer-options');
    const prevQuestionBtn = document.getElementById('prev-question-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    const finishQuizBtn = document.getElementById('finish-quiz-btn');

    const quizResultsDiv = document.getElementById('quiz-results');
    const finalScoreElement = document.getElementById('final-score');
    const executionCodeElement = document.getElementById('execution-code');
    const timeTakenElement = document.getElementById('time-taken');
    const detailedResultsDiv = document.getElementById('detailed-results');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');

    // --- Quiz State Variables ---
    let currentTestId = null;
    let currentTestName = '';
    let currentTestDescription = '';
    let currentQuestions = [];
    let currentQuestionIndex = 0;
    let userAnswers = [];
    let quizStartTime = null;
    let quizDuration = 0;
    let quizExecutionCode = null;
    let latestQuizResults = null;

    const languageCode = quizContainer.dataset.languageCode || 'en';

    // --- Initialization ---
    // ... (codice invariato) ...
    async function initializeQuizPlugin() {
        await getSexOptions();
        await loadRandomTestDetails();
    }

    async function loadRandomTestDetails() {
        try {
            const randomTestResponse = await fetch(`/${languageCode}/quiz/api/random_test_id/`);
            if (!randomTestResponse.ok) throw new Error(`HTTP error! status: ${randomTestResponse.status}`);
            const randomTestData = await randomTestResponse.json();
            currentTestId = randomTestData.test_id;
            currentTestName = randomTestData.test_name;
            currentTestDescription = randomTestData.test_description;

            if (!currentTestId) {
                quizTitleDisplay.textContent = 'Error: No tests available.';
                return;
            }
            quizTitleDisplay.textContent = currentTestName;
            quizDescriptionDisplay.textContent = currentTestDescription;

        } catch (error) {
            console.error('Error loading random test details:', error);
            quizTitleDisplay.textContent = 'Error loading quiz.';
            quizDescriptionDisplay.textContent = 'Please try refreshing the page.';
        }
    }
    initializeQuizPlugin();
    async function getSexOptions() {
        try {
            const response = await fetch(`/${languageCode}/quiz/api/sex_options/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            sexSelect.innerHTML = '<option value="">Select...</option>';
            data.sex_options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.id;
                optionElement.textContent = option.name;
                sexSelect.appendChild(optionElement);
            });
        } catch (error) {
            console.error('Error fetching sex options:', error);
        }
    }


    // --- Event Listeners ---
    // ... (quizStartForm event listener invariato) ...
    quizStartForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (!ageInput.value || !sexSelect.value) {
            alert('Please enter your age and select your sex.');
            return;
        }
        if (!currentTestId) {
            alert('Quiz not loaded yet. Please wait or refresh.');
            return;
        }

        quizStartTime = Date.now();

        try {
            const response = await fetch(`/${languageCode}/quiz/api/test/${currentTestId}/questions/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            currentQuestions = data.questions;

            if (currentQuestions.length === 0) {
                alert('No questions found for this test.');
                return;
            }

            userAnswers = Array(currentQuestions.length).fill(null);
            currentQuestionIndex = 0;
            
            quizStartForm.style.display = 'none';
            quizQuestionsDiv.style.display = 'block';
            renderProgressIndicator();
            renderQuestion();

        } catch (error) {
            console.error('Error fetching questions:', error);
            alert('Could not load quiz questions. Please try again.');
        }
    });


    // FIX: [Problema 2] Aggiungi un event listener al contenitore delle risposte
    // per reagire subito al click su una radio.
    answerOptionsDiv.addEventListener('click', (event) => {
        // Usa event delegation per verificare se è stata cliccata una radio
        if (event.target.type === 'radio') {
            saveCurrentAnswer(); // Salva la risposta e aggiorna lo stato dei pulsanti
        }
    });

    prevQuestionBtn.addEventListener('click', () => {
        saveCurrentAnswer();
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            renderQuestion();
        }
    });
    
    nextQuestionBtn.addEventListener('click', () => {
        saveCurrentAnswer();
        if (currentQuestionIndex < currentQuestions.length - 1) {
            currentQuestionIndex++;
            renderQuestion();
        }
    });

    finishQuizBtn.addEventListener('click', () => {
        saveCurrentAnswer();
        if (checkAllQuestionsAnswered()) {
            quizDuration = Math.round((Date.now() - quizStartTime) / 1000);
            submitQuizResults();
        } else {
            alert('Please answer all questions before finishing the quiz.');
        }
    });


    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async () => {
            if (!latestQuizResults) {
                alert("No quiz results available to download.");
                return;
            }

            const executionCode = latestQuizResults.execution_code;
            // Prepend language code to the API URL
            const downloadUrl = `/${languageCode}/quiz/api/results/${executionCode}/download_pdf/`;

            try {
                const response = await fetch(downloadUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({
                        final_score: latestQuizResults.score,
                        max_score: latestQuizResults.max_score,
                        execution_code: latestQuizResults.execution_code,
                        duration: latestQuizResults.duration,
                        detailed_answers: latestQuizResults.detailed_answers,
                        min_score: latestQuizResults.min_score
                    })
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `quiz_results_${executionCode}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                } else {
                    const errorText = await response.text();
                    alert(`Failed to download PDF: ${response.status} ${response.statusText}\n${errorText}`);
                    console.error('PDF download error:', response.status, response.statusText, errorText);
                }
            } catch (error) {
                console.error('Error during PDF download:', error);
                alert('An error occurred while trying to download the PDF.');
            }
        });
    } else {
        console.warn("PDF download button not found.");
    }

    // --- Core Quiz Functions ---
    // ... (tutte le altre funzioni fino a displayResults rimangono invariate) ...
    function saveCurrentAnswer() {
        const selectedAnswerInput = document.querySelector('input[name="answer"]:checked');
        if (selectedAnswerInput) {
            userAnswers[currentQuestionIndex] = {
                question_id: currentQuestions[currentQuestionIndex].id,
                answer_id: parseInt(selectedAnswerInput.value)
            };
        }
        checkSubmitButtonState();
        updateProgressIndicator();
    }
    function renderProgressIndicator() {
        progressIndicatorDiv.innerHTML = '';
        currentQuestions.forEach((_, index) => {
            const progressBtn = document.createElement('button');
            progressBtn.textContent = index + 1;
            progressBtn.classList.add('progress-btn');
            progressBtn.dataset.index = index;
            progressBtn.addEventListener('click', () => {
                saveCurrentAnswer();
                currentQuestionIndex = index;
                renderQuestion();
            });
            progressIndicatorDiv.appendChild(progressBtn);
        });
    }
    function updateProgressIndicator() {
        const progressBtns = document.querySelectorAll('.progress-btn');
        progressBtns.forEach((btn, index) => {
            btn.classList.remove('current', 'answered');
            if (userAnswers[index] !== null) {
                btn.classList.add('answered');
            }
            if (index === currentQuestionIndex) {
                btn.classList.add('current');
            }
        });
    }
    function jumpToQuestion(index) {
        if (index >= 0 && index < currentQuestions.length) {
            saveCurrentAnswer();
            currentQuestionIndex = index;
            renderQuestion();
        }
    }
    function renderQuestion() {
        const question = currentQuestions[currentQuestionIndex];
        questionNumberElement.textContent = `Question ${currentQuestionIndex + 1}/${currentQuestions.length}`;
        questionTextElement.innerHTML = question.text;

        answerOptionsDiv.innerHTML = '';
        const shuffledAnswers = shuffleArray([...question.answers]);

        shuffledAnswers.forEach(answer => {
            const answerDiv = document.createElement('div');
            const radioInput = document.createElement('input');
            radioInput.type = 'radio';
            radioInput.name = 'answer';
            radioInput.value = answer.id;
            radioInput.id = `answer-${answer.id}`;

            if (userAnswers[currentQuestionIndex] && userAnswers[currentQuestionIndex].answer_id === answer.id) {
                radioInput.checked = true;
            }

            const label = document.createElement('label');
            label.htmlFor = `answer-${answer.id}`;
            label.innerHTML = answer.text;

            answerDiv.appendChild(radioInput);
            answerDiv.appendChild(label);
            answerOptionsDiv.appendChild(answerDiv);
        });
        
        prevQuestionBtn.style.display = currentQuestionIndex > 0 ? 'inline-block' : 'none';
        nextQuestionBtn.style.display = currentQuestionIndex < currentQuestions.length - 1 ? 'inline-block' : 'none';

        updateProgressIndicator();
    }
    function checkAllQuestionsAnswered() {
        return userAnswers.every(answer => answer !== null);
    }
    function checkSubmitButtonState() {
        if (checkAllQuestionsAnswered()) {
            finishQuizBtn.disabled = false;
        } else {
            finishQuizBtn.disabled = true;
        }
    }
    async function submitQuizResults() {
        const finalAnswers = userAnswers.filter(a => a !== null);
        if (finalAnswers.length !== currentQuestions.length) {
            alert("Error: Not all questions have been answered.");
            return;
        }
        
        const payload = {
            test_id: currentTestId,
            age: parseInt(ageInput.value),
            sex_id: parseInt(sexSelect.value),
            duration: quizDuration,
            answers: finalAnswers,
        };

        try {
            const response = await fetch(`/${languageCode}/quiz/api/submit_results/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const result = await response.json();
            latestQuizResults = result;
            displayResults(result);

        } catch (error) {
            console.error('Error submitting quiz results:', error);
            alert('Could not submit quiz results. Please try again.');
        }
    }


    // FIX: [Problema 3] Rendiamo la funzione di visualizzazione più robusta
    // assicurandoci che i dati esistano prima di provare a mostrarli.
    function displayResults(results) {
        // Verifica che i dati dei risultati e gli elementi DOM esistano
        if (!results || !finalScoreElement || !executionCodeElement || !timeTakenElement) {
            console.error("Results data or DOM elements are missing.");
            detailedResultsDiv.innerHTML = '<p>Error displaying results.</p>';
            return;
        }

        // Popola i campi con i valori ricevuti
        finalScoreElement.textContent = `${results.score}/${results.max_score}`;
        executionCodeElement.textContent = results.execution_code;
        timeTakenElement.textContent = `${results.duration} seconds`;

        detailedResultsDiv.innerHTML = ''; // Svuota i risultati precedenti
        if (results.detailed_answers && Array.isArray(results.detailed_answers)) {
            results.detailed_answers.forEach(item => {
                const resultItemDiv = document.createElement('div');
                resultItemDiv.classList.add('quiz-result-item');

                const questionText = document.createElement('h4');
                questionText.innerHTML = `Question: ${item.question_text}`;
                resultItemDiv.appendChild(questionText);

                const userAnswer = document.createElement('p');
                userAnswer.innerHTML = `Your Answer: ${item.given_answer_text} ` +
                                    `<span class="${item.is_correct ? 'correct' : 'incorrect'}">` +
                                    `${item.is_correct ? '(Correct)' : '(Incorrect)'}</span>`;
                resultItemDiv.appendChild(userAnswer);

                if (!item.is_correct && item.correction_text) {
                    const correction = document.createElement('p');
                    correction.innerHTML = `Explanation: ${item.correction_text}`;
                    correction.classList.add('correction-text');
                    resultItemDiv.appendChild(correction);
                }
                detailedResultsDiv.appendChild(resultItemDiv);
            });
        }

        const minPassingScore = parseFloat(results.min_score);
        const userScore = parseFloat(results.score);

        const passFailMessageElement = document.getElementById('pass-fail-message');
        if (userScore >= minPassingScore) {
            passFailMessageElement.textContent = `Result: Passed!`;
            passFailMessageElement.style.color = 'green';
            passFailMessageElement.style.fontWeight = 'bold';
        } else {
            passFailMessageElement.textContent = `Result: Failed!`;
            passFailMessageElement.style.color = 'red';
            passFailMessageElement.style.fontWeight = 'bold';
        }

        quizQuestionsDiv.style.display = 'none';
        quizResultsDiv.style.display = 'block';
    }

    // --- Utility Functions ---
    // ... (getCookie e shuffleArray invariati) ...
    function getCookie(name) { let cookieValue = null; if (document.cookie && document.cookie !== '') { const cookies = document.cookie.split(';'); for (let i = 0; i < cookies.length; i++) { const cookie = cookies[i].trim(); if (cookie.substring(0, name.length + 1) === (name + '=')) { cookieValue = decodeURIComponent(cookie.substring(name.length + 1)); break; } } } return cookieValue; }
    function shuffleArray(array) { for (let i = array.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [array[i], array[j]] = [array[j], array[i]]; } return array; }
});