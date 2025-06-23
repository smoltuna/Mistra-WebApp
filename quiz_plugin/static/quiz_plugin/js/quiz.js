document.addEventListener('DOMContentLoaded', () => {

    // =============================================================================
    // RIFERIMENTI AGLI ELEMENTI DEL DOM
    // =============================================================================

    // Il contenitore principale
    const quizContainer = document.getElementById('quiz-container');
    if (!quizContainer) return;

    // Elementi per la schermata iniziale del quiz
    const quizTitleDisplay = document.getElementById('quiz-title-display');
    const quizDescriptionDisplay = document.getElementById('quiz-description-display');
    const quizStartForm = document.getElementById('quiz-start-form');
    const ageInput = document.getElementById('age');
    const sexSelect = document.getElementById('sex');

    // Elementi per la schermata delle domande
    const quizQuestionsDiv = document.getElementById('quiz-questions');
    const progressIndicatorDiv = document.getElementById('quiz-navigation-indicator'); // Lista delle domande da scegliere
    const questionNumberElement = document.getElementById('question-number');
    const questionTextElement = document.getElementById('question-text'); //Testo domanda
    const answerOptionsDiv = document.getElementById('answer-options'); // Dove appaiono le risposte (radio button)
    const prevQuestionBtn = document.getElementById('prev-question-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    const finishQuizBtn = document.getElementById('finish-quiz-btn');

    // Elementi per la schermata dei risultati
    const quizResultsDiv = document.getElementById('quiz-results');
    const finalScoreElement = document.getElementById('final-score');
    const executionCodeElement = document.getElementById('execution-code'); // Codice univoco del test
    const timeTakenElement = document.getElementById('time-taken');
    const detailedResultsDiv = document.getElementById('detailed-results'); // Dettaglio domanda per domanda
    const downloadPdfBtn = document.getElementById('download-pdf-btn');

    // =============================================================================
    // VARIABILI DI STATO DEL QUIZ
    // =============================================================================

    // Variabili per memorizzare lo stato corrente del quiz mentre l'utente interagisce.
    let currentTestId = null; // ID del test che l'utente sta svolgendo
    let currentQuestions = []; // Array che conterrà tutte le domande del test
    let currentQuestionIndex = 0; // Indice della domanda corrente
    let userAnswers = []; // Array per memorizzare le risposte date dall'utente
    let quizStartTime = null; // tempo di quando il quiz è iniziato
    let latestQuizResults = null; // Oggetto che conterrà i risultati dell'ultimo test, usato per il PDF


    const languageCode = quizContainer.dataset.languageCode || 'en';


    // =============================================================================
    // INIZIALIZZAZIONE DEL PLUGIN
    // =============================================================================

    /**
     * Carica le opzioni per il sesso e i dettagli di un test casuale.
     */
    async function initializeQuizPlugin() {
        await loadRandomTestDetails();
        await getSexOptions();
    }

    /**
     * Carica i dettagli di un test scelto casualmente dal backend.
     */
    async function loadRandomTestDetails() {
        try {
            // Chiama l'API del backend per ottenere l'ID e i dettagli di un test casuale.
            const response = await fetch(`/${languageCode}/quiz/api/random_test_id/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            // Aggiorna le variabili di stato e l'interfaccia.
            currentTestId = data.test_id;
            quizTitleDisplay.textContent = data.test_name;
            // Usiamo `innerHTML` per la descrizione per permettere la formattazione HTML dal backend.
            quizDescriptionDisplay.innerHTML = data.test_description;

        } catch (error) {
            // Se c'è un errore (es. rete assente), lo mostra nella console e all'utente.
            console.error('Error loading random test details:', error);
            quizTitleDisplay.textContent = 'Errore nel caricamento del quiz.';
        }
    }

    /**
     * Carica le opzioni per il sesso dal backend
     * e le inserisce nel menu a tendina '<select>'.
     */
    async function getSexOptions() {
        try {
            const response = await fetch(`/${languageCode}/quiz/api/sex_options/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            // Pulisce il menu a tendina e aggiunge le nuove opzioni.
            sexSelect.innerHTML = '<option value="">Seleziona...</option>';
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

    // =============================================================================
    // EVENT LISTENERS
    // =============================================================================
    // Qui definiamo come il quiz reagisce alle azioni dell'utente (es. click, submit,).

    // Gestisce l'invio del form iniziale (età e sesso).
    if (quizStartForm) {
        quizStartForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Impedisce il ricaricamento della pagina.
            if (!ageInput.value || !sexSelect.value) {
                alert('Per favore, inserisci la tua età e seleziona il sesso.');
                return;
            }
            quizStartTime = Date.now(); // Memorizza l'ora di inizio.

            // Carica le domande del test.
            try {
                const response = await fetch(`/${languageCode}/quiz/api/test/${currentTestId}/questions/`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                
                // Prepara lo stato del quiz con le domande ricevute.
                currentQuestions = data.questions;
                userAnswers = Array(currentQuestions.length).fill(null); // Array vuoto per le risposte.
                currentQuestionIndex = 0;

                // Nasconde il form iniziale e mostra la prima domanda.
                quizStartForm.style.display = 'none';
                quizQuestionsDiv.style.display = 'block';
                renderProgressIndicator(); // Crea i pulsanti di progresso.
                renderQuestion(); // Mostra la prima domanda.
            } catch (error) {
                console.error('Error fetching questions:', error);
                alert('Impossibile caricare le domande del quiz.');
            }
        });
    }
    
    /**
     * Invece di aggiungere un listener a ogni singolo radio button, aggiungiamo un solo
     * listener al loro contenitore (`answerOptionsDiv`). Questo è molto più efficiente,
     * specialmente quando gli elementi vengono creati e distrutti dinamicamente.
     */
    if (answerOptionsDiv) {
        answerOptionsDiv.addEventListener('click', (event) => {
            // Se l'elemento cliccato è un radio button salvo la risposta
            if (event.target.type === 'radio') {
                saveCurrentAnswer();
            }
        });
    }

    // I pulsanti "Avanti" e "Indietro" cambiano solo l'indice della domanda
    // e poi chiamano 'renderQuestion()' per aggiornare l'interfaccia.
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

    // Gestisce il click sul pulsante "Fine Quiz".
    if (finishQuizBtn) {
        finishQuizBtn.addEventListener('click', () => {
            // Controlla che tutte le domande abbiano una risposta.
            if (userAnswers.every(answer => answer !== null)) {
                const quizDuration = Math.round((Date.now() - quizStartTime) / 1000); // Calcola la durata in secondi.
                submitQuizResults(quizDuration);
            } else {
                alert('Per favore, rispondi a tutte le domande prima di concludere.');
            }
        });
    }
    
    /**
     * Gestione download del PDF.
     * Il browser fa solo richiesta, il server crea e restituisce il PDF
     */
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async () => {
            if (!latestQuizResults) {
                console.error("Risultati del quiz non disponibili per il download.");
                return;
            }

            downloadPdfBtn.textContent = 'Generazione PDF in corso...';
            downloadPdfBtn.disabled = true;

            try {
                // Chiama l'API del backend che genera il PDF (WeasyPrint).
                // Richiesta POST -> inviamo dati al server (risultati dell'utente) ->
                // permette di creare un PDF personalizzato.
                const response = await fetch(`/${languageCode}/quiz/api/results/${latestQuizResults.execution_code}/download_pdf/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') // Token di sicurezza di Django
                    },
                    // Corpo della richiesta contiene i dati per popolare il template del PDF.
                    body: JSON.stringify({
                        final_score: latestQuizResults.score,
                        max_score: latestQuizResults.max_score,
                        detailed_answers: latestQuizResults.detailed_answers,
                        min_score: latestQuizResults.min_score
                    })
                });

                if (response.ok) {
                    // Se il server risponde con successo, il corpo della risposta è il file PDF.
                    const blob = await response.blob(); // Convertiamo la risposta in un oggetto "Blob" (un file grezzo).
                    const url = window.URL.createObjectURL(blob); // Creiamo un URL temporaneo per questo file.

                    //standard per avviare un download da JavaScript:
                    const a = document.createElement('a'); // Crea un link invisibile
                    a.href = url;
                    a.download = `quiz_results_${latestQuizResults.execution_code}.pdf`; // nome
                    document.body.appendChild(a);
                    a.click(); // Scarico

                    // Pulisce tutto dopo il download.
                    a.remove();
                    window.URL.revokeObjectURL(url);

                } else {
                    console.error('Errore dal server durante la generazione del PDF:', response.statusText);
                    alert('Impossibile generare il PDF. Riprova più tardi.');
                }
            } catch (error) {
                console.error('Errore di rete durante il download del PDF:', error);
                alert('Si è verificato un errore di rete. Controlla la connessione e riprova.');
            } finally {
                // Ripristino
                downloadPdfBtn.textContent = 'Download PDF';
                downloadPdfBtn.disabled = false;
            }
        });
    }

    
    // =============================================================================
    // FUNZIONI PRINCIPALI 
    // =============================================================================

    /**
     * Salva la risposta selezionata per la domanda corrente nell'array `userAnswers`.
     */
    function saveCurrentAnswer() {
        // Trova il radio button attualmente selezionato.
        const selected = document.querySelector('input[name="answer"]:checked');
        if (selected) {
            // Salva l'ID della domanda e della risposta scelta.
            userAnswers[currentQuestionIndex] = {
                question_id: currentQuestions[currentQuestionIndex].id,
                answer_id: parseInt(selected.value)
            };
        }
        updateProgressIndicator();

        // Abilito il pulsante "Fine Quiz" solo se tutte le domande hanno ricevuto risposta.
        finishQuizBtn.disabled = !userAnswers.every(a => a !== null);
    }
    
    /**
     * Crea i pulsanti della barra 
     */
    function renderProgressIndicator() {
        progressIndicatorDiv.innerHTML = '';
        currentQuestions.forEach((_, index) => {
            const btn = document.createElement('button');
            btn.textContent = index + 1;
            btn.classList.add('progress-btn');
            // Aggiunge un listener a ogni pulsante per navigare direttamente a quella domanda.
            btn.addEventListener('click', () => {
                currentQuestionIndex = index;
                renderQuestion();
            });
            progressIndicatorDiv.appendChild(btn);
        });
    }

    /**
     * Aggiorna lo stile dei pulsanti di progresso per mostrare
     * qual è la domanda corrente e quali hanno già ricevuto una risposta.
     */
    function updateProgressIndicator() {
        document.querySelectorAll('.progress-btn').forEach((btn, index) => {
            btn.classList.toggle('answered', userAnswers[index] !== null);
            btn.classList.toggle('current', index === currentQuestionIndex);
        });
    }
    
    /**
     * Mostra la domanda corrente e le sue opzioni di risposta.
     * Aggiorna l'interfaccia a ogni cambio di domanda.
     */
    function renderQuestion() {
        const question = currentQuestions[currentQuestionIndex];
        questionNumberElement.textContent = `Domanda ${currentQuestionIndex + 1}/${currentQuestions.length}`;
        questionTextElement.innerHTML = question.text; // `innerHTML` per permettere HTML nel testo della domanda.

        // Pulisce le risposte precedenti.
        answerOptionsDiv.innerHTML = '';
        // Mescola le risposte e crea i radio button.
        shuffleArray(question.answers).forEach(answer => {
            const div = document.createElement('div');
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'answer';
            radio.value = answer.id;
            radio.id = `answer-${answer.id}`;

            // Riprisitino la scelta precedente (se presente).
            if (userAnswers[currentQuestionIndex]?.answer_id === answer.id) {
                radio.checked = true;
            }
            
            const label = document.createElement('label');
            label.htmlFor = radio.id;
            label.innerHTML = answer.text; // `innerHTML` per permettere HTML nel testo della risposta.
            
            div.append(radio, label);
            answerOptionsDiv.appendChild(div);
        });

        // Mostra/nasconde i pulsanti "Avanti" e "Indietro" in base alla posizione nel quiz.
        prevQuestionBtn.style.visibility = currentQuestionIndex > 0 ? 'visible' : 'hidden';
        nextQuestionBtn.style.visibility = currentQuestionIndex < currentQuestions.length - 1 ? 'visible' : 'hidden';
        
        // Aggiorna lo stato dei pulsanti di progresso.
        updateProgressIndicator();
    }
    
    /**
     * Invia i risultati del quiz al backend.
     */
    async function submitQuizResults(duration) {
        try {
            // Prepara il pacchetto di dati da inviare.
            const payload = {
                test_id: currentTestId,
                age: parseInt(ageInput.value),
                sex_id: parseInt(sexSelect.value),
                duration: duration,
                answers: userAnswers,
            };

            const response = await fetch(`/${languageCode}/quiz/api/submit_results/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error('Submission failed');
            
            // Salva i risultati ricevuti dal server e li mostra.
            const result = await response.json();
            latestQuizResults = result; // Salva i risultati per il download del PDF.
            displayResults(result);
        } catch (error) {
            console.error('Error submitting results:', error);
            alert('Impossibile inviare i risultati. Riprova.');
        }
    }

    /**
     * Mostra la schermata finale con i risultati del quiz.
     */
    function displayResults(results) {
        // Popola i campi principali (punteggio, codice, tempo).
        finalScoreElement.textContent = `${results.score}/${results.max_score}`;
        executionCodeElement.textContent = results.execution_code;
        timeTakenElement.textContent = `${results.duration}`;

        // Crea dinamicamente il riepilogo dettagliato delle risposte.
        detailedResultsDiv.innerHTML = '';
        results.detailed_answers.forEach((item, index) => {
            const block = document.createElement('div');
            block.className = 'question-block';
            
            // Risposte corrette o errate.
            const resultClass = item.is_correct ? 'correct' : 'incorrect';
            const resultText = item.is_correct ? '(Corretta)' : '(Errata)';
            
            block.innerHTML = `
                <h4>D${index + 1}: ${item.question_text}</h4>
                <p>La tua risposta: ${item.given_answer_text} <span class="${resultClass}">${resultText}</span></p>
            `;

            // Se la risposta è errata e c'è una spiegazione, la aggiunge.
            if (!item.is_correct && item.correction_text) {
                const explanation = document.createElement('div');
                explanation.className = 'explanation';
                explanation.innerHTML = `<strong>Spiegazione:</strong> ${item.correction_text}`;
                block.appendChild(explanation);
            }
            detailedResultsDiv.appendChild(block);
        });

        // Mostra un messaggio di "Superato" o "Non superato" in base al punteggio.
        const passFailMessage = document.getElementById('pass-fail-message');
        if (passFailMessage) {
            const isPassed = parseFloat(results.score) >= parseFloat(results.min_score);
            passFailMessage.textContent = `Esito: ${isPassed ? 'Superato!' : 'Non Superato'}`;
            passFailMessage.style.color = isPassed ? 'green' : 'red';
            passFailMessage.style.fontWeight = 'bold';
        }

        // Nasconde le domande e mostra la schermata dei risultati.
        quizQuestionsDiv.style.display = 'none';
        quizResultsDiv.style.display = 'block';
    }
    
    // =============================================================================
    // FUNZIONI DI SUPPORTO
    // =============================================================================

    /**
     * Legge un cookie dal browser. Necessario per ottenere il token CSRF di Django.
     * @param {string} name Il nome del cookie da leggere.
     * @returns {string|null} Il valore del cookie o null se non trovato.
     */
    function getCookie(name) {
        let value = "; " + document.cookie;
        let parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }

    /**
     * Mescola un array sul posto usando l'algoritmo di Fisher-Yates.
     * Utile per randomizzare l'ordine delle risposte.
     * @param {Array} array L'array da mescolare.
     * @returns {Array} Lo stesso array, ma mescolato.
     */
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    // --- Avvia l'esecuzione del plugin ---
    initializeQuizPlugin();
});