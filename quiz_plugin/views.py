import json
import random
# uuid non è più usato, ma lo lascio per non creare confusione
import uuid 
from datetime import datetime, timedelta
import logging

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction
# NUOVO: Import per renderizzare il template
from django.template.loader import render_to_string

# RIMOSSO: Tutti gli import di ReportLab non sono più necessari
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.units import inch
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.enums import TA_CENTER, TA_LEFT
# from reportlab.lib.colors import black, green, red, darkgrey, lightgrey, white

# NUOVO: Importa WeasyPrint
from weasyprint import HTML

from .models import Test, QuestionInTest, Question, Answer, Sex, TestExecution, GivenAnswer
# Logger setup
logger = logging.getLogger(__name__)

# QUIZ_MIN_SCORE = 1 # This global variable is now less relevant for PDF generation, as min_score comes from the Test model
@csrf_exempt
@require_POST # Aggiungo il decoratore per coerenza, POST è l'unico metodo accettato
def download_quiz_pdf(request, execution_code=None):
    """
    Generates a PDF from an HTML template using WeasyPrint.
    """
    try:
        # 1. Carica i dati inviati dal frontend
        data = json.loads(request.body)
        logger.info(f"Generating PDF for {execution_code} with WeasyPrint.")

        # 2. Prepara il "contesto" per il template Django
        #    Uso .get() con un valore di default per sicurezza
        score = data.get('final_score', 0)
        min_score = data.get('min_score', 1)

        context = {
            'execution_code': execution_code,
            'score': score,
            'max_score': data.get('max_score'),
            'detailed_answers': data.get('detailed_answers', []),
            'pass_status': "Passed" if float(score) >= float(min_score) else "Failed"
        }

        # 3. Renderizza il template HTML in una stringa
        #    Assicurati che il percorso del template sia corretto: 'nome_app/nome_template.html'
        html_string = render_to_string('quiz_plugin/results_pdf.html', context)

        # 4. Crea la risposta HTTP per il PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quiz_results_{execution_code}.pdf"'

        # 5. WeasyPrint converte la stringa HTML in un PDF
        HTML(string=html_string).write_pdf(response)

        return response

    except Exception as e:
        logger.exception("Error generating PDF with WeasyPrint")
        return HttpResponse(f"An error occurred during PDF generation: {e}", status=500)


# =========================================================================
#  TUTTE LE ALTRE VISTE RIMANGONO ESATTAMENTE COME ERANO
# =========================================================================
@require_GET
def get_sex_options(request):
    """
    Returns a list of available sex options.
    """
    sex_options = [{'id': s.id, 'name': s.name} for s in Sex.objects.all().order_by('id')]
    return JsonResponse({'sex_options': sex_options})

@require_GET
def get_random_test_id(request):
    """
    Returns the ID, name, and description of a randomly selected Test.
    """
    try:
        tests = list(Test.objects.all()) # Fetch all Test objects
        if not tests:
            return JsonResponse({'error': 'No tests available.'}, status=404)

        random_test = random.choice(tests) # Select a random Test object
        return JsonResponse({
            'test_id': random_test.id,
            'test_name': random_test.name,         # Include test name
            'test_description': random_test.description # Include test description
        })
    except Exception as e:
        logger.exception("Error in get_random_test_id.")
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

@require_GET
def get_random_test_questions(request, test_id):
    """
    Retrieves and shuffles questions and their answers for a given test ID.
    """
    try:
        test = get_object_or_404(Test, id=test_id)
        question_in_tests = QuestionInTest.objects.filter(id_test=test).select_related('id_question')

        questions_data = []
        for qit in question_in_tests:
            question = qit.id_question
            db_answers = list(Answer.objects.filter(id_question=question).values('id', 'text'))
            formatted_answers = [{'id': ans['id'], 'text': ans['text']} for ans in db_answers]
            random.shuffle(formatted_answers) # Shuffle answers for each question

            questions_data.append({
                'id': question.id,
                'text': question.text,
                'answers': formatted_answers
            })

        random.shuffle(questions_data) # Shuffle the order of questions
        return JsonResponse({'questions': questions_data})

    except Test.DoesNotExist:
        logger.error(f"Test with ID {test_id} not found.")
        return JsonResponse({'error': 'Test not found.'}, status=404)
    except Exception as e:
        logger.exception("Error in get_random_test_questions.")
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

