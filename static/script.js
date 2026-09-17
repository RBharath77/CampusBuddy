/* ============================================================
   CampusBuddy — frontend logic
   Backend contract is unchanged: /ask, /feedback, /unanswered
   ============================================================ */

const app      = document.getElementById("app");
const input    = document.getElementById("question");
const sendBtn  = document.getElementById("send");
const chatBox  = document.getElementById("chat-box");
const thread   = document.getElementById("thread");
const jumpBtn  = document.getElementById("jump");
const themeBtn = document.getElementById("theme-toggle");
const languageSelect = document.getElementById("language-select");
const languageHint = document.getElementById("language-hint");

let lastQuestion = "";
let selectedLanguage = localStorage.getItem("campusbuddy-language") || "auto";

if (languageSelect) languageSelect.value = selectedLanguage;
let pinnedToBottom = true;

/* ---------------------------------------------- helpers ---- */

function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
}

function icon(id, size = 16) {
    return `<svg class="ic ic-${size}"><use href="#${id}"></use></svg>`;
}

function timeNow() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function startChat() {
    app.classList.add("chatting");
}

function scrollToBottom() {
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
    pinnedToBottom = true;
    jumpBtn.classList.remove("show");
}

function maybeScroll() {
    if (pinnedToBottom) scrollToBottom();
    else jumpBtn.classList.add("show");
}

chatBox.addEventListener("scroll", () => {
    const gap = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;
    pinnedToBottom = gap < 60;
    if (pinnedToBottom) jumpBtn.classList.remove("show");
});

/* Hide the avatar when the previous message came from the same side. */
function applyGrouping(node, role) {
    const prev = thread.lastElementChild;
    if (prev && prev.classList.contains(role) && prev.id !== "typing") {
        node.classList.add("grouped");
    }
}

/* ---------------------------------------------- language UI ---- */
const CATEGORY_QUESTIONS = {
    Admission: "How can I apply for admission?",
    Academics: "What are the college timings?",
    Exams: "When are semester exams conducted?",
    Fees: "How can I pay my college fees?",
    Hostel: "What hostel facilities are available?",
    Library: "What is the library timing?",
    Placement: "How can I get placement information?",
    Transport: "Does the college provide bus facilities?",
    General: "How can I contact the college?"
};


