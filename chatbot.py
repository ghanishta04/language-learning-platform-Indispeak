from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user
from app import db

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# Language code mapping for Web Speech API
LANGUAGE_CODES = {
    'Hindi': 'hi-IN',
    'Marathi': 'mr-IN',
    'Malayalam': 'ml-IN',
    'Gujarati': 'gu-IN',
    'Telugu': 'te-IN',
    'Kannada': 'kn-IN',
    'Tamil': 'ta-IN',
    'Odia': 'or-IN',
    'Assamese': 'as-IN',
    'Bengali': 'bn-IN',
    'Konkani': 'mr-IN',
    'Rajasthani': 'hi-IN',
    'Manipuri': 'as-IN',
    'English': 'en-US'
}

# Practice scenarios for each language
PRACTICE_SCENARIOS = {
    'Hindi': {
        'greetings': [
            {'user': 'Namaste', 'bot': 'Namaste! Aap kaise hain?', 'translation': 'Hello! How are you?'},
            {'user': 'Shubh prabhat', 'bot': 'Shubh prabhat! Aaj ka din shubh ho!', 'translation': 'Good morning! May your day be good!'},
            {'user': 'S铁道 goodbye', 'bot': 'Alvida! Phir milenge!', 'translation': 'Goodbye! See you again!'}
        ],
        'basic': [
            {'user': 'Mera naam [name] hai', 'bot': 'Namaste [name]! Bahut khushi hui', 'translation': 'My name is [name] - Nice to meet you [name]!'},
            {'user': 'Main Hindi seekh raha hoon', 'bot': 'Bahut acchi baat hai! Main aapki madad kar sakta hoon', 'translation': 'I am learning Hindi - That is great! I can help you'},
            {'user': 'Kya aap English bolte hain?', 'bot': 'Haan, main thodi English bol sakta hoon', 'translation': 'Do you speak English? - Yes, I can speak a little English'}
        ]
    },
    'Bengali': {
        'greetings': [
            {'user': 'Nomoskar', 'bot': 'Nomoskar! Apni kemon achen?', 'translation': 'Hello! How are you?'},
            {'user': 'Shubho prabhat', 'bot': 'Shubho prabhat! Din shubho hoy!', 'translation': 'Good morning! Have a good day!'},
            {'user': 'Bye', 'bot': 'Odh! Fer hoye debo!', 'translation': 'Bye! See you later!'}
        ],
        'basic': [
            {'user': 'Amar naam [name]', 'bot': 'Nomoskar [name]! Very happy to meet you', 'translation': 'My name is [name] - Nice to meet you [name]!'},
            {'user': 'Ami Bengali shikchi', 'bot': 'Eto bhalo kotha! Ami tomake sahayya korbo', 'translation': 'I am learning Bengali - That is great! I will help you'}
        ]
    },
    'Marathi': {
        'greetings': [
            {'user': 'Namaskar', 'bot': 'Namaskar! Tu kasa ahes?', 'translation': 'Hello! How are you?'},
            {'user': 'Suprabhat', 'bot': 'Suprabhat! Divas cha shubh varshas paros', 'translation': 'Good morning! May you have a blessed day!'}
        ],
        'basic': [
            {'user': 'Mi Marathi shikto', 'bot': 'Galat mahnun nahi! Mi tuze madad karun', 'translation': 'I am learning Marathi - That is great! I will help you'}
        ]
    },
    'Gujarati': {
        'greetings': [
            {'user': 'Kem cho', 'bot': 'Maja ma! Tamari kem cho?', 'translation': 'How are you? - Great! How are you?'},
            {'user': 'Namaste', 'bot': 'Namaste! Su keb che?', 'translation': 'Hello! What are you doing?'}
        ],
        'basic': [
            {'user': 'Hu Gujarati sikhsu', 'bot': 'Bahut nu! Hu tamne madad kar su', 'translation': 'I am learning Gujarati - That is great! I will help you'}
        ]
    },
    'Telugu': {
        'greetings': [
            {'user': 'Vanakam', 'bot': 'Vanakam! Ela undi?', 'translation': 'Hello! How are you?'},
            {'user': 'Shubhram', 'bot': 'Shubhram! Roju chanidi shubhama ledu', 'translation': 'Good morning! Have a blessed day'}
        ],
        'basic': [
            {'user': 'Nenu Telugu kosam', 'bot': 'Ee bhavishyathlo ledu! Nenu nee kosam undi', 'translation': 'I am learning Telugu - That is great! I am here to help you'}
        ]
    },
    'Malayalam': {
        'greetings': [
            {'user': 'Namskaram', 'bot': 'Namskaram! Sthreeyaanu?', 'translation': 'Hello! How are you?'},
            {'user': 'Suprabadham', 'bot': 'Suprabadham! Samayangal mulam', 'translation': 'Good morning! Best wishes for the day'}
        ],
        'basic': [
            {'user': 'Njan Malayalam theriyum', 'bot': 'Sukham aan! Njan ninnehelp cheyyan undi', 'translation': 'I know Malayalam - Great! I can help you'}
        ]
    }
}

