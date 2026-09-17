from flask import Flask, render_template, request, jsonify
import json
import random
from datetime import datetime
import re
from functools import lru_cache

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# ==========================================
# Load FAQ Data
# ==========================================
with open("faq.json", "r", encoding="utf-8") as file:
    faqs = json.load(file)

# Extra multilingual words are added to the FAQ text so that
# Tamil, Hindi and common Tanglish questions can still match.
LANGUAGE_ALIASES = {
    # Tanglish
    "evlo": "how much", "evalo": "how much", "eppo": "when", "epdi": "how",
    "enga": "where", "engae": "where", "enna": "what", "yaru": "who",
    "iruka": "available", "irukku": "available", "venum": "need", "pannanum": "do",
    "pannurathu": "do", "apply panrathu": "apply", "join panrathu": "join",
    "fees ah": "fees", "fee ah": "fee", "timing enna": "timing what",
    "open ah": "open", "close ah": "close", "bro": "",
    # Tamil
    "கல்லூரி": "college", "சேர்க்கை": "admission", "விண்ணப்பம்": "application",
    "படிப்பு": "academics", "துறை": "department", "தேர்வு": "exam",
    "கட்டணம்": "fees fee", "ஹாஸ்டல்": "hostel", "விடுதி": "hostel",
    "நூலகம்": "library", "புத்தகம்": "book books", "வேலைவாய்ப்பு": "placement job",
    "பேருந்து": "bus transport", "போக்குவரத்து": "transport", "நேரம்": "timing time",
    "எப்போது": "when", "எப்படி": "how", "எங்கே": "where", "எவ்வளவு": "how much",
    "என்ன": "what", "தொடர்பு": "contact", "காலை": "morning", "மாலை": "evening",
    # Hindi
    "कॉलेज": "college", "प्रवेश": "admission", "आवेदन": "application",
    "पढ़ाई": "academics", "विभाग": "department", "परीक्षा": "exam",
    "फीस": "fees fee", "छात्रावास": "hostel", "हॉस्टल": "hostel",
    "पुस्तकालय": "library", "किताब": "book books", "प्लेसमेंट": "placement job",
    "बस": "bus transport", "परिवहन": "transport", "समय": "timing time",
    "कब": "when", "कैसे": "how", "कहाँ": "where", "कितना": "how much",
    "क्या": "what", "संपर्क": "contact",
    # Kannada
    "ಕಾಲೇಜು": "college", "ಪ್ರವೇಶ": "admission", "ಅರ್ಜಿ": "application", "ಪರೀಕ್ಷೆ": "exam",
    "ಶುಲ್ಕ": "fees fee", "ಹಾಸ್ಟೆಲ್": "hostel", "ಗ್ರಂಥಾಲಯ": "library", "ನೇಮಕಾತಿ": "placement job",
    "ಬಸ್": "bus transport", "ಸಮಯ": "timing time", "ಎಷ್ಟು": "how much", "ಹೇಗೆ": "how", "ಎಲ್ಲಿ": "where",
    # Telugu
    "కళాశాల": "college", "ప్రవేశం": "admission", "దరఖాస్తు": "application", "పరీక్ష": "exam",
    "ఫీజు": "fees fee", "హాస్టల్": "hostel", "గ్రంథాలయం": "library", "ప్లేస్మెంట్": "placement job",
    "బస్": "bus transport", "సమయం": "timing time", "ఎంత": "how much", "ఎలా": "how", "ఎక్కడ": "where",
    # Gujarati
    "કોલેજ": "college", "પ્રવેશ": "admission", "અરજી": "application", "પરીક્ષા": "exam",
    "ફી": "fees fee", "હોસ્ટેલ": "hostel", "પુસ્તકાલય": "library", "પ્લેસમેન્ટ": "placement job",
    "બસ": "bus transport", "સમય": "timing time", "કેટલું": "how much", "કેવી રીતે": "how", "ક્યાં": "where",
    # Bengali
    "কলেজ": "college", "ভর্তি": "admission", "আবেদন": "application", "পরীক্ষা": "exam",
    "ফি": "fees fee", "হোস্টেল": "hostel", "লাইব্রেরি": "library", "প্লেসমেন্ট": "placement job",
    "বাস": "bus transport", "সময়": "timing time", "কত": "how much", "কীভাবে": "how", "কোথায়": "where",
    # Urdu
    "کالج": "college", "داخلہ": "admission", "درخواست": "application", "امتحان": "exam",
    "فیس": "fees fee", "ہاسٹل": "hostel", "کتب خانہ": "library", "پلیسمنٹ": "placement job",
    "بس": "bus transport", "وقت": "timing time", "کتنا": "how much", "کیسے": "how", "کہاں": "where"
}


def normalize_multilingual(text):
    normalized = text.lower().strip()
    # Long phrases first
    for source, target in sorted(LANGUAGE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        normalized = normalized.replace(source.lower(), f" {target} ")
    return re.sub(r"\s+", " ", normalized).strip()


questions = [
    faq["question"] + " " + " ".join(faq["keywords"]) + " " +
    " ".join(LANGUAGE_ALIASES.keys())
    for faq in faqs
]

# ==========================================
# NLP Model
# ==========================================
vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2))
faq_vectors = vectorizer.fit_transform(questions)