const UI_TEXT = {
    en: {
        status: "Online · College assistant",
        clear: "Clear",
        introTitle: "Ask anything about your college.",
        introDescription: "Timings, fees, hostel, exams, placements — answers in one line, no office visits.",
        topic: "Start with a topic",
        latest: "Latest message",
        placeholder: "Ask your college question…",
        related: "Related questions",
        noMatch: "No match in the FAQ yet. Send this question to the college office and it gets added.",
        sendQuestion: "Send this question",
        sent: "Sent. This question will be answered in a future update.",
        helpful: "Helpful",
        notHelpful: "Not helpful",
        copy: "Copy answer",
        copied: "Copied",
        thanks: "Thanks — noted.",
        greeting: "Hi — I'm CampusBuddy. Pick a topic or type your question.",
        error: "Can't reach the server right now. Check that the Flask app is running, then send the question again.",
        hint: "🇬🇧 English mode · Press Enter to send",
        themeLight: "Switch to light theme",
        themeDark: "Switch to dark theme"
    },
    ta: {
        status: "Online · கல்லூரி உதவியாளர்",
        clear: "அழி",
        introTitle: "உங்கள் கல்லூரி பற்றி எதையும் கேளுங்கள்.",
        introDescription: "Timing, fees, hostel, exams, placements — எல்லா பதிலும் ஒரே இடத்தில்.",
        topic: "ஒரு தலைப்பை தேர்வு செய்யுங்கள்",
        latest: "சமீபத்திய செய்தி",
        placeholder: "உங்கள் கல்லூரி கேள்வியை கேளுங்கள்…",
        related: "தொடர்புடைய கேள்விகள்",
        noMatch: "இந்த கேள்வி FAQ-ல் இன்னும் இல்லை. இந்த கேள்வியை College Office-க்கு அனுப்பலாம்.",
        sendQuestion: "இந்த கேள்வியை அனுப்பு",
        sent: "அனுப்பப்பட்டது. இந்த கேள்வி அடுத்த update-ல் சேர்க்கப்படும்.",
        helpful: "பயனுள்ளதாக உள்ளது",
        notHelpful: "பயனுள்ளதாக இல்லை",
        copy: "பதிலை நகலெடு",
        copied: "நகலெடுக்கப்பட்டது",
        thanks: "நன்றி — பதிவு செய்துவிட்டோம்.",
        greeting: "வணக்கம்! நான் CampusBuddy. ஒரு topic தேர்வு செய்யுங்கள் அல்லது கேள்வியை type செய்யுங்கள்.",
        error: "இப்போது server-ஐ connect செய்ய முடியவில்லை. Flask app running-ஆ இருக்கிறதா என்று check செய்து மீண்டும் கேளுங்கள்.",
        hint: "🇮🇳 தமிழ் mode · Enter அழுத்தி அனுப்பலாம்",
        themeLight: "Light theme-க்கு மாற்று",
        themeDark: "Dark theme-க்கு மாற்று"
    },
    tanglish: {
        status: "Online · College assistant",
        clear: "Clear",
        introTitle: "Unga college pathi edhu venalum kelu.",
        introDescription: "Timing, fees, hostel, exams, placements — answers ellam ore place-la.",
        topic: "Oru topic select pannunga",
        latest: "Latest message",
        placeholder: "Unga college question-a kelu…",
        related: "Related questions",
        noMatch: "Indha question FAQ-la innum illa. College Office-ku indha question-a send pannalam.",
        sendQuestion: "Indha question-a send pannu",
        sent: "Sent. Indha question future update-la answer aagum.",
        helpful: "Helpful",
        notHelpful: "Not helpful",
        copy: "Copy answer",
        copied: "Copied",
        thanks: "Thanks bro — noted.",
        greeting: "Hi bro! 👋 Naan CampusBuddy. Oru topic select pannu illa un question-a kelu.",
        error: "Ippo server-a reach panna mudiyala. Flask app running-la irukka nu check panni question-a again kelu.",
        hint: "🗣️ Tanglish mode · Enter press panni send pannunga",
        themeLight: "Light theme-ku maathu",
        themeDark: "Dark theme-ku maathu"
    },
    hi: {
        status: "Online · कॉलेज सहायक",
        clear: "साफ़ करें",
        introTitle: "अपने कॉलेज के बारे में कुछ भी पूछें।",
        introDescription: "Timing, fees, hostel, exams, placements — सभी जवाब एक ही जगह।",
        topic: "एक विषय चुनें",
        latest: "नवीनतम संदेश",
        placeholder: "अपने कॉलेज का सवाल पूछें…",
        related: "संबंधित सवाल",
        noMatch: "यह सवाल अभी FAQ में नहीं है। इसे College Office को भेज सकते हैं।",
        sendQuestion: "यह सवाल भेजें",
        sent: "भेज दिया गया। यह सवाल अगले update में जोड़ा जाएगा।",
        helpful: "उपयोगी",
        notHelpful: "उपयोगी नहीं",
        copy: "जवाब कॉपी करें",
        copied: "कॉपी हो गया",
        thanks: "धन्यवाद — नोट कर लिया गया।",
        greeting: "नमस्ते! मैं CampusBuddy हूँ। कोई विषय चुनें या अपना सवाल पूछें।",
        error: "अभी server से connect नहीं हो पा रहा है। Flask app running है या नहीं check करके फिर पूछें।",
        hint: "🇮🇳 हिन्दी mode · Enter दबाकर भेजें",
        themeLight: "Light theme पर जाएँ",
        themeDark: "Dark theme पर जाएँ"
    },
    kn: { status:"Online · ಕಾಲೇಜು ಸಹಾಯಕ", clear:"ಅಳಿಸಿ", introTitle:"ನಿಮ್ಮ ಕಾಲೇಜಿನ ಬಗ್ಗೆ ಏನಾದರೂ ಕೇಳಿ.", introDescription:"Timing, fees, hostel, exams, placements — ಎಲ್ಲಾ ಮಾಹಿತಿ ಒಂದೇ ಸ್ಥಳದಲ್ಲಿ.", topic:"ಒಂದು ವಿಷಯ ಆಯ್ಕೆ ಮಾಡಿ", latest:"ಇತ್ತೀಚಿನ ಸಂದೇಶ", placeholder:"ನಿಮ್ಮ ಕಾಲೇಜಿನ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ…", related:"ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಗಳು", noMatch:"ಈ ಪ್ರಶ್ನೆ FAQ ನಲ್ಲಿ ಇನ್ನೂ ಇಲ್ಲ. ಇದನ್ನು College Office ಗೆ ಕಳುಹಿಸಬಹುದು.", sendQuestion:"ಈ ಪ್ರಶ್ನೆಯನ್ನು ಕಳುಹಿಸಿ", sent:"ಕಳುಹಿಸಲಾಗಿದೆ. ಮುಂದಿನ update ನಲ್ಲಿ ಈ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಲಾಗುತ್ತದೆ.", helpful:"ಉಪಯುಕ್ತ", notHelpful:"ಉಪಯುಕ್ತವಲ್ಲ", copy:"ಉತ್ತರವನ್ನು copy ಮಾಡಿ", copied:"Copy ಆಯಿತು", thanks:"ಧನ್ಯವಾದಗಳು — ದಾಖಲಿಸಲಾಗಿದೆ.", greeting:"ನಮಸ್ಕಾರ! ನಾನು CampusBuddy. ಒಂದು topic ಆಯ್ಕೆ ಮಾಡಿ ಅಥವಾ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ.", error:"ಈಗ server connect ಆಗುತ್ತಿಲ್ಲ. Flask app running ಇದೆಯೇ ಎಂದು check ಮಾಡಿ.", hint:"🇮🇳 ಕನ್ನಡ mode · Enter ಒತ್ತಿ ಕಳುಹಿಸಿ", themeLight:"Light theme ಗೆ ಬದಲಿಸಿ", themeDark:"Dark theme ಗೆ ಬದಲಿಸಿ" },
    ur: { status:"Online · کالج اسسٹنٹ", clear:"صاف کریں", introTitle:"اپنے کالج کے بارے میں کچھ بھی پوچھیں۔", introDescription:"Timings, fees, hostel, exams, placements — تمام معلومات ایک جگہ۔", topic:"ایک موضوع منتخب کریں", latest:"تازہ ترین پیغام", placeholder:"اپنے کالج کا سوال پوچھیں…", related:"متعلقہ سوالات", noMatch:"یہ سوال ابھی FAQ میں نہیں ہے۔ اسے College Office کو بھیج سکتے ہیں۔", sendQuestion:"یہ سوال بھیجیں", sent:"بھیج دیا گیا۔ یہ سوال اگلے update میں شامل ہوگا۔", helpful:"مفید", notHelpful:"مفید نہیں", copy:"جواب copy کریں", copied:"Copy ہو گیا", thanks:"شکریہ — نوٹ کر لیا گیا۔", greeting:"السلام علیکم! میں CampusBuddy ہوں۔ کوئی topic منتخب کریں یا اپنا سوال پوچھیں۔", error:"ابھی server سے connect نہیں ہو پا رہا۔ Flask app check کریں۔", hint:"🇵🇰 اردو mode · Enter دباکر بھیجیں", themeLight:"Light theme پر جائیں", themeDark:"Dark theme پر جائیں" },
    gu: { status:"Online · કોલેજ સહાયક", clear:"સાફ કરો", introTitle:"તમારી કોલેજ વિશે કંઈપણ પૂછો.", introDescription:"Timing, fees, hostel, exams, placements — બધી માહિતી એક જ જગ્યાએ.", topic:"એક વિષય પસંદ કરો", latest:"છેલ્લો સંદેશ", placeholder:"તમારો કોલેજ પ્રશ્ન પૂછો…", related:"સંબંધિત પ્રશ્નો", noMatch:"આ પ્રશ્ન હજુ FAQ માં નથી. તેને College Office ને મોકલી શકો છો.", sendQuestion:"આ પ્રશ્ન મોકલો", sent:"મોકલ્યો. આગામી update માં જવાબ ઉમેરવામાં આવશે.", helpful:"ઉપયોગી", notHelpful:"ઉપયોગી નથી", copy:"જવાબ copy કરો", copied:"Copy થઈ ગયું", thanks:"આભાર — નોંધ્યું.", greeting:"નમસ્તે! હું CampusBuddy છું. Topic પસંદ કરો અથવા પ્રશ્ન પૂછો.", error:"હમણાં server connect થઈ રહ્યું નથી. Flask app check કરો.", hint:"🇮🇳 ગુજરાતી mode · Enter દબાવીને મોકલો", themeLight:"Light theme પર જાઓ", themeDark:"Dark theme પર જાઓ" },
    te: { status:"Online · కళాశాల సహాయకుడు", clear:"క్లియర్", introTitle:"మీ కాలేజీ గురించి ఏదైనా అడగండి.", introDescription:"Timings, fees, hostel, exams, placements — మొత్తం సమాచారం ఒకే చోట.", topic:"ఒక topic ఎంచుకోండి", latest:"తాజా సందేశం", placeholder:"మీ కాలేజీ ప్రశ్నను అడగండి…", related:"సంబంధిత ప్రశ్నలు", noMatch:"ఈ ప్రశ్న ఇంకా FAQలో లేదు. దీన్ని College Officeకి పంపవచ్చు.", sendQuestion:"ఈ ప్రశ్నను పంపండి", sent:"పంపబడింది. తదుపరి updateలో ఈ ప్రశ్నకు సమాధానం వస్తుంది.", helpful:"ఉపయోగకరం", notHelpful:"ఉపయోగకరం కాదు", copy:"సమాధానం copy చేయండి", copied:"Copy అయింది", thanks:"ధన్యవాదాలు — నమోదు చేశాం.", greeting:"నమస్కారం! నేను CampusBuddy. Topic ఎంచుకోండి లేదా మీ ప్రశ్న అడగండి.", error:"ఇప్పుడు server connect కావడం లేదు. Flask app running ఉందో check చేయండి.", hint:"🇮🇳 తెలుగు mode · Enter నొక్కి పంపండి", themeLight:"Light themeకి మార్చండి", themeDark:"Dark themeకి మార్చండి" },
    mr: { status:"Online · कॉलेज सहाय्यक", clear:"साफ करा", introTitle:"तुमच्या कॉलेजविषयी काहीही विचारा.", introDescription:"Timing, fees, hostel, exams, placements — सर्व माहिती एका ठिकाणी.", topic:"एक विषय निवडा", latest:"नवीनतम संदेश", placeholder:"तुमचा कॉलेज प्रश्न विचारा…", related:"संबंधित प्रश्न", noMatch:"हा प्रश्न अजून FAQ मध्ये नाही. तो College Office ला पाठवू शकता.", sendQuestion:"हा प्रश्न पाठवा", sent:"पाठवला. पुढील update मध्ये या प्रश्नाचे उत्तर दिले जाईल.", helpful:"उपयुक्त", notHelpful:"उपयुक्त नाही", copy:"उत्तर copy करा", copied:"Copy झाले", thanks:"धन्यवाद — नोंद केली.", greeting:"नमस्कार! मी CampusBuddy आहे. Topic निवडा किंवा तुमचा प्रश्न विचारा.", error:"आत्ता server connect होत नाही. Flask app check करा.", hint:"🇮🇳 मराठी mode · Enter दाबून पाठवा", themeLight:"Light theme वर जा", themeDark:"Dark theme वर जा" },
    bn: { status:"Online · কলেজ সহায়ক", clear:"পরিষ্কার করুন", introTitle:"আপনার কলেজ সম্পর্কে যেকোনো কিছু জিজ্ঞেস করুন।", introDescription:"Timing, fees, hostel, exams, placements — সব তথ্য এক জায়গায়।", topic:"একটি বিষয় বেছে নিন", latest:"সর্বশেষ বার্তা", placeholder:"আপনার কলেজের প্রশ্ন করুন…", related:"সম্পর্কিত প্রশ্ন", noMatch:"এই প্রশ্নটি এখনও FAQ-তে নেই। এটি College Office-এ পাঠাতে পারেন।", sendQuestion:"এই প্রশ্নটি পাঠান", sent:"পাঠানো হয়েছে। পরবর্তী update-এ উত্তর যোগ হবে।", helpful:"সহায়ক", notHelpful:"সহায়ক নয়", copy:"উত্তর copy করুন", copied:"Copy হয়েছে", thanks:"ধন্যবাদ — নোট করা হয়েছে।", greeting:"নমস্কার! আমি CampusBuddy। একটি topic বেছে নিন বা আপনার প্রশ্ন করুন।", error:"এখন server connect হচ্ছে না। Flask app running আছে কি না check করুন।", hint:"🇮🇳 বাংলা mode · Enter চাপুন", themeLight:"Light theme-এ যান", themeDark:"Dark theme-এ যান" }
};