# Default responses for when no specific scenario matches
DEFAULT_RESPONSES = {
    'Hindi': [
        'Bahut accha! Aage badhenge. (Very good! We will progress.)',
        'Theek hai! Koi baat nahi. (Okay! No problem.)',
        'Ek baar phir se try karein. (Try once more.)',
        'Shabash! Aap seekh rahe hain. (Great! You are learning.)'
    ],
    'Bengali': [
        'Eto bhalo! Amra ek kichu shikbo. (Very good! We will learn something.)',
        'Thik ache! Kono rosob nai. (Okay! No problem.)'
    ],
    'Marathi': [
        'Lagncha! Tu shikto. (Great! You are learning.)',
        'Sahi ahe! Try kar. (Correct! Try again.)'
    ],
    'Gujarati': [
        'Bahut badhu! (Very good!)',
        'Thai gayu? (Is it done?)'
    ],
    'Telugu': [
        'Ee bhavishyathlo ledu! (That is great!)',
        'Matladuthunna. (I am speaking.)'
    ],
    'Malayalam': [
        'Sukham aan! (Great!)',
        'Njan manasilikkunnu. (I understand.)'
    ],
    'Tamil': [
        'Nalla irukku! Neenga nalla payirchi panreenga. (Great! You are practicing well.)',
        'Sari, meendum oru murai sollunga. (Okay, please say it one more time.)'
    ],
    'Kannada': [
        'Tumba chennagide! Nivu chennagi abhyaasa madtiddira. (Very good! You are practicing well.)',
        'Sari, matte prayatna madi. (Okay, try once again.)'
    ],
    'Odia': [
        'Bahuta bhal! Tume bhala abhyasa karuchha. (Very good! You are practicing well.)',
        'Thik achhi, au thare chesta kara. (Okay, try once again.)'
    ],
    'Assamese': [
        'Khub bhal! Apuni bhal kore abhyas kori ase. (Very good! You are practicing well.)',
        'Bhal, aru eta bar koise saba. (Okay, please say it once more.)'
    ],
    'Konkani': [
        'Khoob borem! Tumi borem riyaz korta. (Very good! You are practicing well.)',
        'Barobar, ekdam punha mhunn sang. (Okay, say it one more time.)'
    ],
    'Rajasthani': [
        'Ghani badiya! Thane badiya reet si abhyas kar ra ho. (Very good! You are practicing well.)',
        'Theek hai, fer ek baar bolo. (Okay, please say it one more time.)'
    ],
    'Manipuri': [
        'Yamna phajai! Nangna phajna practice toure. (Very good! You are practicing well.)',
        'Changa, amuk hanna hairu. (Okay, say it once again.)'
    ],
    'English': [
        'Great! Keep practicing.',
        'Nice sentence. Let us continue.',
        'Well done. Try another phrase.',
        'Good effort. You are improving.'
    ]
}