# ==========================================
# Friendly Chat — multilingual
# ==========================================
friendly_messages = {
    "en": {
        "greeting": [
            "Hey! 👋 I'm CampusBuddy. How can I help you today? 😊",
            "Hello bro! 😄 What can I help you with?",
            "Hey there! 👋 Need any help with college information?",
            "Hi! 😊 I'm your CampusBuddy. Ask me anything about college!"
        ],
        "how_are_you": ["I'm doing great! 😄 Thanks for asking. How can I help you?", "I'm good bro! 🤖 Always ready to help!"],
        "thanks": ["Anytime bro! 😄 Happy to help.", "You're welcome! 😊 That's what I'm here for."],
        "bye": ["Bye bro! 👋 Have a great day!", "See you! 😊 Take care and have a great college day!"],
        "bored": ["Haha 😄 College life can get boring sometimes! Want to know something about campus?", "Bored ah? 😂 Try asking me about placements, library, hostel or exams!"],
        "confused": ["No worries bro 😊 Tell me what you're confused about and I'll try to help.", "It's okay! 😄 Ask me in your own words."],
        "general": ["Sure bro! 😊 Ask me anything related to college.", "I'm listening 👂 Ask me your question!"]
    },
    "ta": {
        "greeting": ["வணக்கம்! 👋 நான் CampusBuddy. இன்று என்ன உதவி வேண்டும்? 😊", "ஹாய் bro! 😄 கல்லூரி பற்றிய எந்த கேள்வியும் கேளுங்க!"],
        "how_are_you": ["நான் நல்லா இருக்கேன் bro! 😄 கேட்டதுக்கு thanks. என்ன கேட்கணும்?", "செம்மையா இருக்கேன்! 🤖 உங்களுக்கு help பண்ண ready!"],
        "thanks": ["எப்போதும் bro! 😄 சந்தோஷமா help பண்றேன்.", "பரவாயில்லை! 😊 எப்போது வேண்டுமானாலும் கேளுங்க."],
        "bye": ["Bye bro! 👋 நல்லா இருங்க!", "சரி bro, see you! 😊 கவனமா இருங்க!"],
        "bored": ["Haha 😄 college life-la bore அடிக்கலாம்! Campus பற்றி ஏதாவது கேட்கலாமே?", "Bore ah? 😂 Placement, library, hostel அல்லது exams பற்றி கேளுங்க!"],
        "confused": ["கவலைப்படாதீங்க bro 😊 என்ன குழப்பம்னு சொல்லுங்க, help பண்றேன்.", "பரவாயில்லை! 😄 உங்க கேள்வியை உங்க style-லேயே கேளுங்க."],
        "general": ["சரி bro! 😊 College தொடர்பான எதையும் கேளுங்க.", "நான் கேட்க ready 👂 என்ன தெரிஞ்சிக்கணும்? "]
    },
    "tanglish": {
        "greeting": ["Hey bro! 👋 Naan CampusBuddy. Enna help venum? 😊", "Hi bro! 😄 College pathi enna venalum kelu!"],
        "how_are_you": ["Nalla iruken bro! 😄 Kettadhukku thanks. Enna kekka pora?", "Semma good! 🤖 Unakku help panna always ready!"],
        "thanks": ["Anytime bro! 😄 Happy ah help panren.", "Parava illa bro! 😊 Eppo venalum kelu."],
        "bye": ["Bye bro! 👋 Nalla poitu va!", "See you bro! 😊 Take care!"],
        "bored": ["Haha 😄 College life-la bore adikkalam! Campus pathi edhavadhu kekkalaama?", "Bored ah? 😂 Placement, library, hostel illa exams pathi kelu!"],
        "confused": ["No worries bro 😊 Enna confusion nu sollu, help panren.", "Parava illa! 😄 Un style-la question kelu."],
        "general": ["Sure bro! 😊 College related edhavadhu kelu.", "I'm listening bro 👂 Enna therinjikanum?"]
    },
    "hi": {
        "greeting": ["नमस्ते! 👋 मैं CampusBuddy हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ? 😊", "हैलो bro! 😄 कॉलेज से जुड़ा कोई भी सवाल पूछिए!"],
        "how_are_you": ["मैं बढ़िया हूँ bro! 😄 पूछने के लिए धन्यवाद। आप क्या जानना चाहते हैं?", "मैं अच्छा हूँ! 🤖 आपकी मदद के लिए हमेशा तैयार हूँ!"],
        "thanks": ["कोई बात नहीं bro! 😄 मदद करके खुशी हुई।", "आपका स्वागत है! 😊 जब चाहें पूछिए।"],
        "bye": ["बाय bro! 👋 आपका दिन अच्छा रहे!", "फिर मिलते हैं! 😊 अपना ध्यान रखिए!"],
        "bored": ["Haha 😄 कॉलेज लाइफ कभी-कभी बोरिंग हो सकती है! कैंपस के बारे में कुछ पूछें?", "बोर हो रहे हैं? 😂 प्लेसमेंट, लाइब्रेरी, हॉस्टल या परीक्षा के बारे में पूछें!"],
        "confused": ["कोई चिंता नहीं bro 😊 बताइए किस बात को लेकर confusion है।", "कोई बात नहीं! 😄 अपने शब्दों में सवाल पूछिए।"],
        "general": ["ज़रूर bro! 😊 कॉलेज से जुड़ा कोई भी सवाल पूछिए।", "मैं सुन रहा हूँ 👂 आपको क्या जानना है?"]
    },

    "kn": {
        "greeting": ["ನಮಸ್ಕಾರ! 👋 ನಾನು CampusBuddy. ಇಂದು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ? 😊", "ಹಾಯ್ bro! 😄 ಕಾಲೇಜಿಗೆ ಸಂಬಂಧಿಸಿದ ಯಾವುದೇ ಪ್ರಶ್ನೆ ಕೇಳಿ!"],
        "how_are_you": ["ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ bro! 😄 ಕೇಳಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು. ನಿಮಗೆ ಏನು ತಿಳಿದುಕೊಳ್ಳಬೇಕು?"],
        "thanks": ["ಯಾವಾಗ ಬೇಕಾದರೂ bro! 😄 ಸಹಾಯ ಮಾಡಲು ಸಂತೋಷವಾಗಿದೆ."],
        "bye": ["ಬೈ bro! 👋 ನಿಮ್ಮ ದಿನ ಚೆನ್ನಾಗಿರಲಿ!", "ಮತ್ತೆ ಸಿಗೋಣ! 😊"],
        "bored": ["Haha 😄 College life ಕೆಲವೊಮ್ಮೆ boring ಆಗಬಹುದು! Campus ಬಗ್ಗೆ ಏನಾದರೂ ಕೇಳಿ."],
        "confused": ["ಚಿಂತೆ ಬೇಡ bro 😊 ನಿಮಗೆ ಯಾವ ವಿಷಯದಲ್ಲಿ confusion ಇದೆ ಹೇಳಿ."],
        "general": ["ಖಂಡಿತ bro! 😊 College ಬಗ್ಗೆ ಏನಾದರೂ ಕೇಳಿ."]
    },
    "ur": {
        "greeting": ["السلام علیکم! 👋 میں CampusBuddy ہوں۔ آج میں آپ کی کیسے مدد کر سکتا ہوں؟ 😊", "ہیلو bro! 😄 کالج سے متعلق کوئی بھی سوال پوچھیں!"],
        "how_are_you": ["میں بالکل ٹھیک ہوں bro! 😄 پوچھنے کا شکریہ۔ آپ کیا جاننا چاہتے ہیں؟"],
        "thanks": ["کبھی بھی bro! 😄 مدد کرکے خوشی ہوئی۔"],
        "bye": ["بائے bro! 👋 آپ کا دن اچھا گزرے!", "پھر ملیں گے! 😊"],
        "bored": ["Haha 😄 کالج لائف کبھی کبھی boring ہو سکتی ہے! Campus کے بارے میں کچھ پوچھیں۔"],
        "confused": ["فکر نہ کریں bro 😊 بتائیں کس بات میں confusion ہے۔"],
        "general": ["ضرور bro! 😊 کالج سے متعلق کچھ بھی پوچھیں۔"]
    },
    "gu": {
        "greeting": ["નમસ્તે! 👋 હું CampusBuddy છું. આજે હું તમારી કેવી રીતે મદદ કરી શકું? 😊", "હેલો bro! 😄 કોલેજ સંબંધિત કોઈપણ પ્રશ્ન પૂછો!"],
        "how_are_you": ["હું મજામાં છું bro! 😄 પૂછવા બદલ આભાર. તમને શું જાણવું છે?"],
        "thanks": ["ક્યારેય પણ bro! 😄 મદદ કરીને ખુશી થઈ."],
        "bye": ["બાય bro! 👋 તમારો દિવસ સારો રહે!", "ફરી મળીશું! 😊"],
        "bored": ["Haha 😄 College life ક્યારેક boring થઈ શકે! Campus વિશે કંઈક પૂછો."],
        "confused": ["ચિંતા ન કરો bro 😊 તમને શું confusion છે તે કહો."],
        "general": ["ચોક્કસ bro! 😊 College વિશે કંઈપણ પૂછો."]
    },
    "te": {
        "greeting": ["నమస్కారం! 👋 నేను CampusBuddy. ఈ రోజు మీకు ఎలా సహాయం చేయగలను? 😊", "హాయ్ bro! 😄 కాలేజీ గురించి ఏ ప్రశ్నైనా అడగండి!"],
        "how_are_you": ["నేను బాగున్నాను bro! 😄 అడిగినందుకు ధన్యవాదాలు. మీకు ఏమి తెలుసుకోవాలి?"],
        "thanks": ["ఎప్పుడైనా bro! 😄 సహాయం చేయడం ఆనందంగా ఉంది."],
        "bye": ["బై bro! 👋 మీ రోజు బాగుండాలి!", "మళ్లీ కలుద్దాం! 😊"],
        "bored": ["Haha 😄 College life కొన్నిసార్లు boring గా ఉంటుంది! Campus గురించి ఏదైనా అడగండి."],
        "confused": ["పర్లేదు bro 😊 ఏ విషయం గురించి confusion ఉందో చెప్పండి."],
        "general": ["తప్పకుండా bro! 😊 College గురించి ఏదైనా అడగండి."]
    },
    "mr": {
        "greeting": ["नमस्कार! 👋 मी CampusBuddy आहे. आज मी तुमची कशी मदत करू शकतो? 😊", "हाय bro! 😄 कॉलेजशी संबंधित कोणताही प्रश्न विचारा!"],
        "how_are_you": ["मी छान आहे bro! 😄 विचारल्याबद्दल धन्यवाद. तुम्हाला काय जाणून घ्यायचे आहे?"],
        "thanks": ["कधीही bro! 😄 मदत करून आनंद झाला."],
        "bye": ["बाय bro! 👋 तुमचा दिवस छान जावो!", "पुन्हा भेटूया! 😊"],
        "bored": ["Haha 😄 College life कधी कधी boring होऊ शकते! Campus बद्दल काही विचारा."],
        "confused": ["काळजी करू नका bro 😊 तुम्हाला कशाबद्दल confusion आहे ते सांगा."],
        "general": ["नक्की bro! 😊 College बद्दल काहीही विचारा."]
    },
    "bn": {
        "greeting": ["নমস্কার! 👋 আমি CampusBuddy। আজ আমি কীভাবে সাহায্য করতে পারি? 😊", "হাই bro! 😄 কলেজ সম্পর্কে যেকোনো প্রশ্ন করুন!"],
        "how_are_you": ["আমি ভালো আছি bro! 😄 জিজ্ঞেস করার জন্য ধন্যবাদ। আপনি কী জানতে চান?"],
        "thanks": ["যেকোনো সময় bro! 😄 সাহায্য করতে পেরে ভালো লাগছে।"],
        "bye": ["বাই bro! 👋 আপনার দিন ভালো কাটুক!", "আবার দেখা হবে! 😊"],
        "bored": ["Haha 😄 College life মাঝে মাঝে boring হতে পারে! Campus সম্পর্কে কিছু জিজ্ঞেস করুন."],
        "confused": ["চিন্তা করবেন না bro 😊 কী নিয়ে confusion হচ্ছে বলুন."],
        "general": ["অবশ্যই bro! 😊 College সম্পর্কে যেকোনো কিছু জিজ্ঞেস করুন."]
    }
}