const CATEGORY_LABELS = {
    en: { Admission:"Admission", Academics:"Academics", Exams:"Exams", Fees:"Fees", General:"General", Hostel:"Hostel", Library:"Library", Placement:"Placement", Transport:"Transport" },
    ta: { Admission:"சேர்க்கை", Academics:"படிப்பு", Exams:"தேர்வுகள்", Fees:"கட்டணம்", General:"பொது", Hostel:"ஹாஸ்டல்", Library:"நூலகம்", Placement:"வேலைவாய்ப்பு", Transport:"போக்குவரத்து" },
    tanglish: { Admission:"Admission", Academics:"Academics", Exams:"Exams", Fees:"Fees", General:"General", Hostel:"Hostel", Library:"Library", Placement:"Placement", Transport:"Transport" },
    hi: { Admission:"प्रवेश", Academics:"पढ़ाई", Exams:"परीक्षा", Fees:"फीस", General:"सामान्य", Hostel:"हॉस्टल", Library:"लाइब्रेरी", Placement:"प्लेसमेंट", Transport:"परिवहन" },
    kn: { Admission:"ಪ್ರವೇಶ", Academics:"ಶಿಕ್ಷಣ", Exams:"ಪರೀಕ್ಷೆಗಳು", Fees:"ಶುಲ್ಕ", General:"ಸಾಮಾನ್ಯ", Hostel:"ಹಾಸ್ಟೆಲ್", Library:"ಗ್ರಂಥಾಲಯ", Placement:"ಪ್ಲೇಸ್‌ಮೆಂಟ್", Transport:"ಸಾರಿಗೆ" },
    ur: { Admission:"داخلہ", Academics:"تعلیم", Exams:"امتحانات", Fees:"فیس", General:"عام", Hostel:"ہاسٹل", Library:"کتب خانہ", Placement:"پلیسمنٹ", Transport:"ٹرانسپورٹ" },
    gu: { Admission:"પ્રવેશ", Academics:"અભ્યાસ", Exams:"પરીક્ષાઓ", Fees:"ફી", General:"સામાન્ય", Hostel:"હોસ્ટેલ", Library:"લાઇબ્રેરી", Placement:"પ્લેસમેન્ટ", Transport:"પરિવહન" },
    te: { Admission:"ప్రవేశం", Academics:"విద్య", Exams:"పరీక్షలు", Fees:"ఫీజు", General:"సాధారణ", Hostel:"హాస్టల్", Library:"లైబ్రరీ", Placement:"ప్లేస్‌మెంట్", Transport:"రవాణా" },
    mr: { Admission:"प्रवेश", Academics:"अभ्यास", Exams:"परीक्षा", Fees:"फी", General:"सामान्य", Hostel:"वसतिगृह", Library:"ग्रंथालय", Placement:"प्लेसमेंट", Transport:"वाहतूक" },
    bn: { Admission:"ভর্তি", Academics:"পড়াশোনা", Exams:"পরীক্ষা", Fees:"ফি", General:"সাধারণ", Hostel:"হোস্টেল", Library:"লাইব্রেরি", Placement:"প্লেসমেন্ট", Transport:"পরিবহন" }
};