@csrf_exempt
@require_POST
def submit_results(request):
    """
    Receives user answers, calculates score, saves test execution,
    and returns detailed results including the test's minimum passing score.
    """
    try:
        data = json.loads(request.body)
        test_id = data.get('test_id')
        age = data.get('age')
        sex_id = data.get('sex_id')
        duration_seconds = data.get('duration')
        user_answers_data = data.get('answers', [])

        if not all([test_id, age, sex_id, duration_seconds is not None, user_answers_data is not None]):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        test = get_object_or_404(Test, id=test_id)
        sex = get_object_or_404(Sex, id=sex_id)

        total_score = 0
        max_possible_score = 0
        detailed_answers_for_response = []

        with transaction.atomic(): # Ensure atomicity for database operations
            execution_code = datetime.now().strftime('%Y%m%d%H%M%S') + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
            duration_timedelta = timedelta(seconds=duration_seconds)

            test_execution = TestExecution.objects.create(
                id=execution_code,
                execution_time=datetime.now(),
                age=age,
                id_sex=sex,
                id_test=test,
                score=0, # Initial score, will be updated
                IP=request.META.get('REMOTE_ADDR', 'Unknown'),
                duration=duration_timedelta
            )

            for ua in user_answers_data:
                question_id = ua['question_id']
                given_answer_id = ua['answer_id']
                question = get_object_or_404(Question, id=question_id)
                given_answer = get_object_or_404(Answer, id=given_answer_id, id_question=question)

                GivenAnswer.objects.create(
                    id_testExecution=test_execution,
                    id_answer=given_answer,
                    id_question=question
                )

                total_score += given_answer.score
                is_correct = (given_answer.score == 1)

                # Calculate max possible score based on questions that have a correct answer (score=1)
                if Answer.objects.filter(id_question=question, score=1).exists():
                    max_possible_score += 1

                detailed_answers_for_response.append({
                    'question_text': question.text,
                    'given_answer_text': given_answer.text,
                    'is_correct': is_correct,
                    'correction_text': given_answer.correction if not is_correct and given_answer.correction else None
                })

            test_execution.score = total_score
            test_execution.save()

        return JsonResponse({
            'execution_code': execution_code,
            'score': total_score,
            'max_score': max_possible_score,
            'duration': duration_seconds,
            'detailed_answers': detailed_answers_for_response,
            'min_score': float(test.min_score) # <--- Include test's min_score in the response for frontend use
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body for submit_results.")
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except (Test.DoesNotExist, Sex.DoesNotExist, Question.DoesNotExist, Answer.DoesNotExist) as e:
        logger.error(f"Data not found error in submit_results: {e}")
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        logger.exception("Unexpected error in submit_results.")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

@require_GET
def get_sex_options(request):
    """
    Returns a list of available sex options.
    """
    sex_options = [{'id': s.id, 'name': s.name} for s in Sex.objects.all().order_by('id')]
    return JsonResponse({'sex_options': sex_options})

@require_GET
def get_random_test_id(request):
    """
    Returns the ID, name, and description of a randomly selected Test.
    """
    try:
        tests = list(Test.objects.all()) # Fetch all Test objects
        if not tests:
            return JsonResponse({'error': 'No tests available.'}, status=404)

        random_test = random.choice(tests) # Select a random Test object
        return JsonResponse({
            'test_id': random_test.id,
            'test_name': random_test.name,         # Include test name
            'test_description': random_test.description # Include test description
        })
    except Exception as e:
        logger.exception("Error in get_random_test_id.")
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

@require_GET
def get_random_test_questions(request, test_id):
    """
    Retrieves and shuffles questions and their answers for a given test ID.
    """
    try:
        test = get_object_or_404(Test, id=test_id)
        question_in_tests = QuestionInTest.objects.filter(id_test=test).select_related('id_question')

        questions_data = []
        for qit in question_in_tests:
            question = qit.id_question
            db_answers = list(Answer.objects.filter(id_question=question).values('id', 'text'))
            formatted_answers = [{'id': ans['id'], 'text': ans['text']} for ans in db_answers]
            random.shuffle(formatted_answers) # Shuffle answers for each question

            questions_data.append({
                'id': question.id,
                'text': question.text,
                'answers': formatted_answers
            })

        random.shuffle(questions_data) # Shuffle the order of questions
        return JsonResponse({'questions': questions_data})

    except Test.DoesNotExist:
        logger.error(f"Test with ID {test_id} not found.")
        return JsonResponse({'error': 'Test not found.'}, status=404)
    except Exception as e:
        logger.exception("Error in get_random_test_questions.")
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

@csrf_exempt
@require_POST
def submit_results(request):
    """
    Receives user answers, calculates score, saves test execution,
    and returns detailed results including the test's minimum passing score.
    """
    try:
        data = json.loads(request.body)
        test_id = data.get('test_id')
        age = data.get('age')
        sex_id = data.get('sex_id')
        duration_seconds = data.get('duration')
        user_answers_data = data.get('answers', [])

        if not all([test_id, age, sex_id, duration_seconds is not None, user_answers_data is not None]):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        test = get_object_or_404(Test, id=test_id)
        sex = get_object_or_404(Sex, id=sex_id)

        total_score = 0
        max_possible_score = 0
        detailed_answers_for_response = []

        with transaction.atomic(): # Ensure atomicity for database operations
            execution_code = datetime.now().strftime('%Y%m%d%H%M%S') + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
            duration_timedelta = timedelta(seconds=duration_seconds)

            test_execution = TestExecution.objects.create(
                id=execution_code,
                execution_time=datetime.now(),
                age=age,
                id_sex=sex,
                id_test=test,
                score=0, # Initial score, will be updated
                IP=request.META.get('REMOTE_ADDR', 'Unknown'),
                duration=duration_timedelta
            )

            for ua in user_answers_data:
                question_id = ua['question_id']
                given_answer_id = ua['answer_id']
                question = get_object_or_404(Question, id=question_id)
                given_answer = get_object_or_404(Answer, id=given_answer_id, id_question=question)

                GivenAnswer.objects.create(
                    id_testExecution=test_execution,
                    id_answer=given_answer,
                    id_question=question
                )

                total_score += given_answer.score
                is_correct = (given_answer.score == 1)

                # Calculate max possible score based on questions that have a correct answer (score=1)
                if Answer.objects.filter(id_question=question, score=1).exists():
                    max_possible_score += 1

                detailed_answers_for_response.append({
                    'question_text': question.text,
                    'given_answer_text': given_answer.text,
                    'is_correct': is_correct,
                    'correction_text': given_answer.correction if not is_correct and given_answer.correction else None
                })

            test_execution.score = total_score
            test_execution.save()

        return JsonResponse({
            'execution_code': execution_code,
            'score': total_score,
            'max_score': max_possible_score,
            'duration': duration_seconds,
            'detailed_answers': detailed_answers_for_response,
            'min_score': float(test.min_score) # <--- Include test's min_score in the response for frontend use
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body for submit_results.")
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except (Test.DoesNotExist, Sex.DoesNotExist, Question.DoesNotExist, Answer.DoesNotExist) as e:
        logger.error(f"Data not found error in submit_results: {e}")
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        logger.exception("Unexpected error in submit_results.")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