# ==========================================
# Offline FAQ answer translations
# ==========================================
FAQ_TRANSLATIONS = {
    1: {"ta": "சேர்க்கைக்கான தகுதி மற்றும் நடைமுறை கல்லூரியின் விதிமுறைகள் மற்றும் குறிப்பிட்ட பாடத்திட்டத்தைப் பொறுத்தது. சமீபத்திய விவரங்களுக்கு Admission Office-ஐ தொடர்பு கொள்ளுங்கள்.", "tanglish": "Admission eligibility and process college rules-um course-um depend aagum. Latest details-ku Admission Office-a contact pannunga.", "hi": "प्रवेश की पात्रता और प्रक्रिया कॉलेज के नियमों तथा संबंधित पाठ्यक्रम पर निर्भर करती है। नवीनतम जानकारी के लिए Admission Office से संपर्क करें."},
    2: {"ta": "கல்லூரி சேர்க்கைக்கு தேவையான ஆவணங்கள் பாடத்திட்டத்தைப் பொறுத்து மாறலாம். பொதுவாக mark sheets, ID proof மற்றும் passport-size photos தேவைப்படலாம்.", "tanglish": "Admission-ku thevaiyana documents course-ku depend aagum. Usually mark sheets, ID proof and passport-size photos thevai padalam.", "hi": "प्रवेश के लिए आवश्यक दस्तावेज़ पाठ्यक्रम के अनुसार बदल सकते हैं। आमतौर पर mark sheets, ID proof और passport-size photos की आवश्यकता हो सकती है."},
    3: {"ta": "கல்லூரியின் வழிகாட்டுதலின்படி ஆன்லைன் அல்லது Admission Office மூலம் விண்ணப்பிக்கலாம்.", "tanglish": "College guidelines padi online illa Admission Office moolama apply pannalam.", "hi": "कॉलेज के दिशानिर्देशों के अनुसार ऑनलाइन या Admission Office के माध्यम से आवेदन किया जा सकता है."},
    4: {"ta": "பொதுவாக கல்லூரி நேரம் காலை 9:00 மணி முதல் மாலை 4:30 மணி வரை இருக்கும். உங்கள் துறையின் குறிப்பிட்ட நேரத்தை சரிபார்க்கவும்.", "tanglish": "Usually college timing morning 9:00 AM to evening 4:30 PM. Unga department specific timing-a check pannunga.", "hi": "आम तौर पर कॉलेज का समय सुबह 9:00 बजे से शाम 4:30 बजे तक होता है। अपने विभाग का विशेष समय जाँच करें."},
    5: {"ta": "கல்லூரி விதிமுறைகளில் குறிப்பிடப்பட்ட குறைந்தபட்ச attendance சதவீதத்தை மாணவர்கள் பராமரிக்க வேண்டும்.", "tanglish": "College regulations-la sollirukkura minimum attendance percentage maintain pannanum.", "hi": "छात्रों को कॉलेज के नियमों में निर्धारित न्यूनतम attendance percentage बनाए रखना चाहिए."},
    6: {"ta": "கல்லூரி வேலை நேரத்தில் உங்கள் Department Office அல்லது சம்பந்தப்பட்ட faculty member-ஐ தொடர்பு கொள்ளலாம்.", "tanglish": "College working hours-la unga Department Office illa concerned faculty member-a contact pannalam.", "hi": "कॉलेज के कार्य समय में अपने Department Office या संबंधित faculty member से संपर्क कर सकते हैं."},
    7: {"ta": "Semester exams கல்லூரி வெளியிடும் academic calendar-ன் படி நடத்தப்படும்.", "tanglish": "Semester exams college release panra academic calendar padi conduct pannuvanga.", "hi": "Semester examinations कॉलेज द्वारा जारी academic calendar के अनुसार आयोजित की जाती हैं."},
    8: {"ta": "Exam timetable பொதுவாக Examination Cell மூலம் கல்லூரியின் அதிகாரப்பூர்வ communication channels-ல் வெளியிடப்படும்.", "tanglish": "Exam timetable usually Examination Cell moolama official college communication channels-la publish pannuvanga.", "hi": "Exam timetable आमतौर पर Examination Cell द्वारा कॉलेज के official communication channels पर प्रकाशित किया जाता है."},
    9: {"ta": "Exam-க்கு valid hall ticket மற்றும் examination instructions-ல் அனுமதிக்கப்பட்ட பொருட்களை கொண்டு செல்ல வேண்டும்.", "tanglish": "Exam-ku valid hall ticket and examination instructions-la allowed items kondu ponga.", "hi": "परीक्षा के लिए valid hall ticket और examination instructions में अनुमत वस्तुएँ साथ ले जाएँ."},
    10: {"ta": "College வழங்கும் payment methods மூலம் fees செலுத்தலாம். தற்போதைய payment details-க்கு Accounts Office-ஐ தொடர்பு கொள்ளுங்கள்.", "tanglish": "College provide panra payment methods-la fees pay pannalam. Current details-ku Accounts Office-a contact pannunga.", "hi": "कॉलेज द्वारा दिए गए payment methods से fees का भुगतान किया जा सकता है। वर्तमान जानकारी के लिए Accounts Office से संपर्क करें."},
    11: {"ta": "Online fee payment கல்லூரியின் designated payment portal மூலம் கிடைக்கலாம்.", "tanglish": "Online fee payment college designated payment portal moolama available-a irukkalam.", "hi": "Online fee payment कॉलेज के designated payment portal के माध्यम से उपलब्ध हो सकता है."},
    12: {"ta": "Latest fee structure-ஐ College Accounts அல்லது Admission Office-ல் பெறலாம்.", "tanglish": "Latest fee structure-a College Accounts illa Admission Office-la get pannalam.", "hi": "Latest fee structure College Accounts या Admission Office से प्राप्त कर सकते हैं."},
    13: {"ta": "College hostel-ல் accommodation மற்றும் அடிப்படை மாணவர் வசதிகள் உள்ளன. Current availability-க்கு Hostel Office-ஐ தொடர்பு கொள்ளுங்கள்.", "tanglish": "College hostel-la accommodation and basic student facilities irukku. Current availability-ku Hostel Office-a contact pannunga.", "hi": "College hostel में accommodation और basic student facilities उपलब्ध हैं। वर्तमान availability के लिए Hostel Office से संपर्क करें."},
    14: {"ta": "College hostel admission procedure-ன் படி Hostel Office மூலம் accommodation-க்கு apply செய்யலாம்.", "tanglish": "College hostel admission procedure padi Hostel Office moolama accommodation-ku apply pannalam.", "hi": "College hostel admission procedure के अनुसार Hostel Office के माध्यम से accommodation के लिए आवेदन कर सकते हैं."},
    15: {"ta": "Hostel entry மற்றும் exit timings, hostel administration அமைக்கும் விதிமுறைகளின் அடிப்படையில் இருக்கும்.", "tanglish": "Hostel entry and exit timings hostel administration set panra rules padi irukkum.", "hi": "Hostel entry और exit timings hostel administration द्वारा निर्धारित rules के अनुसार होते हैं."},
    16: {"ta": "Library working days-ல் காலை 8:30 மணி முதல் மாலை 5:30 மணி வரை திறந்திருக்கும்.", "tanglish": "Library working days-la morning 8:30 AM to evening 5:30 PM open-a irukkum.", "hi": "Library working days में सुबह 8:30 बजे से शाम 5:30 बजे तक खुली रहती है."},
    17: {"ta": "Borrow செய்யக்கூடிய புத்தகங்களின் எண்ணிக்கை library rules மற்றும் student category-ஐ பொறுத்தது.", "tanglish": "Borrow panna mudiyura books count library rules and student category-ku depend aagum.", "hi": "Borrow किए जा सकने वाले books की संख्या library rules और student category पर निर्भर करती है."},
    18: {"ta": "தேவையான registration procedure-ஐ பின்பற்றி College Library மூலம் library membership பெறலாம்.", "tanglish": "Required registration procedure follow panni College Library moolama library membership get pannalam.", "hi": "Required registration procedure का पालन करके College Library से library membership प्राप्त कर सकते हैं."},
    19: {"ta": "Placement தொடர்பான தகவல்களை Placement Cell வழங்கும். Current opportunities-க்கு Placement Office-ஐ தொடர்பு கொள்ளுங்கள்.", "tanglish": "Placement related information Placement Cell provide pannum. Current opportunities-ku Placement Office-a contact pannunga.", "hi": "Placement से संबंधित जानकारी Placement Cell द्वारा दी जाती है। वर्तमान opportunities के लिए Placement Office से संपर्क करें."},
    20: {"ta": "Campus-க்கு வரும் companies ஒவ்வொரு ஆண்டும் placement opportunities மற்றும் recruitment requirements அடிப்படையில் மாறும்.", "tanglish": "Campus-ku varra companies each year placement opportunities and recruitment requirements padi change aagum.", "hi": "Campus पर आने वाली companies हर वर्ष placement opportunities और recruitment requirements के अनुसार बदलती हैं."},
    21: {"ta": "College வழங்கும் instructions-ன் படி Placement Cell மூலம் placement activities-க்கு register செய்யலாம்.", "tanglish": "College instructions padi Placement Cell moolama placement activities-ku register pannalam.", "hi": "College द्वारा दिए गए instructions के अनुसार Placement Cell के माध्यम से placement activities के लिए register कर सकते हैं."},
    22: {"ta": "தேர்ந்தெடுக்கப்பட்ட routes-ல் college transport facilities இருக்கலாம். Current route மற்றும் timing details-க்கு Transport Office-ஐ தொடர்பு கொள்ளுங்கள்.", "tanglish": "Selected routes-la college transport facilities irukkalam. Current route and timing details-ku Transport Office-a contact pannunga.", "hi": "चयनित routes पर college transport facilities उपलब्ध हो सकती हैं। वर्तमान route और timing के लिए Transport Office से संपर्क करें."},
    23: {"ta": "Current bus routes மற்றும் timings-ஐ College Transport Office-ல் பெறலாம்.", "tanglish": "Current bus routes and timings-a College Transport Office-la get pannalam.", "hi": "Current bus routes और timings College Transport Office से प्राप्त कर सकते हैं."},
    24: {"ta": "Available routes-ன் அடிப்படையில் Transport Office மூலம் college transportation-க்கு register செய்யலாம்.", "tanglish": "Available routes base panni Transport Office moolama college transportation-ku register pannalam.", "hi": "Available routes के आधार पर Transport Office के माध्यम से college transportation के लिए register कर सकते हैं."},
    25: {"ta": "Official working hours-ல் College Office-ஐ தொடர்பு கொண்டு உதவி பெறலாம்.", "tanglish": "Official working hours-la College Office-a contact panni assistance get pannalam.", "hi": "Official working hours में College Office से संपर्क करके सहायता प्राप्त कर सकते हैं."},
    26: {"ta": "General college office working hours காலை 9:00 மணி முதல் மாலை 4:30 மணி வரை.", "tanglish": "General college office working hours morning 9:00 AM to evening 4:30 PM.", "hi": "General college office working hours सुबह 9:00 बजे से शाम 4:30 बजे तक हैं."}
}


