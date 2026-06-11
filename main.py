from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Language, Lesson, CompletedLesson, QuizScore, User, UserCourse
from app.lesson_data import LESSONS_DATA

main_bp = Blueprint('main', __name__)

# Language data with emojis
LANGUAGE_DATA = [
    ('Marathi', '🙏'),
    ('Hindi', '🟧'),
    ('Malayalam', '🌴'),
    ('Gujarati', '💠'),
    ('Assamese', '🌄'),
    ('Telugu', '🎶'),
    ('Odia', '🌾'),
    ('Kannada', '🌿'),
    ('Konkani', '🏖️'),
    ('Rajasthani', '🏜️'),
    ('Manipuri', '🎭'),
    ('Bengali', '🐅'),
]

# Total lessons per course
TOTAL_LESSONS_PER_COURSE = 10

WORDS_OF_THE_DAY = [
    {'word': 'Namaste', 'meaning': 'Hello in (Hindi)'},
    {'word': 'Namskaram', 'meaning': 'Hello in (Malayalam)'},
    {'word': 'Suswagatam', 'meaning': 'Welcome in (Sanskrit)'},
    {'word': 'Kem Cho', 'meaning': 'How are you? in (Gujarati)'},
    {'word': 'Nomoskar', 'meaning': 'Hello in (Bengali/Assamese)'},
    {'word': 'Vanakam', 'meaning': 'Hello in (Tamil)'},
    {'word': 'Shubhadayam', 'meaning': 'Good morning in (Kannada)'},
    {'word': 'Namaskar', 'meaning': 'Greetings in (Hindi/Marathi)'},
]


def ensure_lesson_record(course_name, lesson_num, lesson_data):
    """Create or fetch the backing Lesson row for a static lesson."""
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

@main_bp.route('/')
def index():
    """Home page / redirect to dashboard if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with language courses"""
    user = current_user
    speak_word_of_day = session.pop('speak_word_of_day_on_dashboard', False)
    
    # Get user's progress
    completed_lessons = CompletedLesson.query.filter_by(user_id=user.id).count()
    quiz_scores = QuizScore.query.filter_by(user_id=user.id).all()
    
    # Calculate statistics
    total_attempts = len(quiz_scores)
    avg_score = 0
    if quiz_scores:
        avg_score = sum(score.score_percentage for score in quiz_scores) / total_attempts
    
    # Prepare languages list
    languages = []
    for name, emoji in LANGUAGE_DATA:
        languages.append({'name': name, 'emoji': emoji})
    
    return render_template('dashboard.html',
                         user=user,
                         languages=languages,
                         speak_word_of_day=speak_word_of_day,
                         completed_lessons=completed_lessons,
                         total_attempts=total_attempts,
                         avg_score=avg_score)


@main_bp.route('/my-courses')
@login_required
def my_courses():
    """Display user's courses - only courses that user has started"""
    user = current_user
    
    # Get only courses that user has started (from UserCourse table)
    started_courses = UserCourse.query.filter_by(user_id=user.id).all()
    started_course_names = {uc.course_name for uc in started_courses}
    
    # Create a mapping of course_name to emoji
    course_emoji_map = {name: emoji for name, emoji in LANGUAGE_DATA}
    
    courses = []
    for course_name in started_course_names:
        emoji = course_emoji_map.get(course_name, '📚')
        
        # Count completed lessons for this course
        completed_count = db.session.query(
            db.func.count(CompletedLesson.id)
        ).filter(
            CompletedLesson.user_id == user.id,
            CompletedLesson.lesson_title.like(f'{course_name}%')
        ).scalar() or 0
        
        # Calculate percentage
        progress_percentage = int((completed_count / TOTAL_LESSONS_PER_COURSE) * 100)
        
        courses.append({
            'name': course_name,
            'emoji': emoji,
            'progress': progress_percentage,
            'completed_lessons': completed_count,
            'total_lessons': TOTAL_LESSONS_PER_COURSE,
            'completed': progress_percentage == 100
        })
    
    return render_template('my_courses.html', courses=courses)


