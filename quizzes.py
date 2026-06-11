from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Quiz, Question, QuizScore

quizzes_bp = Blueprint('quizzes', __name__)

@quizzes_bp.route('/quizzes')
@login_required
def quizzes():
    """View all quizzes"""
    quizzes = Quiz.query.all()
    
    # Get user's quiz scores
    user_scores = QuizScore.query.filter_by(user_id=current_user.id).all()
    user_scores_dict = {score.quiz_id: score for score in user_scores}
    
    quiz_list = []
    for quiz in quizzes:
        score_data = user_scores_dict.get(quiz.id)
        quiz_list.append({
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'difficulty': quiz.difficulty,
            'questions_count': len(quiz.questions),
            'user_score': score_data.score_percentage if score_data else None,
            'attempted': score_data is not None
        })
    
    return render_template('quizzes.html', quizzes=quiz_list)


@quizzes_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_view(quiz_id):
    """View and take a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    
    if not questions:
        return redirect(url_for('quizzes.quizzes'))
    
    # Shuffle questions for variety
    import random
    questions = list(questions)
    random.shuffle(questions)
    
    return render_template('quiz_start.html', 
                         quiz=quiz,
                         questions=questions)


@quizzes_bp.route('/api/quiz/<int:quiz_id>/questions')
@login_required
def get_quiz_questions(quiz_id):
    """Get quiz questions as JSON"""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    
    if not questions:
        return jsonify({'success': False, 'message': 'No questions found'}), 404
    
    questions_data = []
    for question in questions:
        questions_data.append({
            'id': question.id,
            'text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d
            }
        })
    
    return jsonify({
        'success': True,
        'quiz_id': quiz.id,
        'title': quiz.title,
        'total_questions': len(questions),
        'questions': questions_data
    })


@quizzes_bp.route('/api/submit-quiz', methods=['POST'])
@login_required
def submit_quiz():
    """Submit quiz answers and save score"""
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    answers = data.get('answers', {})
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Score the quiz
    correct_count = 0
    total_questions = len(quiz.questions)
    
    for question in quiz.questions:
        user_answer = answers.get(str(question.id))
        if user_answer and user_answer.upper() == question.correct_answer:
            correct_count += 1
    
    # Calculate percentage
    percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Save quiz score
    quiz_score = QuizScore(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=correct_count,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=percentage
    )
    
    db.session.add(quiz_score)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'score': correct_count,
        'total': total_questions,
        'percentage': round(percentage, 2),
        'message': f'You scored {correct_count}/{total_questions}'
    })


@quizzes_bp.route('/quiz/results/<int:result_id>')
@login_required
def quiz_results(result_id):
    """View quiz results"""
    result = QuizScore.query.get_or_404(result_id)
    
    # Ensure it's the current user's result
    if result.user_id != current_user.id:
        return redirect(url_for('quizzes.quizzes'))
    
    return render_template('quiz_results.html', result=result)