SUPPORTED_LANGUAGES = {"en", "ta", "tanglish", "hi", "kn", "ur", "gu", "te", "mr", "bn", "auto"}
TRANSLATABLE_LANGUAGES = {"kn", "ur", "gu", "te", "mr", "bn"}
TRANSLATION_TARGETS = {"kn": "kn", "ur": "ur", "gu": "gu", "te": "te", "mr": "mr", "bn": "bn"}

@lru_cache(maxsize=512)
def translate_text(text, target, source="auto"):
    if not text or target in {"en", "tanglish"}:
        return text
    if GoogleTranslator is None:
        return text
    try:
        return GoogleTranslator(source=source, target=TRANSLATION_TARGETS.get(target, target)).translate(text) or text
    except Exception:
        return text

def to_english_for_search(text, language):
    if language in TRANSLATABLE_LANGUAGES:
        return translate_text(text, language, source="auto") if False else translate_text(text, "en", source=language)
    return normalize_multilingual(text)

def detect_language(text):
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta"
    if re.search(r"[\u0C80-\u0CFF]", text):
        return "kn"
    if re.search(r"[\u0C00-\u0C7F]", text):
        return "te"
    if re.search(r"[\u0A80-\u0AFF]", text):
        return "gu"
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn"
    # Devanagari covers Hindi and Marathi; auto mode uses Hindi as the default.
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    if re.search(r"[\u0600-\u06FF]", text):
        return "ur"
    lower = text.lower()
    tanglish_words = ["epdi", "eppo", "evlo", "enga", "enna", "venum", "pannu", "panrathu", "iruka", "bro", "ah", "la", "ku", "illa"]
    if sum(1 for word in tanglish_words if re.search(rf"\b{re.escape(word)}\b", lower)) >= 1:
        return "tanglish"
    return "en"