@main_bp.route('/start-course/<course_name>')
@login_required
def start_course(course_name):
    """Start a course - records that user has started the course"""
    user = current_user
    
    # Validate course name
    valid_courses = [name for name, _ in LANGUAGE_DATA]
    if course_name not in valid_courses:
        return redirect(url_for('main.dashboard'))
    
    # Check if user already started this course
    existing = UserCourse.query.filter_by(
        user_id=user.id,
        course_name=course_name
    ).first()
    
    # If not started, record it
    if not existing:
        user_course = UserCourse(
            user_id=user.id,
            course_name=course_name
        )
        db.session.add(user_course)
        db.session.commit()
    
    return render_template('course_view.html', course_name=course_name)


@main_bp.route('/lessons/<course_name>')
@login_required
def lessons(course_name):
    """View lessons for a course"""
    valid_courses = [name for name, _ in LANGUAGE_DATA]
    if course_name not in valid_courses:
        return redirect(url_for('main.dashboard'))
    
    user = current_user
    
    # Get completed lessons for this course
    completed_lessons = CompletedLesson.query.filter(
        CompletedLesson.user_id == user.id,
        CompletedLesson.lesson_title.like(f'{course_name}%')
    ).all()
    
    completed_numbers = set()
    prefix = f'{course_name} Lesson '
    for lesson in completed_lessons:
        if lesson.lesson_title.startswith(prefix):
            remainder = lesson.lesson_title[len(prefix):]
            lesson_number = remainder.split(' - ', 1)[0].strip()
            if lesson_number.isdigit():
                completed_numbers.add(int(lesson_number))
    
    return render_template('lessons.html', 
                         course_name=course_name,
                         completed_numbers=completed_numbers)


@main_bp.route('/lesson/<course_name>/<lesson_num>')
@login_required
def lesson_view(course_name, lesson_num):
    """View individual lesson"""
    valid_courses = [name for name, _ in LANGUAGE_DATA]
    if course_name not in valid_courses:
        return redirect(url_for('main.dashboard'))
    
    try:
        lesson_num = int(lesson_num)
    except ValueError:
        return redirect(url_for('main.lessons', course_name=course_name))
    
    # Validate lesson number (1-10)
    if lesson_num < 1 or lesson_num > 10:
        return redirect(url_for('main.lessons', course_name=course_name))
    
    # Get lesson data for this language and lesson number
    lesson_data = None
    if course_name in LESSONS_DATA:
        lessons = LESSONS_DATA[course_name]
        for lesson in lessons:
            if lesson['lesson_num'] == lesson_num:
                lesson_data = lesson
                break
    
    if not lesson_data:
        return redirect(url_for('main.lessons', course_name=course_name))
    
    lesson = ensure_lesson_record(course_name, lesson_num, lesson_data)
    lesson_title = f"{course_name} Lesson {lesson_num} - {lesson_data['title']}"
    vocabulary = lesson_data['vocabulary']
    lesson_completed = False
    if lesson:
        lesson_completed = CompletedLesson.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id
        ).first() is not None
    
    return render_template('lesson_detail.html',
                         course_name=course_name,
                         lesson_num=lesson_num,
                         lesson_id=lesson.id if lesson else None,
                         lesson_title=lesson_title,
                         vocabulary=vocabulary,
                         lesson_completed=lesson_completed)


@main_bp.route('/mark-completed', methods=['POST'])
@login_required
def mark_completed():
    """Mark a lesson as completed"""
    data = request.get_json()
    lesson_title = data.get('lesson_title')
    lesson_id = data.get('lesson_id')
    
    if not lesson_title or not lesson_id:
        return {'success': False, 'message': 'Invalid lesson'}, 400
    
    # Check if already completed
    existing = CompletedLesson.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not existing:
        completed = CompletedLesson(
            user_id=current_user.id,
            lesson_id=lesson_id,
            lesson_title=lesson_title
        )
        db.session.add(completed)
        db.session.commit()
    
    return {'success': True}


@main_bp.route('/help')
def help():
    """Help page"""
    return render_template('help.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')