const CATEGORY_QUESTIONS_LOCAL = {
    en: CATEGORY_QUESTIONS,
    ta: {
        Admission:"சேர்க்கைக்கு எப்படி விண்ணப்பிப்பது?",
        Academics:"கல்லூரி நேரம் என்ன?",
        Exams:"Semester exams எப்போது நடக்கும்?",
        Fees:"College fees எப்படி செலுத்துவது?",
        Hostel:"Hostel-ல் என்ன facilities இருக்கு?",
        Library:"Library timing என்ன?",
        Placement:"Placement information எப்படி கிடைக்கும்?",
        Transport:"College bus வசதி இருக்கா?",
        General:"College-ஐ எப்படி contact செய்வது?"
    },
    tanglish: {
        Admission:"Admission-ku epdi apply panrathu?",
        Academics:"College timing enna?",
        Exams:"Semester exams eppo nadakkum?",
        Fees:"College fees epdi pay panrathu?",
        Hostel:"Hostel-la enna facilities irukku?",
        Library:"Library timing enna?",
        Placement:"Placement information epdi kidaikkum?",
        Transport:"College bus facility irukka?",
        General:"College-a epdi contact panrathu?"
    },
    hi: {
        Admission:"Admission के लिए कैसे apply करें?", Academics:"College timing क्या है?", Exams:"Semester exams कब होते हैं?", Fees:"College fees कैसे pay करें?", Hostel:"Hostel में कौन-कौन सी facilities हैं?", Library:"Library का timing क्या है?", Placement:"Placement information कैसे मिलेगी?", Transport:"क्या college bus facility है?", General:"College से कैसे contact करें?"
    },
    kn: { Admission:"ಪ್ರವೇಶಕ್ಕೆ ಹೇಗೆ apply ಮಾಡುವುದು?", Academics:"College timing ಏನು?", Exams:"Semester exams ಯಾವಾಗ ನಡೆಯುತ್ತವೆ?", Fees:"College fees ಹೇಗೆ pay ಮಾಡುವುದು?", Hostel:"Hostel ನಲ್ಲಿ ಯಾವ facilities ಇವೆ?", Library:"Library timing ಏನು?", Placement:"Placement information ಹೇಗೆ ಸಿಗುತ್ತದೆ?", Transport:"College bus facility ಇದೆಯೇ?", General:"College ಅನ್ನು ಹೇಗೆ contact ಮಾಡುವುದು?" },
    ur: { Admission:"Admission کے لیے کیسے apply کریں؟", Academics:"College timing کیا ہے؟", Exams:"Semester exams کب ہوتے ہیں؟", Fees:"College fees کیسے pay کریں؟", Hostel:"Hostel میں کون سی facilities ہیں؟", Library:"Library کا timing کیا ہے؟", Placement:"Placement information کیسے ملے گی؟", Transport:"کیا college bus facility ہے؟", General:"College سے کیسے contact کریں؟" },
    gu: { Admission:"Admission માટે કેવી રીતે apply કરવું?", Academics:"College timing શું છે?", Exams:"Semester exams ક્યારે થાય છે?", Fees:"College fees કેવી રીતે pay કરવી?", Hostel:"Hostel માં કઈ facilities છે?", Library:"Library timing શું છે?", Placement:"Placement information કેવી રીતે મળશે?", Transport:"શું college bus facility છે?", General:"College ને કેવી રીતે contact કરવું?" },
    te: { Admission:"Admission కి ఎలా apply చేయాలి?", Academics:"College timing ఏమిటి?", Exams:"Semester exams ఎప్పుడు జరుగుతాయి?", Fees:"College fees ఎలా pay చేయాలి?", Hostel:"Hostel లో ఏ facilities ఉన్నాయి?", Library:"Library timing ఏమిటి?", Placement:"Placement information ఎలా వస్తుంది?", Transport:"College bus facility ఉందా?", General:"College ని ఎలా contact చేయాలి?" },
    mr: { Admission:"Admission साठी कसे apply करायचे?", Academics:"College timing काय आहे?", Exams:"Semester exams कधी होतात?", Fees:"College fees कशा pay करायच्या?", Hostel:"Hostel मध्ये कोणत्या facilities आहेत?", Library:"Library timing काय आहे?", Placement:"Placement information कशी मिळेल?", Transport:"College bus facility आहे का?", General:"College शी contact कसा करायचा?" },
    bn: { Admission:"Admission-এর জন্য কীভাবে apply করব?", Academics:"College timing কী?", Exams:"Semester exams কখন হয়?", Fees:"College fees কীভাবে pay করব?", Hostel:"Hostel-এ কী কী facilities আছে?", Library:"Library timing কী?", Placement:"Placement information কীভাবে পাব?", Transport:"College bus facility আছে কি?", General:"College-এর সঙ্গে কীভাবে contact করব?" }
};

