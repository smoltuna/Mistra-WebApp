import json
import random
from datetime import datetime, timedelta
import logging

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.template.loader import render_to_string
from django.db.models import Max
from weasyprint import HTML

from .models import Test,  Question, Answer, Sex, TestExecution, GivenAnswer

logger = logging.getLogger(__name__)


# Esenta questa vista dal controllo CSRF, dato che i dati vengono inviati da JS.
@csrf_exempt
# Permette solo richieste di tipo POST.
@require_POST
def download_quiz_pdf(request, execution_code=None):
    """Genera e restituisce un PDF con i risultati del quiz."""
    try:
        # Carica i dati dei risultati inviati dal frontend.
        data = json.loads(request.body)
        score = data.get('final_score', 0)
        min_score = data.get('min_score', 1)

        # Prepara il contesto da passare al template HTML del PDF.
        context = {
            'execution_code': execution_code,
            'score': score,
            'max_score': data.get('max_score'),
            'detailed_answers': data.get('detailed_answers', []),
            'pass_status': "Passed" if float(score) >= float(min_score) else "Failed"
        }
        
        # Renderizza il template HTML in una stringa.
        html_string = render_to_string('quiz_plugin/results_pdf.html', context)
        # Prepara una risposta HTTP con il tipo di contenuto corretto per un PDF.
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quiz_results_{execution_code}.pdf"'
        
        # WeasyPrint converte la stringa HTML in un PDF e lo scrive nella risposta.
        HTML(string=html_string).write_pdf(response)
        return response
    except Exception as e:
        logger.exception("Error generating PDF with WeasyPrint: %s", e)
        return HttpResponse(f"An error occurred during PDF generation: {e}", status=500)

@require_GET
def get_sex_options(request):
    """Restituisce le opzioni per il sesso in formato JSON."""
    sex_options = list(Sex.objects.all().order_by('id').values('id', 'name'))
    return JsonResponse({'sex_options': sex_options})

@require_GET
def get_random_test_id(request):
    """Seleziona un test casuale dal database e ne restituisce i dettagli base."""
    try:
        # '?' in order_by() seleziona una riga casuale.
        random_test = Test.objects.order_by('?').first()
        if not random_test:
            return JsonResponse({'error': 'No tests available.'}, status=404)
        
        return JsonResponse({
            'test_id': random_test.id,
            'test_name': random_test.name,
            'test_description': random_test.description
        })
    except Exception as e:
        logger.exception("Error in get_random_test_id: %s", e)
        return JsonResponse({'error': f'An error occurred: {e}'}, status=500)
@require_GET
def get_random_test_questions(request, test_id):
    """Dato un ID di test, restituisce le sue domande e risposte in ordine casuale."""
    try:
        test = get_object_or_404(Test, id=test_id)
    
        # Accedi alle domande tramite il manager M2M dell'oggetto 'test'.
        # `prefetch_related` è un'ottimizzazione per caricare tutte le risposte
        # associate con una sola query aggiuntiva, invece di una per ogni domanda.
        questions = test.questions.all().prefetch_related('answers')
        
        questions_data = []
        for question in list(questions):
            # Prepara la lista di risposte per la domanda corrente.
            answers = [{'id': ans.id, 'text': ans.text} for ans in question.answers.all()]
            random.shuffle(answers) # Mescola le risposte.
            questions_data.append({
                'id': question.id,
                'text': question.text,
                'answers': answers
            })
        
        random.shuffle(questions_data) # Mescola le domande.
        return JsonResponse({'questions': questions_data})
    except Exception as e:
        # Aggiungo il nome della funzione al log per un debug più facile
        logger.exception("Error in get_random_test_questions: %s", e)
        return JsonResponse({'error': 'An error occurred.'}, status=500)

@csrf_exempt
@require_POST
@transaction.atomic
def submit_results(request):
    try:
        data = json.loads(request.body)
        test_id = data.get('test_id')
        age = data.get('age')
        sex_id = data.get('sex_id')
        duration_seconds = data.get('duration')
        user_answers = data.get('answers', [])

        if not all([test_id, age, sex_id, duration_seconds is not None]):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        test = get_object_or_404(Test, id=test_id)
        sex = get_object_or_404(Sex, id=sex_id)
        
        execution_code = datetime.now().strftime('%Y%m%d%H%M%S') + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))

        test_execution = TestExecution.objects.create(
            id=execution_code, age=age, id_sex=sex, id_test=test,
            IP=request.META.get('REMOTE_ADDR'), duration=timedelta(seconds=duration_seconds)
        )

        questions_in_test = Question.objects.filter(test=test)
        
        # calcolo del punteggio massimo TOTALE del test
        max_scores_per_question_qs = Answer.objects.filter(id_question__in=questions_in_test).values('id_question').annotate(max_score_for_q=Max('score'))
        max_possible_score = sum(item['max_score_for_q'] for item in max_scores_per_question_qs if item['max_score_for_q'] > 0)
        
        # mappa {question_id: max_score} per un facile accesso
        max_score_map = {item['id_question']: item['max_score_for_q'] for item in max_scores_per_question_qs}

        total_score = 0
        detailed_answers = []

        all_given_answers_pks = [ua['answer_id'] for ua in user_answers]
        answers_qs = Answer.objects.filter(pk__in=all_given_answers_pks).select_related('id_question')
        answers_map = {ans.id: ans for ans in answers_qs}

        for ua in user_answers:
            answer = answers_map.get(ua['answer_id'])
            if not answer or answer.id_question.id != ua['question_id']:
                continue
            
            GivenAnswer.objects.create(
                id_testExecution=test_execution,
                id_answer=answer,
                id_question=answer.id_question
            )
            
            total_score += answer.score

            # Una risposta è "corretta" se il suo punteggio è uguale al massimo
            # punteggio possibile per QUELLA domanda (e se è > 0).
            # max_score_for_this_question = max_score_map.get(answer.id_question.id, 0)

            # Una ripsota è "corretta" se il suo punteggio è maggiore di 0
            is_correct = (answer.score > 0)
            # ===================================================================
            
            detailed_answers.append({
                'question_text': answer.id_question.text,
                'given_answer_text': answer.text,
                'is_correct': is_correct,
                'correction_text': answer.correction if not is_correct and answer.correction else None
            })

        # Aggiorna il punteggio
        test_execution.score = total_score
        test_execution.save()

        # Arrotondiamo i valori a 2 cifre decimali
        formatted_score = round(total_score, 2)
        formatted_max_score = round(max_possible_score, 2)

        return JsonResponse({
            'execution_code': execution_code,
            'score': formatted_score,          
            'max_score': formatted_max_score, 
            'detailed_answers': detailed_answers,
            'min_score': float(test.min_score),
            'duration': duration_seconds 
        })
    except Exception as e:
        logger.exception("Error submitting results: %s", e)
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)