def get_friendly_response(message, language="auto"):
    lang = detect_language(message) if language == "auto" else language
    text = message.lower().strip()

    greetings = ["hi", "hello", "hey", "hii", "hiii", "hey bro", "hi bro", "hello bro", "good morning", "good afternoon", "good evening", "vanakkam", "வணக்கம்", "नमस्ते", "हैलो"]
    if text in greetings:
        return random.choice(friendly_messages[lang]["greeting"]), lang

    if ("how are you" in text or "how r u" in text or "how are u" in text or
        "epdi iruka" in text or "epdi iruk" in text or "எப்படி இருக்க" in text):
        return random.choice(friendly_messages[lang]["how_are_you"]), lang

    if any(word in text for word in ["thanks", "thank you", "thankyou", "tq", "ty", "nandri", "நன்றி", "धन्यवाद"]):
        return random.choice(friendly_messages[lang]["thanks"]), lang

    if any(word in text for word in ["bye", "goodbye", "see you", "see ya", "பை", "अलविदा"]):
        return random.choice(friendly_messages[lang]["bye"]), lang

    if any(word in text for word in ["bored", "boring", "bore", "boring ah"]):
        return random.choice(friendly_messages[lang]["bored"]), lang

    if any(word in text for word in ["confused", "confusion", "don't understand", "not understand", "puriyala", "புரியல", "समझ नहीं"]):
        return random.choice(friendly_messages[lang]["confused"]), lang

    return None, lang