function currentUILanguage() {
    return selectedLanguage === "auto" ? "en" : selectedLanguage;
}

function updateLanguageUI() {
    const lang = currentUILanguage();
    const t = UI_TEXT[lang] || UI_TEXT.en;

    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };

    setText("status-text", t.status);
    setText("clear-label", t.clear);
    setText("intro-title", t.introTitle);
    setText("intro-description", t.introDescription);
    setText("topic-label", t.topic);
    setText("latest-label", t.latest);
    input.placeholder = t.placeholder;
    languageHint.textContent = t.hint;

    document.querySelectorAll(".cat-grid button, .chip-bar button").forEach(btn => {
        const category = btn.getAttribute("data-category");
        if (category) btn.textContent = (CATEGORY_LABELS[lang] || CATEGORY_LABELS.en)[category] || category;
    });

    applyTheme(document.body.classList.contains("light"));
}

/* ---------------------------------------------- messages ---- */

function addUserMessage(message) {
    startChat();

    const node = document.createElement("div");
    node.className = "msg user";
    applyGrouping(node, "user");

    node.innerHTML = `
        <div class="body">
            <div class="bubble">${escapeHTML(message)}</div>
            <div class="foot"><span class="time">${timeNow()}</span></div>
        </div>`;

    thread.appendChild(node);
    pinnedToBottom = true;
    scrollToBottom();
}

