import re
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Language, Lesson, LessonScore, CompletedLesson, QuizScore, UserCourse
from app.lesson_data import LESSONS_DATA

api_bp = Blueprint('api', __name__, url_prefix='/api')


def get_or_create_lesson(course_name, lesson_num):
    """Resolve a static lesson to a persisted Lesson row."""
    lesson_num = int(lesson_num)
    lesson_items = LESSONS_DATA.get(course_name, [])
    lesson_data = next((item for item in lesson_items if item['lesson_num'] == lesson_num), None)
    if not lesson_data:
        return None

    language = Language.query.filter_by(name=course_name).first()
    if not language:
        return None

    lesson = Lesson.query.filter_by(language_id=language.id, order=lesson_num).first()
    if not lesson:
        lesson = Lesson(
            language_id=language.id,
            title=lesson_data['title'],
            content=lesson_data,
            order=lesson_num
        )
        db.session.add(lesson)
        db.session.commit()

    return lesson

@api_bp.route('/save-score', methods=['POST'])
@login_required
def save_score():
    """Save lesson score"""
    data = request.get_json()
    
    lesson_title = data.get('lesson')
    lesson_id = data.get('lesson_id')
    total_questions = data.get('total')
    correct_answers = data.get('correct')
    
    if not lesson_title or total_questions is None or correct_answers is None:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    
    try:
        total_questions = int(total_questions)
        correct_answers = int(correct_answers)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid question count'}), 400
    
    if not lesson_id:
        match = re.match(r'(.+?) Lesson (\d+) - .+', lesson_title)
        if match:
            lesson = get_or_create_lesson(match.group(1).strip(), match.group(2))
            lesson_id = lesson.id if lesson else None

    if not lesson_id:
        return jsonify({'success': False, 'error': 'Invalid lesson reference'}), 400

    # Calculate percentage
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Save score
    lesson_score = LessonScore(
        user_id=current_user.id,
        lesson_id=lesson_id,
        lesson_title=lesson_title,
        total_questions=total_questions,
        correct_answers=correct_answers,
        score_percentage=percentage
    )
    
    db.session.add(lesson_score)
    
    # Mark lesson as completed if not already
    completed = CompletedLesson.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not completed:
        completed = CompletedLesson(
            user_id=current_user.id,
            lesson_id=lesson_id,
            lesson_title=lesson_title
        )
        db.session.add(completed)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Score saved successfully',
        'score_percentage': round(percentage, 2)
    })


@api_bp.route('/mark-lesson-completed', methods=['POST'])
@login_required
def mark_lesson_completed():
    """Mark a lesson as completed"""
    data = request.get_json()
    lesson_title = data.get('lesson_title')
    lesson_id = data.get('lesson_id')
    
    if not lesson_title:
        return jsonify({'success': False, 'error': 'Invalid lesson'}), 400

    if not lesson_id:
        match = re.match(r'(.+?) Lesson (\d+) - .+', lesson_title)
        if match:
            lesson = get_or_create_lesson(match.group(1).strip(), match.group(2))
            lesson_id = lesson.id if lesson else None

    if not lesson_id:
        return jsonify({'success': False, 'error': 'Invalid lesson reference'}), 400
    
    completed = CompletedLesson.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not completed:
        completed = CompletedLesson(
            user_id=current_user.id,
            lesson_id=lesson_id,
            lesson_title=lesson_title
        )
        db.session.add(completed)
        db.session.commit()
    
    # Parse the lesson_title to extract course name and lesson number
    # Format: "{course_name} Lesson {lesson_num} - {title}"
    # Example: "Hindi Lesson 10 - Weather"
    match = re.match(r'(.+?) Lesson (\d+) - .+', lesson_title)
    
    if match:
        course_name = match.group(1).strip()
        lesson_num = int(match.group(2))
        
        # If this is the last lesson (lesson 10), mark the course as completed
        if lesson_num == 10:
            user_course = UserCourse.query.filter_by(
                user_id=current_user.id,
                course_name=course_name
            ).first()
            
            if user_course and not user_course.completed:
                user_course.completed = True
                user_course.completed_at = datetime.utcnow()
                db.session.commit()
    
    return jsonify({'success': True, 'message': 'Lesson marked as completed'})


@api_bp.route('/user-stats')
@login_required
def user_stats():
    """Get user statistics"""
    user = current_user
    
    completed_lessons = CompletedLesson.query.filter_by(user_id=user.id).count()
    quiz_scores = QuizScore.query.filter_by(user_id=user.id).all()
    
    total_attempts = len(quiz_scores)
    avg_score = 0
    best_score = 0
    
    if quiz_scores:
        scores = [score.score_percentage for score in quiz_scores]
        avg_score = sum(scores) / total_attempts
        best_score = max(scores)
    
    return jsonify({
        'completed_lessons': completed_lessons,
        'total_attempts': total_attempts,
        'average_score': round(avg_score, 2),
        'best_score': round(best_score, 2)
    })


@api_bp.route('/word-of-day')
def word_of_day():
    """Get word of the day"""
    from app.routes.main import WORDS_OF_THE_DAY
    from datetime import date
    
    day_of_year = date.today().timetuple().tm_yday
    word = WORDS_OF_THE_DAY[day_of_year % len(WORDS_OF_THE_DAY)]
    
    return jsonify(word)