def answer_for_language(faq, language):
    if language == "en":
        return faq["answer"]
    manual = FAQ_TRANSLATIONS.get(faq["id"], {}).get(language)
    if manual:
        return manual
    if language in TRANSLATABLE_LANGUAGES:
        return translate_text(faq["answer"], language, source="en")
    return faq["answer"]


def translate_question_label(question, language):
    # Keep suggestions readable without needing an online translation service.
    translations = {
        "What is the library timing?": {"ta": "Library timing என்ன?", "tanglish": "Library timing enna?", "hi": "Library ka timing kya hai?"},
        "How can I apply for admission?": {"ta": "Admission-க்கு எப்படி apply செய்வது?", "tanglish": "Admission-ku epdi apply panrathu?", "hi": "Admission के लिए कैसे apply करें?"},
        "How can I get placement information?": {"ta": "Placement information எப்படி கிடைக்கும்?", "tanglish": "Placement information epdi kidaikkum?", "hi": "Placement information कैसे मिलेगी?"},
        "What are the college timings?": {"ta": "College timing என்ன?", "tanglish": "College timing enna?", "hi": "College timing kya hai?"},
        "When are semester exams conducted?": {"ta": "Semester exams எப்போது நடக்கும்?", "tanglish": "Semester exams eppo nadakkum?", "hi": "Semester exams कब होते हैं?"},
        "How can I pay my college fees?": {"ta": "College fees எப்படி pay செய்வது?", "tanglish": "College fees epdi pay panrathu?", "hi": "College fees कैसे pay करें?"},
        "What hostel facilities are available?": {"ta": "Hostel-ல் என்ன facilities இருக்கு?", "tanglish": "Hostel-la enna facilities irukku?", "hi": "Hostel में कौन-कौन सी facilities हैं?"},
        "How can I contact the college?": {"ta": "College-ஐ எப்படி contact செய்வது?", "tanglish": "College-a epdi contact panrathu?", "hi": "College से कैसे contact करें?"}
    }
    manual = translations.get(question, {}).get(language)
    if manual:
        return manual
    if language in TRANSLATABLE_LANGUAGES:
        return translate_text(question, language, source="en")
    return question

