import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from flask import Flask, send_file, jsonify, request, render_template_string
import requests
import folium
import random
import os

# Flask App Setup
app = Flask(__name__)

# HTML template as a string to avoid file encoding issues
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geography Quiz Bot</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <h1>🌍 AI Geography Quiz Bot</h1>
        <div class="main-content">
            <div class="quiz-column">
                <div id="quiz-container">
                    <div id="start-screen">
                        <p>Welcome to the Geography Quiz! Test your knowledge and explore the world.</p>
                        <input type="number" id="num-questions" min="1" max="10" value="5" placeholder="Number of Questions">
                        <button onclick="startQuiz()">Start Quiz</button>
                    </div>
                    <div id="question-container" style="display: none;">
                        <h2 id="question-text"></h2>
                        <div id="options"></div>
                        <div id="feedback" class="feedback"></div>
                    </div>
                    <div id="result-screen" style="display: none;">
                        <h2>Quiz Completed!</h2>
                        <p id="result-text"></p>
                        <button onclick="restartQuiz()">Play Again</button>
                    </div>
                </div>
            </div>
            <div class="map-column">
                <div id="map-container">
                    <iframe id="map-iframe" src="/map" width="100%" height="100%"></iframe>
                </div>
            </div>
        </div>
        <div class="credits">
            <p>Made by: Abhishek Singh</p>
        </div>
    </div>
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
"""

def fetch_questions(num_questions):
    url = f"https://opentdb.com/api.php?amount={num_questions}&category=22&type=multiple"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.RequestException as e:
        print(f"Failed to fetch questions: {e}")
        return []

def create_interactive_map(questions, cumulative_score, rounds_played):
    # Create map directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    world_map = folium.Map(location=[20.5937, 78.9629], zoom_start=3)
    city_data = {
        "Paris": [48.8566, 2.3522], "New York": [40.7128, -74.0060],
        "Sydney": [-33.8688, 151.2093], "Tokyo": [35.6895, 139.6917], 
        "Cairo": [30.0444, 31.2357]
    }
    
    if not questions:
        folium.Marker([0, 0], popup="No questions available.", tooltip="Error").add_to(world_map)
    else:
        for i, question in enumerate(questions):
            city = random.choice(list(city_data.keys()))
            lat, lon = city_data[city]
            hint_text = f"Hint: This question might be related to {city}! 🌍"
            folium.Marker([lat, lon], popup=hint_text, tooltip=f"Hint for Q{i + 1}").add_to(world_map)
    
    score_popup = f"Rounds Played: {rounds_played}, Score: {cumulative_score} 🎯"
    folium.Marker([0, 0], popup=score_popup, tooltip="Your Score").add_to(world_map)
    credits_popup = "Made by: Tek Narayan Yadav, Shivam Sharma, Abhishek Kumar Singh"
    folium.Marker([10, 0], popup=credits_popup, tooltip="Credits 🏆").add_to(world_map)
    
    map_path = "templates/map.html"
    world_map.save(map_path)
    return map_path

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_questions')
def get_questions():
    num_questions = int(request.args.get('num', 5))
    questions = fetch_questions(num_questions)
    return jsonify(questions)

@app.route('/map')
def serve_map():
    score = int(request.args.get('score', 0))
    rounds = int(request.args.get('rounds', 0))
    questions = fetch_questions(5)  # Fetch some questions for map markers
    map_file = create_interactive_map(questions, score, rounds)
    return send_file(map_file)

# PyQt5 Desktop App Setup
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geography Quiz Bot")
        self.setGeometry(0, 0, 1000, 600)

        self.browser = QWebEngineView(self)
        self.setCentralWidget(self.browser)
        
        # Wait for Flask to start
        time.sleep(1)
        self.browser.setUrl(QUrl("http://127.0.0.1:8080"))
        self.move_to_corner()

    def move_to_corner(self):
        screen = QApplication.primaryScreen().geometry()
        window_size = self.size()
        self.move(screen.width() - window_size.width() - 10, 
                 screen.height() - window_size.height() - 40)

def run_flask():
    app.run(host="127.0.0.1", port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Start Flask server
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start PyQt5 application
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qt_app.exec_())