@chatbot_bp.route('/')
@login_required
def index():
    """Chatbot main page"""
    languages = list(LANGUAGE_CODES.keys())
    scenarios = list(PRACTICE_SCENARIOS.keys())
    response = make_response(render_template('chatbot.html',
                                             languages=languages,
                                             scenarios=scenarios,
                                             language_codes=LANGUAGE_CODES))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@chatbot_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages from the chatbot"""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    language = data.get('language', 'Hindi')
    user_name = (
        getattr(current_user, 'username', None)
        or getattr(current_user, 'name', None)
        or 'Friend'
    )
    
    if not message:
        return jsonify({'success': False, 'error': 'No message provided'}), 400
    
    # Get language-specific responses
    lang_responses = DEFAULT_RESPONSES.get(language, DEFAULT_RESPONSES['English'])
    
    # Simple response generation based on keywords
    response = generate_response(message, language, user_name, lang_responses)
    
    response_text = response.get('text', '').strip()
    translation_text = response.get('translation', '').strip()

    # Show non-English replies as: native text (English meaning)
    if language != 'English' and translation_text:
        if '(' not in response_text and ')' not in response_text:
            response_text = f'{response_text} ({translation_text})'
        # Avoid duplicate meaning line in UI when meaning is already in brackets
        translation_text = ''

    return jsonify({
        'success': True,
        'response': response_text,
        'translation': translation_text,
        'language': language
    })


@chatbot_bp.route('/api/scenarios/<language>')
@login_required
def get_scenarios(language):
    """Get practice scenarios for a specific language"""
    scenarios = PRACTICE_SCENARIOS.get(language, {})
    return jsonify({
        'success': True,
        'scenarios': scenarios
    })


def generate_response(message, language, user_name, default_responses):
    """Generate a response based on the user's message"""
    message_lower = message.lower()
    
    # Greetings
    greetings_hindi = ['namaste', 'namaskar', 'hello', 'hi', 'hey']
    greetings_bengali = ['nomoskar', 'namaskar', 'hello', 'hi']
    greetings_marathi = ['namaskar', 'namste', 'hello', 'hi']
    greetings_gujarati = ['kem cho', 'namaste', 'hello', 'hi']
    greetings_telugu = ['vanakam', 'namaste', 'hello', 'hi']
    greetings_malayalam = ['namskaram', 'namaste', 'hello', 'hi']
    
    # Check for greetings based on language
    if language == 'Hindi':
        if any(greet in message_lower for greet in greetings_hindi):
            return {'text': f'Namaste {user_name}! Aap kaise hain?', 'translation': f'Hello {user_name}! How are you?'}
    elif language == 'Bengali':
        if any(greet in message_lower for greet in greetings_bengali):
            return {'text': f'Nomoskar {user_name}! Apni kemon achen?', 'translation': f'Hello {user_name}! How are you?'}
    elif language == 'Marathi':
        if any(greet in message_lower for greet in greetings_marathi):
            return {'text': f'Namaskar {user_name}! Tu kasa ahes?', 'translation': f'Hello {user_name}! How are you?'}
    elif language == 'Gujarati':
        if any(greet in message_lower for greet in greetings_gujarati):
            return {'text': f'Kem cho {user_name}? Tamari kem cho?', 'translation': f'How are you {user_name}? How are you doing?'}
    elif language == 'Telugu':
        if any(greet in message_lower for greet in greetings_telugu):
            return {'text': f'Vanakam {user_name}! Ela undi?', 'translation': f'Hello {user_name}! How are you?'}
    elif language == 'Malayalam':
        if any(greet in message_lower for greet in greetings_malayalam):
            return {'text': f'Namskaram {user_name}! Sthreeyaanu?', 'translation': f'Hello {user_name}! How are you?'}
    
    # Thank you responses
    thank_words = ['thank', 'thanks', 'dhanyavad', 'dhonnobad', 's谢谢', 'shukriya']
    if any(thank in message_lower for thank in thank_words):
        return {'text': 'Aapka shukriya! Main aapki madad ke liye hoon.', 'translation': 'Thank you! I am here to help you.'}
    
    # Help/Learn responses
    learn_words = ['learn', 'teach', 'teaching', 'learning', 'seekh', 'shikh', 'sikh']
    if any(word in message_lower for word in learn_words):
        if language == 'Hindi':
            return {'text': 'Bahut acchi baat hai! Aap mujhse Hindi mein baat kar sakte hain. Main aapko sahi tarika se samjhaunga.', 'translation': 'That is great! You can talk to me in Hindi. I will teach you the right way.'}
        elif language == 'Bengali':
            return {'text': 'Eto bhalo kotha! Apni amay Bengali bolte parben. Ami apnake shikhabo.', 'translation': 'That is great! You can speak to me in Bengali. I will teach you.'}
        else:
            return {'text': 'Great! Let us practice together!', 'translation': 'Great! Let us practice together!'}
    
    # Name responses
    name_words = ['name', 'naam', 'nam', 'name']
    if any(word in message_lower for word in name_words):
        return {'text': f'Mera naam Indispeak Bot hai. Main aapki language learning mein madad karunga.', 'translation': 'My name is Indispeak Bot. I will help you with language learning.'}
    
    # Goodbye responses
    bye_words = ['bye', 'goodbye', 'alvida', 'odh', 'byebye', 'ta ta']
    if any(bye in message_lower for bye in bye_words):
        if language == 'Hindi':
            return {'text': 'Alvida! Fir milenge!', 'translation': 'Goodbye! See you again!'}
        elif language == 'Bengali':
            return {'text': 'Odh! Fer hoye debo!', 'translation': 'Bye! See you later!'}
        else:
            return {'text': 'Goodbye! Keep practicing!', 'translation': 'Goodbye! Keep practicing!'}
    
    # How are you responses
    how_are_you = ['kaise', 'kemon', 'kasa', 'ela', 'kem', 'how are']
    if any(phrase in message_lower for phrase in how_are_you):
        if language == 'Hindi':
            return {'text': 'Main theek hoon! Aap kaise hain?', 'translation': 'I am fine! How are you?'}
        elif language == 'Bengali':
            return {'text': 'Ami bhalo achi. Apni kemon achen?', 'translation': 'I am fine. How are you?'}
        else:
            return {'text': 'I am doing great! How are you?', 'translation': 'I am doing great! How are you?'}
    
    # Default random response
    import random
    default_text = random.choice(default_responses)
    return {'text': default_text, 'translation': ''}
