document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const quizContainer = document.getElementById('quiz-container');
    if (!quizContainer) return; // Se il plugin non è in pagina, ferma tutto

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
    let currentQuestions = [];
    let currentQuestionIndex = 0;
    let userAnswers = [];
    let quizStartTime = null;
    let latestQuizResults = null;

    const languageCode = quizContainer.dataset.languageCode || 'en';

    // --- Initialization ---
    async function initializeQuizPlugin() {
        await getSexOptions();
        await loadRandomTestDetails();
    }

    async function loadRandomTestDetails() {
        try {
            const response = await fetch(`/${languageCode}/quiz/api/random_test_id/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            currentTestId = data.test_id;
            quizTitleDisplay.textContent = data.test_name;
            quizDescriptionDisplay.innerHTML = data.test_description;
        } catch (error) {
            console.error('Error loading random test details:', error);
            quizTitleDisplay.textContent = 'Error loading quiz.';
        }
    }

    async function getSexOptions() {
        try {
            const response = await fetch(`/${languageCode}/quiz/api/sex_options/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            sexSelect.innerHTML = '<option value="">Select...</option>';
            data.sex_options.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.id;
                opt.textContent = option.name;
                sexSelect.appendChild(opt);
            });
        } catch (error) {
            console.error('Error fetching sex options:', error);
        }
    }

    // --- Event Listeners ---
    if (quizStartForm) {
        quizStartForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (!ageInput.value || !sexSelect.value) {
                alert('Please enter your age and select your sex.');
                return;
            }
            quizStartTime = Date.now();
            try {
                const response = await fetch(`/${languageCode}/quiz/api/test/${currentTestId}/questions/`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                currentQuestions = data.questions;
                userAnswers = Array(currentQuestions.length).fill(null);
                currentQuestionIndex = 0;
                quizStartForm.style.display = 'none';
                quizQuestionsDiv.style.display = 'block';
                renderProgressIndicator();
                renderQuestion();
            } catch (error) {
                console.error('Error fetching questions:', error);
                alert('Could not load quiz questions.');
            }
        });
    }

    // ===================================================================
    // CORREZIONE #1: L'UNICO POSTO DOVE SI SALVA UNA RISPOSTA
    // ===================================================================
    if (answerOptionsDiv) {
        answerOptionsDiv.addEventListener('click', (event) => {
            if (event.target.type === 'radio') {
                saveCurrentAnswer();
            }
        });
    }
    
    // ===================================================================
    // CORREZIONE #2: I PULSANTI DI NAVIGAZIONE CAMBIANO SOLO DOMANDA
    // ===================================================================
    if (prevQuestionBtn) {
        prevQuestionBtn.addEventListener('click', () => {
            if (currentQuestionIndex > 0) {
                currentQuestionIndex--;
                renderQuestion();
            }
        });
    }

    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', () => {
            if (currentQuestionIndex < currentQuestions.length - 1) {
                currentQuestionIndex++;
                renderQuestion();
            }
        });
    }

    if (finishQuizBtn) {
        finishQuizBtn.addEventListener('click', () => {
            // L'ultima risposta viene salvata dal click sul radio, non qui
            if (userAnswers.every(answer => answer !== null)) {
                const quizDuration = Math.round((Date.now() - quizStartTime) / 1000);
                submitQuizResults(quizDuration);
            } else {
                alert('Please answer all questions before finishing.');
            }
        });
    }
    
    //     Browser: Fa una piccola richiesta di rete (leggerissima).
    // Server: Fa tutto il lavoro di conversione usando la sua potenza di calcolo.
    // Browser: Rimane veloce e reattivo, riceve un file pronto e lo salva.
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async () => {
            // 1. Controlla se abbiamo i risultati del quiz da inviare
            if (!latestQuizResults) {
                console.error("Risultati del quiz non disponibili per il download.");
                return;
            }

            // 2. Fornisce un feedback all'utente e disabilita il pulsante
            downloadPdfBtn.textContent = 'Generazione PDF in corso...';
            downloadPdfBtn.disabled = true;

            try {
                // 3. Chiama l'API del backend che genera il PDF con WeasyPrint
                const response = await fetch(`/${languageCode}/quiz/api/results/${latestQuizResults.execution_code}/download_pdf/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') // Il tuo helper per il token CSRF
                    },
                    // Invia i dati necessari al backend per popolare il template del PDF
                    body: JSON.stringify({
                        final_score: latestQuizResults.score,
                        max_score: latestQuizResults.max_score,
                        detailed_answers: latestQuizResults.detailed_answers,
                        min_score: latestQuizResults.min_score
                    })
                });

                // 4. Se il backend ha risposto correttamente (con il file PDF)
                if (response.ok) {
                    const blob = await response.blob(); // Ottiene il file come oggetto Blob
                    const url = window.URL.createObjectURL(blob); // Crea un URL locale per il file

                    // Crea un link temporaneo e invisibile per avviare il download
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `quiz_results_${latestQuizResults.execution_code}.pdf`; // Nome del file
                    document.body.appendChild(a);
                    a.click(); // Simula il click sul link

                    // Pulisce l'URL e il link temporaneo dopo il download
                    a.remove();
                    window.URL.revokeObjectURL(url);

                } else {
                    // Se il backend ha restituito un errore
                    console.error('Errore dal server durante la generazione del PDF:', response.statusText);
                    alert('Impossibile generare il PDF. Riprova più tardi.');
                }
            } catch (error) {
                // Se c'è stato un errore di rete o altro
                console.error('Errore di rete durante il download del PDF:', error);
                alert('Si è verificato un errore di rete. Controlla la connessione e riprova.');
            } finally {
                // 5. In ogni caso (successo o fallimento), ripristina il pulsante
                downloadPdfBtn.textContent = 'Download PDF';
                downloadPdfBtn.disabled = false;
            }
        });
    }

    
    // --- Core Functions ---
    function saveCurrentAnswer() {
        const selected = document.querySelector('input[name="answer"]:checked');
        if (selected) {
            userAnswers[currentQuestionIndex] = {
                question_id: currentQuestions[currentQuestionIndex].id,
                answer_id: parseInt(selected.value)
            };
        }
        updateProgressIndicator();
        finishQuizBtn.disabled = !userAnswers.every(a => a !== null);
    }
    
    function renderProgressIndicator() {
        progressIndicatorDiv.innerHTML = '';
        currentQuestions.forEach((_, index) => {
            const btn = document.createElement('button');
            btn.textContent = index + 1;
            btn.classList.add('progress-btn');
            btn.addEventListener('click', () => {
                currentQuestionIndex = index;
                renderQuestion();
            });
            progressIndicatorDiv.appendChild(btn);
        });
    }

    function updateProgressIndicator() {
        document.querySelectorAll('.progress-btn').forEach((btn, index) => {
            btn.classList.toggle('answered', userAnswers[index] !== null);
            btn.classList.toggle('current', index === currentQuestionIndex);
        });
    }
    
    function renderQuestion() {
                const question = currentQuestions[currentQuestionIndex];
        questionNumberElement.textContent = `Question ${currentQuestionIndex + 1}/${currentQuestions.length}`;
        questionTextElement.innerHTML = question.text;

        answerOptionsDiv.innerHTML = '';
        shuffleArray(question.answers).forEach(answer => {
            const div = document.createElement('div');
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'answer';
            radio.value = answer.id;
            radio.id = `answer-${answer.id}`;
            // Ripristina la risposta salvata in precedenza per questa domanda, se esiste
            if (userAnswers[currentQuestionIndex]?.answer_id === answer.id) {
                radio.checked = true;
            }
            const label = document.createElement('label');
            label.htmlFor = radio.id;
            label.innerHTML = answer.text;
            div.append(radio, label);
            answerOptionsDiv.appendChild(div);
        });

        prevQuestionBtn.style.visibility = currentQuestionIndex > 0 ? 'visible' : 'hidden';
        nextQuestionBtn.style.visibility = currentQuestionIndex < currentQuestions.length - 1 ? 'visible' : 'hidden';
        
        // Aggiorna lo stato dei pulsanti di progresso alla fine
        updateProgressIndicator();
    }
    
    async function submitQuizResults(duration) {
        try {
            const response = await fetch(`/${languageCode}/quiz/api/submit_results/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({
                    test_id: currentTestId,
                    age: parseInt(ageInput.value),
                    sex_id: parseInt(sexSelect.value),
                    duration: duration,
                    answers: userAnswers,
                }),
            });
            if (!response.ok) throw new Error('Submission failed');
            const result = await response.json();
            latestQuizResults = result;
            displayResults(result);
        } catch (error) {
            console.error('Error submitting results:', error);
            alert('Could not submit results. Please try again.');
        }
    }

    function displayResults(results) {
        finalScoreElement.textContent = `${results.score}/${results.max_score}`;
        executionCodeElement.textContent = results.execution_code;
        timeTakenElement.textContent = `${results.duration} seconds`;

        detailedResultsDiv.innerHTML = '';
        results.detailed_answers.forEach((item, index) => {
            const block = document.createElement('div');
            block.className = 'question-block';
            
            const resultClass = item.is_correct ? 'correct' : 'incorrect';
            const resultText = item.is_correct ? '(Correct)' : '(Incorrect)';
            
            block.innerHTML = `
                <h4>Q${index + 1}: ${item.question_text}</h4>
                <p>Your Answer: ${item.given_answer_text} <span class="${resultClass}">${resultText}</span></p>
            `;

            if (!item.is_correct && item.correction_text) {
                const explanation = document.createElement('div');
                explanation.className = 'explanation';
                explanation.innerHTML = `<strong>Explanation:</strong> ${item.correction_text}`;
                block.appendChild(explanation);
            }
            detailedResultsDiv.appendChild(block);
        });

        const passFailMessage = document.getElementById('pass-fail-message');
        if (passFailMessage) {
            const isPassed = parseFloat(results.score) >= parseFloat(results.min_score);
            passFailMessage.textContent = `Result: ${isPassed ? 'Passed!' : 'Failed!'}`;
            passFailMessage.style.color = isPassed ? 'green' : 'red';
            passFailMessage.style.fontWeight = 'bold';
        }

        quizQuestionsDiv.style.display = 'none';
        quizResultsDiv.style.display = 'block';
    }
    


    function getCookie(name) {
        let value = "; " + document.cookie;
        let parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }

    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    // --- Start the plugin ---
    initializeQuizPlugin();
});