# ==========================================
# Save JSON Data
# ==========================================
def save_to_json(filename, data):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
    existing_data.append(data)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, indent=4, ensure_ascii=False)

# ==========================================
# Home
# ==========================================
@app.route("/")
def home():
    categories = sorted(set(faq["category"] for faq in faqs))
    return render_template("index.html", categories=categories)

# ==========================================
# Chatbot
# ==========================================
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    user_question = str(data.get("question", "")).strip()
    requested_language = str(data.get("language", "auto")).lower()
    if requested_language not in SUPPORTED_LANGUAGES:
        requested_language = "auto"

    if not user_question:
        lang = "en" if requested_language == "auto" else requested_language
        empty = {
            "en": "Hey bro 😊 Type something and I'll help you!",
            "ta": "ஹே bro 😊 ஏதாவது type பண்ணுங்க, நான் help பண்றேன்!",
            "tanglish": "Hey bro 😊 Edhavadhu type pannu, naan help panren!",
            "hi": "हे bro 😊 कुछ भी type कीजिए, मैं मदद करूँगा!",
            "kn": "ಹೇ bro 😊 ಏನಾದರೂ type ಮಾಡಿ, ನಾನು help ಮಾಡುತ್ತೇನೆ!",
            "ur": "ارے bro 😊 کچھ بھی type کریں، میں مدد کرتا ہوں!",
            "gu": "હે bro 😊 કંઈપણ type કરો, હું help કરીશ!",
            "te": "హే bro 😊 ఏదైనా type చేయండి, నేను help చేస్తాను!",
            "mr": "हे bro 😊 काहीही type करा, मी मदत करतो!",
            "bn": "হে bro 😊 কিছু type করুন, আমি সাহায্য করব!"
        }
        return jsonify({"answer": empty[lang], "category": "General", "confidence": 0, "suggestions": [], "language": lang})

    friendly_response, detected_lang = get_friendly_response(user_question, requested_language)
    language = detected_lang
    if friendly_response:
        suggestions = ["What is the library timing?", "How can I apply for admission?", "How can I get placement information?"]
        suggestions = [translate_question_label(q, language) for q in suggestions]
        return jsonify({"answer": friendly_response, "category": "Friendly Chat", "confidence": 100, "suggestions": suggestions, "language": language})

    # Convert supported regional languages to English for the shared TF-IDF model.
    if language in TRANSLATABLE_LANGUAGES:
        searchable_question = translate_text(user_question, language, source="auto")
        if searchable_question == user_question:
            searchable_question = normalize_multilingual(user_question)
    else:
        searchable_question = normalize_multilingual(user_question)
    user_vector = vectorizer.transform([searchable_question])
    similarities = cosine_similarity(user_vector, faq_vectors)[0]
    best_index = similarities.argmax()
    best_score = float(similarities[best_index])
    best_faq = faqs[best_index]
    threshold = 0.12

    if best_score >= threshold:
        suggestions = [faq["question"] for faq in faqs if faq["category"] == best_faq["category"] and faq["id"] != best_faq["id"]][:3]
        suggestions = [translate_question_label(q, language) for q in suggestions]
        return jsonify({
            "answer": answer_for_language(best_faq, language),
            "category": best_faq["category"],
            "confidence": round(best_score * 100, 2),
            "suggestions": suggestions,
            "language": language
        })

    fallback = {
        "en": "Hmm 🤔 I'm not sure about that one, bro. I'm still learning! 😄 Try asking about admission, academics, exams, fees, hostel, library, placement, or transport.",
        "ta": "Hmm 🤔 அந்த கேள்விக்கு இன்னும் answer தெரியல bro. நான் இன்னும் learn பண்ணிட்டு இருக்கேன்! 😄 Admission, academics, exams, fees, hostel, library, placement அல்லது transport பற்றி கேளுங்க.",
        "tanglish": "Hmm 🤔 Andha question-ku innum answer theriyala bro. Naan innum learn pannitu iruken! 😄 Admission, academics, exams, fees, hostel, library, placement illa transport pathi kelu.",
        "hi": "Hmm 🤔 उस सवाल का जवाब अभी मेरे पास नहीं है bro. मैं अभी सीख रहा हूँ! 😄 Admission, academics, exams, fees, hostel, library, placement या transport के बारे में पूछिए.",
        "kn": "Hmm 🤔 ಆ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರ ಇನ್ನೂ ನನ್ನ ಬಳಿ ಇಲ್ಲ bro. ನಾನು ಇನ್ನೂ ಕಲಿಯುತ್ತಿದ್ದೇನೆ! 😄 Admission, academics, exams, fees, hostel, library, placement ಅಥವಾ transport ಬಗ್ಗೆ ಕೇಳಿ.",
        "ur": "Hmm 🤔 اس سوال کا جواب ابھی میرے پاس نہیں ہے bro. میں ابھی سیکھ رہا ہوں! 😄 Admission, academics, exams, fees, hostel, library, placement یا transport کے بارے میں پوچھیں.",
        "gu": "Hmm 🤔 આ પ્રશ્નનો જવાબ હજી મારી પાસે નથી bro. હું હજી શીખી રહ્યો છું! 😄 Admission, academics, exams, fees, hostel, library, placement અથવા transport વિશે પૂછો.",
        "te": "Hmm 🤔 ఆ ప్రశ్నకు సమాధానం ఇంకా నా దగ్గర లేదు bro. నేను ఇంకా నేర్చుకుంటున్నాను! 😄 Admission, academics, exams, fees, hostel, library, placement లేదా transport గురించి అడగండి.",
        "mr": "Hmm 🤔 त्या प्रश्नाचे उत्तर अजून माझ्याकडे नाही bro. मी अजून शिकत आहे! 😄 Admission, academics, exams, fees, hostel, library, placement किंवा transport बद्दल विचारा.",
        "bn": "Hmm 🤔 এই প্রশ্নের উত্তর এখনও আমার কাছে নেই bro. আমি এখনও শিখছি! 😄 Admission, academics, exams, fees, hostel, library, placement বা transport সম্পর্কে জিজ্ঞেস করুন."
    }
    suggestions = ["How can I apply for admission?", "What is the library timing?", "How can I get placement information?"]
    suggestions = [translate_question_label(q, language) for q in suggestions]
    return jsonify({"answer": fallback[language], "category": "Unknown", "confidence": round(best_score * 100, 2), "suggestions": suggestions, "language": language})

# ==========================================
# Feedback
# ==========================================
@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    feedback_data = {
        "question": data.get("question", ""),
        "answer": data.get("answer", ""),
        "feedback": data.get("feedback", ""),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_to_json("feedback.json", feedback_data)
    return jsonify({"message": "Thank you for your feedback! ❤️"})

# ==========================================
# Unanswered Questions
# ==========================================
@app.route("/unanswered", methods=["POST"])
def unanswered():
    data = request.get_json(silent=True) or {}
    question_data = {"question": data.get("question", ""), "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    save_to_json("unanswered.json", question_data)
    return jsonify({"message": "Got it bro! 👍 I've recorded your question."})

if __name__ == "__main__":
    app.run(debug=True)