function addBotResponse(data) {
    startChat();
    const lang = data.language || currentUILanguage();
    const t = UI_TEXT[lang] || UI_TEXT.en;
    const known = data.category && data.category !== "Unknown";

    let suggest = "";
    if (data.suggestions && data.suggestions.length) {
        suggest = `
            <div class="suggest">
                <p class="suggest-label">${escapeHTML(t.related)}</p>
                <div class="suggest-list">
                    ${data.suggestions.map(q =>
                        `<button type="button" onclick="askSuggestion(this)">${escapeHTML(q)}</button>`
                    ).join("")}
                </div>
            </div>`;
    }

    let unanswered = "";
    if (!known) {
        unanswered = `
            <div class="unanswered">
                <p>${escapeHTML(t.noMatch)}</p>
                <button type="button" onclick="saveUnanswered(this)">${escapeHTML(t.sendQuestion)}</button>
            </div>`;
    }

    const node = document.createElement("div");
    node.className = "msg bot";
    applyGrouping(node, "bot");

    node.innerHTML = `
        <div class="avatar">${icon("i-cap", 18)}</div>
        <div class="body">
            <div class="bubble">${escapeHTML(data.answer)}</div>
            ${suggest}
            ${unanswered}
            <div class="foot">
                <span class="time">${timeNow()}</span>
                <div class="actions">
                    <button type="button" class="act" title="${escapeHTML(t.helpful)}" aria-label="${escapeHTML(t.helpful)}" onclick="sendFeedback(this,'helpful')">${icon("i-up")}</button>
                    <button type="button" class="act" title="${escapeHTML(t.notHelpful)}" aria-label="${escapeHTML(t.notHelpful)}" onclick="sendFeedback(this,'not_helpful')">${icon("i-down")}</button>
                    <button type="button" class="act" title="${escapeHTML(t.copy)}" aria-label="${escapeHTML(t.copy)}" onclick="copyAnswer(this)">${icon("i-copy")}</button>
                </div>
            </div>
        </div>`;

    node.dataset.question = lastQuestion;
    node.dataset.answer = data.answer ?? "";

    thread.appendChild(node);
    maybeScroll();
}

