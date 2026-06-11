language-learning-platform-Indispeak

Indispeak: a language learning platform focused on Indian languages (lessons + quizzes + practice chat).
Converted to Python/Flask from an original PHP project.
Core features
<img width="1240" height="743" alt="image" src="https://github.com/user-attachments/assets/94c241a3-ae63-430a-9658-6eabab05a05b" />

Interactive lessons (vocabulary/content loaded per language + per-lesson pages).
Quiz system (multiple choice, scoring, user quiz history).

Progress tracking
Completed lessons tracking
Lesson score saving
Course completion tracking
User stats: completed lessons, attempts, average & best quiz scores
User profiles & settings
Profile info and profile picture upload
Bio support
Password change flow
Chatbot / practice mode
Scenario-based practice per language (greetings/basic phrases)
Keyword-based response generation
Language selection + translation display behavior
UI niceties: dark mode, responsive design, audio pronunciation (via TTS/front-end behavior)
Tech stack

Backend: Flask
Database: SQLite + SQLAlchemy ORM
Auth: Flask-Login
Security: Werkzeug password hashing
Frontend: HTML templates (Jinja2), CSS, vanilla JavaScript
App configuration: config.py (upload folder, session lifetime, secret key, etc.)
Main components (high level)

app/models.py: database schema (Users, Languages, Lessons, Quizzes, Questions, Scores, Completed lessons, UserCourse)
app/routes/:
main.py: dashboard, courses, lesson pages, help/about
auth.py: login/register/logout
courses.py (profile/settings + profile update APIs + password change)
quizzes.py: quiz listing, quiz taking, quiz submission + quiz-question API
api.py: APIs for lesson score saving, marking lessons completed, user stats, word-of-day
chatbot.py: chatbot UI route + chat/scenario APIs + response generator
How learning/progress works

“Start course” creates a user-course record.
Viewing a lesson ensures lesson rows exist in DB (backed by static lesson data).
Finishing lessons triggers completed lesson records and may mark the course complete (e.g., last lesson).
Project setup & runtime

run.py is the entry point.
requirements.txt defines dependencies.
Database tables are created/managed on first run (with migration scripts present, e.g. completed column addition).
Repository assets

HTML templates for each major page (dashboard, lessons, lesson detail, quizzes, profile, chatbot, etc.)
Static assets (CSS/JS) and uploaded images directory.
Roadmap / future ideas (from docs)

Mobile app, advanced analytics, spaced repetition, pronunciation checking, badges/leaderboards, community features, payments, etc.
