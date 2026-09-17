# 🎓 CampusBuddy – College FAQ Chatbot

CampusBuddy is a simple NLP-based college FAQ chatbot developed using Python and Flask. It helps students get quick answers to common college-related questions such as admission, academics, examinations, fees, hostel, library, placement, and transportation.

The chatbot uses **TF-IDF and Cosine Similarity** to identify the most relevant FAQ based on the user's question.

## ✨ Features

- 💬 Interactive college FAQ chatbot
- 🧠 Simple NLP-based question matching
- 🔍 TF-IDF text vectorization
- 📊 Cosine similarity for FAQ matching
- 📚 FAQ categories
- 💡 Suggested follow-up questions
- 📈 Match confidence score
- 👍/👎 User feedback
- ❓ Unanswered question collection
- 🌙 Dark/Light mode
- 🌐 Multilingual chat: English, Tamil, Tanglish and Hindi
- 🔎 Automatic language detection
- 🗣️ Friendly casual conversation support
- ⌨️ Typing indicator
- 📱 Responsive design
- 🛡️ Safe user-input rendering

## 🛠️ Technologies Used

- Python
- Flask
- Scikit-learn
- TF-IDF
- Cosine Similarity
- HTML
- CSS
- JavaScript
- JSON

## 🏗️ Project Structure

```text
CampusBuddy/
├── app.py
├── faq.json
├── feedback.json
├── unanswered.json
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## 🧠 How It Works

```text
User Question
      ↓
Language Detection / Language Selection
      ↓
Tamil / Hindi / Tanglish Normalization
      ↓
TF-IDF Vectorization
      ↓
Cosine Similarity
      ↓
Find Best FAQ Match
      ↓
Return Answer in Selected Language
```

If a suitable FAQ cannot be found, the chatbot provides a fallback response and allows the user to submit the unanswered question.

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/CampusBuddy.git
cd CampusBuddy
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

#### Windows

```bash
python app.py
```

#### macOS / Linux

```bash
python3 app.py
```

### 5. Open in your browser

```text
http://127.0.0.1:5000
```

## 🌐 Supported Languages

CampusBuddy supports: 

- 🇬🇧 English
- 🇮🇳 Tamil (தமிழ்)
- 🗣️ Tanglish (Tamil written in English letters)
- 🇮🇳 Hindi (हिन्दी)

Use **Auto** mode to detect the language from the message, or choose a language from the 🌐 selector in the header.

Examples:

- `What is the hostel fee?`
- `ஹாஸ்டல் வசதிகள் என்ன?`
- `Hostel facilities enna irukku?`
- `हॉस्टल में क्या सुविधाएँ हैं?`

The multilingual layer works offline using built-in language aliases and response translations, so no translation API key is required.

## 💬 Example Questions

- What are the college timings?
- What is the library timing?
- How can I apply for admission?
- What documents are required for admission?
- What hostel facilities are available?
- How can I register for placements?
- When are semester exams conducted?
- Does the college provide bus facilities?
- How can I pay my college fees?
- How can I contact the college?

## 📂 Data Files

### `faq.json`
Contains the FAQ knowledge base with questions, categories, keywords, and answers.

### `feedback.json`
Stores user feedback for chatbot responses.

### `unanswered.json`
Stores questions that the chatbot could not answer so they can be reviewed later.

## 🎯 Future Improvements

- Voice input
- Voice input
- Text-to-speech
- Database integration
- Admin dashboard
- Advanced semantic embeddings
- Authentication
- Cloud deployment

## 🚀 Live Demo

👉 **[Launch CampusBuddy](https://campusbuddy-57r4.onrender.com/)**

Try the CampusBuddy multilingual college FAQ chatbot online.

## 👨‍💻 Author

**Bharath R**

## 📄 License

This project is created for educational and academic purposes.

> **Note:** The FAQ answers included in this starter project are generic sample information. Replace them with verified information from your college before presenting or publishing the application as a real college assistant.


## Multilingual Support
CampusBuddy supports English, Tamil, Tanglish, Hindi, Kannada, Urdu, Gujarati, Telugu, Marathi, and Bengali. The six additional regional languages use online Google translation through `deep-translator` for FAQ matching, answers, and suggestions. Internet access is required for those automatic translations; the core English/Tamil/Tanglish/Hindi functionality remains available offline.