function botGreeting() {
    const lang = currentUILanguage();
    const t = UI_TEXT[lang] || UI_TEXT.en;
    const node = document.createElement("div");
    node.className = "msg bot";
    node.innerHTML = `
        <div class="avatar">${icon("i-cap", 18)}</div>
        <div class="body">
            <div class="bubble">${escapeHTML(t.greeting)}</div>
            <div class="foot"><span class="time">${timeNow()}</span></div>
        </div>`;
    thread.appendChild(node);
}

/* ---------------------------------------------- typing ---- */

function showTyping() {
    if (document.getElementById("typing")) return;

    const node = document.createElement("div");
    node.id = "typing";
    node.className = "msg bot";
    node.innerHTML = `
        <div class="avatar">${icon("i-cap", 18)}</div>
        <div class="body"><div class="typing"><i></i><i></i><i></i></div></div>`;

    thread.appendChild(node);
    maybeScroll();
}

function removeTyping() {
    document.getElementById("typing")?.remove();
}

/* ---------------------------------------------- sending ---- */

async function sendQuestion() {
    const question = input.value.trim();
    if (!question || input.disabled) { input.focus(); return; }

    addUserMessage(question);
    lastQuestion = question;

    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;
    showTyping();

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, language: selectedLanguage })
        });

        if (!response.ok) throw new Error("Server error");
        const data = await response.json();

        setTimeout(() => {
            removeTyping();
            addBotResponse(data);
            releaseInput();
        }, 420);

    } catch (error) {
        console.error(error);
        removeTyping();
        addBotResponse({
            answer: "Can't reach the server right now. Check that the Flask app is running, then send the question again.",
            category: "Unknown",
            suggestions: []
        });
        releaseInput();
    }
}

