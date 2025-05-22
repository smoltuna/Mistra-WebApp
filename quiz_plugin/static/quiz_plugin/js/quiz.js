document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const quizContainer = document.getElementById('quiz-container');
    const quizTitleDisplay = document.getElementById('quiz-title-display');
    const quizDescriptionDisplay = document.getElementById('quiz-description-display');
    const quizStartForm = document.getElementById('quiz-start-form');
    const ageInput = document.getElementById('age');
    const sexSelect = document.getElementById('sex');

    const quizQuestionsDiv = document.getElementById('quiz-questions');
    const questionNumberElement = document.getElementById('question-number');
    const questionTextElement = document.getElementById('question-text');
    const answerOptionsDiv = document.getElementById('answer-options');
    const nextQuestionBtn = document.getElementById('next-question-btn');

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

    // Get the language code from the quiz-container data attribute
    const languageCode = quizContainer.dataset.languageCode || 'en'; // Default to 'en' if not found

    // --- Initialization ---
    async function initializeQuizPlugin() {
        await getSexOptions();
        await loadRandomTestDetails();
    }

    async function loadRandomTestDetails() {
        try {
            // Prepend language code to the API URL
            const randomTestResponse = await fetch(`/${languageCode}/quiz/api/random_test_id/`);
            if (!randomTestResponse.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const randomTestData = await randomTestResponse.json();
            currentTestId = randomTestData.test_id;
            currentTestName = randomTestData.test_name;
            currentTestDescription = randomTestData.test_description;

            if (!currentTestId) {
                quizTitleDisplay.textContent = 'Error: No tests available.';
                console.error('No random test ID could be fetched.');
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
            // Prepend language code to the API URL
            const response = await fetch(`/${languageCode}/quiz/api/sex_options/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
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

    quizStartForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const age = ageInput.value;
        const sex = sexSelect.value;

        if (!age || !sex) {
            alert('Please enter your age and select your sex.');
            return;
        }

        if (!currentTestId) {
            alert('Quiz not loaded yet. Please wait or refresh.');
            return;
        }

        quizStartTime = Date.now();

        try {
            // Prepend language code to the API URL
            const response = await fetch(`/${languageCode}/quiz/api/test/${currentTestId}/questions/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            currentQuestions = data.questions;

            if (currentQuestions.length === 0) {
                alert('No questions found for this test.');
                return;
            }

            currentQuestionIndex = 0;
            userAnswers = [];
            renderQuestion();

        } catch (error) {
            console.error('Error fetching questions:', error);
            alert('Could not load quiz questions. Please try again.');
        }
    });

    nextQuestionBtn.addEventListener('click', () => {
        const selectedAnswerInput = document.querySelector('input[name="answer"]:checked');
        if (!selectedAnswerInput) {
            alert('Please select an answer before proceeding.');
            return;
        }

        userAnswers.push({
            question_id: currentQuestions[currentQuestionIndex].id,
            answer_id: parseInt(selectedAnswerInput.value)
        });

        currentQuestionIndex++;
        renderQuestion();
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

    function renderQuestion() {
        if (currentQuestionIndex < currentQuestions.length) {
            const question = currentQuestions[currentQuestionIndex];

            questionNumberElement.textContent = `Question ${currentQuestionIndex + 1}/${currentQuestions.length}`;
            questionTextElement.innerHTML = question.text;

            answerOptionsDiv.innerHTML = '';

            const shuffledAnswers = shuffleArray(question.answers);

            shuffledAnswers.forEach(answer => {
                const answerDiv = document.createElement('div');
                const radioInput = document.createElement('input');
                radioInput.type = 'radio';
                radioInput.name = 'answer';
                radioInput.value = answer.id;
                radioInput.id = `answer-${answer.id}`;

                const label = document.createElement('label');
                label.htmlFor = `answer-${answer.id}`;
                label.innerHTML = answer.text;

                answerDiv.appendChild(radioInput);
                answerDiv.appendChild(label);
                answerOptionsDiv.appendChild(answerDiv);
            });

            quizStartForm.style.display = 'none';
            quizQuestionsDiv.style.display = 'block';
            quizResultsDiv.style.display = 'none';
        } else {
            quizDuration = Math.round((Date.now() - quizStartTime) / 1000);
            submitQuizResults();
        }
    }

    async function submitQuizResults() {
        const age = ageInput.value;
        const sex = sexSelect.value;
        const csrfToken = getCookie('csrftoken');

        const payload = {
            test_id: currentTestId,
            age: parseInt(age),
            sex_id: parseInt(sex),
            duration: quizDuration,
            answers: userAnswers,
        };

        try {
            // Prepend language code to the API URL
            const response = await fetch(`/${languageCode}/quiz/api/submit_results/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            quizExecutionCode = result.execution_code;
            latestQuizResults = result;
            displayResults(result);
            console.log("Quiz results submitted successfully:", result);

        } catch (error) {
            console.error('Error submitting quiz results:', error);
            alert('Could not submit quiz results. Please try again.');
        }
    }

    function displayResults(results) {
        finalScoreElement.textContent = `${results.score}/${results.max_score}`;
        executionCodeElement.textContent = results.execution_code;
        timeTakenElement.textContent = `${results.duration} seconds`;

        detailedResultsDiv.innerHTML = '';
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

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }
});