function releaseInput() {
    input.disabled = false;
    sendBtn.disabled = input.value.trim().length === 0;
    input.focus();
}

/* ---------------------------------------------- shortcuts ---- */

function selectCategory(category) {
    const lang = currentUILanguage();
    const localizedQuestions = CATEGORY_QUESTIONS_LOCAL[lang] || CATEGORY_QUESTIONS;
    const question = localizedQuestions[category] || CATEGORY_QUESTIONS[category];
    if (!question) return;
    input.value = question;
    sendQuestion();
}

function askSuggestion(button) {
    input.value = button.textContent.trim();
    sendQuestion();
}

/* ---------------------------------------------- language ---- */

if (languageSelect) {
    languageSelect.addEventListener("change", () => {
        selectedLanguage = languageSelect.value;
        localStorage.setItem("campusbuddy-language", selectedLanguage);
        updateLanguageUI();

        // Refresh the initial greeting in the selected language when chat is still empty.
        if (thread.children.length === 1 && !app.classList.contains("chatting")) {
            thread.innerHTML = "";
            botGreeting();
        }
        input.focus();
    });
}

/* ---------------------------------------------- actions ---- */

async function sendFeedback(button, feedbackType) {
    const msg = button.closest(".msg");
    const row = button.closest(".actions");

    try {
        await fetch("/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: msg.dataset.question,
                answer: msg.dataset.answer,
                feedback: feedbackType
            })
        });

        const lang = currentUILanguage();
        row.outerHTML = `<span class="thanks">${escapeHTML((UI_TEXT[lang] || UI_TEXT.en).thanks)}</span>`;
    } catch (error) {
        console.error("Feedback error:", error);
    }
}

async function copyAnswer(button) {
    const msg = button.closest(".msg");
    try {
        await navigator.clipboard.writeText(msg.dataset.answer || "");
        button.innerHTML = icon("i-check");
        button.classList.add("done");
        button.title = (UI_TEXT[currentUILanguage()] || UI_TEXT.en).copied;
        setTimeout(() => {
            button.innerHTML = icon("i-copy");
            button.classList.remove("done");
            button.title = (UI_TEXT[currentUILanguage()] || UI_TEXT.en).copy;
        }, 1500);
    } catch (error) {
        console.error("Copy error:", error);
    }
}

async function saveUnanswered(button) {
    const msg = button.closest(".msg");
    const box = button.closest(".unanswered");

    try {
        await fetch("/unanswered", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: msg.dataset.question })
        });

        const t = UI_TEXT[currentUILanguage()] || UI_TEXT.en;
        box.innerHTML = `<p>${escapeHTML(t.sent)}</p>`;
    } catch (error) {
        console.error("Unanswered question error:", error);
    }
}

function clearChat() {
    thread.innerHTML = "";
    app.classList.remove("chatting");
    lastQuestion = "";
    botGreeting();
    updateLanguageUI();
    input.value = "";
    sendBtn.disabled = true;
    chatBox.scrollTo({ top: 0 });
    input.focus();
}

/* ---------------------------------------------- theme ---- */
/* Dark is the default look; body.light switches to the pale theme. */

function applyTheme(isLight) {
    document.body.classList.toggle("light", isLight);
    const t = UI_TEXT[currentUILanguage()] || UI_TEXT.en;
    themeBtn.setAttribute("aria-label", isLight ? t.themeDark : t.themeLight);
}

function toggleTheme() {
    const isLight = !document.body.classList.contains("light");
    applyTheme(isLight);
    localStorage.setItem("theme", isLight ? "light" : "dark");
}

applyTheme(localStorage.getItem("theme") === "light");

/* ---------------------------------------------- input events ---- */

input.addEventListener("input", () => {
    sendBtn.disabled = input.value.trim().length === 0;
});

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
});

/* ---------------------------------------------- boot ---- */

updateLanguageUI();
botGreeting();
input.focus();