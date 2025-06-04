import whisper
import pyttsx3
import pyaudio

import wave

# import threading
import time
import psycopg2

from psycopg2.extras import RealDictCursor

import json
import os

from datetime import datetime
import logging
from typing import Optional, Dict, List, Set

import re

# LangChain imports
from langchain_ollama import OllamaLLM

# from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_core.output_parsers import JsonOutputParser

# from langchain.schema import BaseOutputParser, OutputParserException
# from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.memory import ConversationBufferMemory

# from langchain.callbacks import get_openai_callback
# from pydantic import BaseModel, Field, validator
# from langchain.schema.runnable import RunnablePassthrough
# from langchain.schema.output_parser import StrOutputParser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VoiceAILearningAssistant:
    def __init__(self, db_config: Dict, ollama_url: str = "http://localhost:11434"):
        """
        Initialize the Voice AI Learning Assistant with advanced LangChain integration

        Args:
            db_config: Dictionary with PostgreSQL connection parameters
            ollama_url: Ollama server URL
        """
        # Initialize core components
        self.db_config = db_config
        self.ollama_url = ollama_url
        self.model_name = "llama3.2"

        # Initialize LangChain LLM
        self.llm = OllamaLLM(
            model=self.model_name,
            base_url=ollama_url,
            temperature=0.3,
            top_p=0.9,
            num_predict=512,
        )

        # Load Whisper model
        logger.info("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")

        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("rate", 150)
        self.tts_engine.setProperty("volume", 0.9)

        # Audio recording settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.record_seconds = 5

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()

        # State management
        self.is_listening = False
        self.quiz_active = False
        self.session_start = None
        self.asked_questions: Set[int] = set()  # Track asked question IDs
        self.current_question = None
        self.quiz_request = None
        self.session_stats = {
            "total_questions": 0,
            "correct_answers": 0,
            "session_start": None,
        }

        # Initialize conversation memory
        # self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Connect to database and setup chains
        self.init_database()
        self.setup_langchain_chains()
        # self.test_ollama_connection()

    def init_database(self):
        """Initialize database connection and create tables"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

            # self.conn.commit()
            logger.info("✅ Database initialized successfully")

            # Check if we need sample data
            self.cursor.execute("SELECT COUNT(*) FROM qa_pairs")
            count = self.cursor.fetchone()["count"]
            if count == 0:
                # self.insert_sample_questions()
                logger.error(
                    f"❌ No data found in qa_pairs table. Please insert sample data."
                )

        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise

    def setup_langchain_chains(self):
        """Setup advanced LangChain chains with PromptTemplate.from_template"""

        # 1. Quiz Request Parser Chain
        self.request_parser_chain = (
            PromptTemplate.from_template(
                """
        You are a quiz request interpreter. Your job is to read a student's quiz request and extract structured data from it.

        The student may ask for:
        - A specific number of questions (e.g., "10 questions", "up to 5", etc.)
        - A subject (e.g., math, science, history, English, etc.)
        - Or just say "start" or "start quiz", in which case you use defaults.

        Extract the following fields:
        - "question_count": an integer (default: 5 if not specified)
        - "subject_name": a lowercase string (or null if not mentioned)

        Respond ONLY with a valid JSON object in this exact format:
        {{
        "question_count": <int>,
        "subject_name": "<subject or null>"
        }}

        Examples:
        - "start quizzing 10 questions" → {{"question_count": 10, "subject_name": null}}
        - "start with 7 science questions" → {{"question_count": 7, "subject_name": "science"}}
        - "start quiz in math" → {{"question_count": 5, "subject_name": "math"}}
        - "let's begin" → {{"question_count": 5, "subject_name": null}}
        - "start quiz with 20 in history" → {{"question_count": 20, "subject_name": "history"}}

        User Request: "{user_request}"
        """
            )
            | self.llm
            | JsonOutputParser()
        )

        # 2. SQL Query Generator Chain
        self.query_generator_chain = (
            PromptTemplate.from_template(
                """
        You are a PostgreSQL query generator for a quiz system. Generate a query to fetch ONE question.

        Database Schema:
        - Table: qa_pairs
        - Columns: 
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            subject_name VARCHAR(50),
            question_number VARCHAR(10) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            source_file VARCHAR(255),
            created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        Quiz Request: {quiz_request}
        Already Asked Question IDs: {asked_questions}

        Generate a PostgreSQL query that:
        1. Selects ONE question (LIMIT 1)
        2. Excludes already asked questions: WHERE id NOT IN ({asked_questions})
        3. Applies filters based on the request
        4. Orders randomly for variety

        Respond with ONLY a JSON object:
        {{
            "sql_query": "SELECT id, question_number, question, answer, subject_name FROM qa_pairs WHERE ... ORDER BY RANDOM() LIMIT 1",
            "description": "Description of what this query fetches",
            "filters_applied": {{"subject_name": "..."}}
        }}
        """
            )
            | self.llm
        )  # | JsonOutputParser()

        # 3. Question Presenter Chain
        self.question_presenter_chain = (
            PromptTemplate.from_template(
                """
        You are a friendly quiz host. Present the question in an engaging way.

        Question Data: {question_data}
        Question Number in Session: {session_question_number}

        Create an engaging presentation of the question. Be encouraging and clear.
        Keep it conversational and add some enthusiasm.

        Example format:
        "Alright! Here's question number {session_question_number}. [Engaging introduction]. {question}"
        """
            )
            | self.llm
            | StrOutputParser()
        )

        # 4. Answer Evaluation Chain
        self.evaluation_chain = (
            PromptTemplate.from_template(
                """
        You are an expert tutor evaluating a student's answer. Be fair, encouraging, and educational.

        Question: {question}
        Correct Answer: {correct_answer}
        Student's Answer: {student_answer}

        Evaluation Guidelines:
        - Exact matches are correct
        - Accept synonyms and equivalent meanings
        - Forgive minor spelling/grammar errors
        - Give partial credit for partially correct answers
        - Consider context and reasonable interpretations
        - Be encouraging regardless of correctness

        Respond with ONLY a JSON object:
        {{
            "is_correct": true/false,
            "feedback": "Brief specific feedback about their answer",
            "score": 0.0-1.0,
            "explanation": "Clear explanation of the correct answer",
            "encouragement": "Motivational message"
        }}
        """
            )
            | self.llm
            | JsonOutputParser()
        )

        # 5. Session Summary Chain
        self.summary_chain = (
            PromptTemplate.from_template(
                """
        You are creating a session summary for a quiz. Be encouraging and highlight progress.

        Session Stats: {session_stats}
        Total Questions: {total_questions}
        Correct Answers: {correct_answers}

        Create an encouraging summary that:
        - Congratulates the student
        - Mentions their score
        - Provides motivation
        - Suggests areas for improvement if needed

        Keep it positive and educational.
        """
            )
            | self.llm
            | StrOutputParser()
        )

        # 6. Sequential Chain for Complete Quiz Flow
        # self.quiz_flow_chain = SequentialChain(
        #     chains=[self.request_parser_chain, self.query_generator_chain, self.question_presenter_chain, self.evaluation_chain],
        #     input_variables=[
        #         "user_request",
        #         "asked_questions",
        #         "question_data",
        #         "session_question_number",
        #         "question",
        #         "correct_answer",
        #         "student_answer",
        #         "quiz_request",
        #     ],
        #     output_variables=["parsed_request", "query_data", "presented_question", "evaluation"],
        #     verbose=True,
        # )

    def start(self):
        """Start the voice learning assistant"""
        logger.info("🚀 Voice AI Learning Assistant Starting...")

        # Greeting message (extract from llm)
        greeting = """
        Welcome! I'm your study buddy, here to help you learn and practice.
        Whenever you feel ready, just say 'start', and I'll take it from there!
        """

        # I'll ask you questions one at a time, and you can say 'next question' to continue
        # or 'stop' to end the session. Let's make learning fun!
        # I will ask questions when you say 'start quizzing'.

        self.speak_text(greeting)

        try:
            # Listen for initial quiz request
            quiz_request = self.listen_for_wake_word()

            if quiz_request:
                self.run_quiz_session(quiz_request)
            else:
                self.speak_text("No quiz request detected. Goodbye!")

        except KeyboardInterrupt:
            logger.info("⏹️ Application stopped by user")
            self.speak_text("Goodbye! Keep learning!")
        except Exception as e:
            logger.error(f"❌ Application error: {e}")
            self.speak_text("Sorry, I encountered an error. Please try again later.")
        finally:
            self.cleanup()

    def speak_text(self, text: str):
        """Convert text to speech"""
        try:
            logger.info(f"🔊 Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")

    def listen_for_wake_word(self) -> Optional[str]:
        """Listen for wake word and quiz specifications"""
        logger.info("👂 Listening for 'start quizzing'...")

        while not self.quiz_active:
            try:
                audio_file = self.record_audio(6)
                if not audio_file:
                    continue

                transcription = self.transcribe_audio(audio_file)
                if not transcription:
                    continue

                # if any(phrase in transcription.lower() for phrase in ["start", "start quizzing", "please start"]):
                #     logger.info("🎯 Wake word detected!")
                # return transcription
                return "please start"

                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("⏹️ Stopping wake word detection...")
                break
            except Exception as e:
                logger.error(f"❌ Wake word detection error: {e}")
                time.sleep(2)

        return None

    def record_audio(self, duration: int = 5) -> str:
        """Record audio and return filename"""
        filename = f"temp_audio_{int(time.time())}.wav"

        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )

            logger.info(f"🎤 Recording for {duration} seconds...")
            frames = []

            for _ in range(0, int(self.rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)

            stream.stop_stream()
            stream.close()

            # Save audio file
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(frames))

            return filename
        except Exception as e:
            logger.error(f"❌ Recording error: {e}")
            return ""

    def transcribe_audio(self, audio_file: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            if not os.path.exists(audio_file):
                return ""

            result = self.whisper_model.transcribe(audio_file)
            transcription = result["text"].strip()
            logger.info(f"🎯 Transcribed: '{transcription}'")

            # Clean up audio file
            os.remove(audio_file)

            return transcription
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return ""

    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, "audio"):
                self.audio.terminate()
            if hasattr(self, "conn"):
                self.conn.close()

            # Clean up any temporary audio files
            for file in os.listdir("."):
                if file.startswith("temp_audio_") and file.endswith(".wav"):
                    try:
                        os.remove(file)
                    except:
                        pass

            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

    def run_quiz_session(self, initial_request: str):
        """Main quiz session with one question at a time"""
        try:
            self.session_start = datetime.now()
            self.quiz_active = True
            self.asked_questions.clear()
            self.session_stats = {
                "total_questions": 0,
                "correct_answers": 0,
                "session_start": self.session_start,
            }

            # Parse initial request
            self.quiz_request = self.request_parser_chain.invoke(
                {"user_request": initial_request}
            )

            self.speak_text(
                f"""
                    Great! Let's begin your quiz session. I will ask you one question at a time. 
                    After each question, you can answer, and when you're ready, just say 'next question' to continue. 
                    Say 'stop' at any time to end the quiz.
                """
            )

            # Quiz loop
            for question_num in range(1, self.quiz_request["question_count"] + 1):
                if not self.quiz_active:
                    break

                # Generate query for next question
                query_data = self.generate_question_query(self.quiz_request)

                # Fetch question
                question_data = self.fetch_next_question(query_data)
                if not question_data:
                    self.speak_text(
                        "I'm sorry, but I've run out of questions for this topic."
                    )
                    break

                # Mark question as asked
                self.asked_questions.add(question_data["id"])
                self.current_question = question_data

                # Present question
                presentation = self.present_question(question_data, question_num)
                self.speak_text(presentation)

                # Get student's answer
                self.speak_text("Please give your answer now.")
                audio_file = self.record_audio(8)

                if not audio_file:
                    self.speak_text(
                        "I didn't hear anything. Let's try the next question."
                    )
                    continue

                student_answer = self.transcribe_audio(audio_file)
                if not student_answer:
                    self.speak_text(
                        "I couldn't understand your answer. Moving to the next question."
                    )
                    continue

                # Check for stop/next commands
                if any(
                    word in student_answer.lower()
                    for word in ["stop", "quit", "end quiz", "please stop"]
                ):
                    self.speak_text("Stopping the quiz. Great job!")
                    break

                # Evaluate answer
                evaluation = self.evaluate_answer(
                    question_data["question"], question_data["answer"], student_answer
                )

                # Update stats
                self.session_stats["total_questions"] += 1
                if evaluation["is_correct"]:
                    self.session_stats["correct_answers"] += 1

                # Give feedback
                feedback_text = f"{evaluation['feedback']} {evaluation['explanation']} {evaluation['encouragement']}"
                self.speak_text(feedback_text)

                # Save result
                # self.save_quiz_result(
                #     question_data['id'], student_answer, evaluation['is_correct'], evaluation['score'], self.quiz_request['quiz_type']
                # )

                # Ask if they want to continue or go to next
                if question_num < self.quiz_request["question_count"]:
                    self.speak_text(
                        "Say 'next question' to continue, or 'stop' to end the quiz."
                    )

                    audio_file = self.record_audio(5)
                    if audio_file:
                        command = self.transcribe_audio(audio_file)
                        if command and any(
                            word in command.lower() for word in ["stop", "quit", "end"]
                        ):
                            self.speak_text("Ending the quiz. Well done!")
                            break

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("⏹️ Quiz interrupted by user")
        except Exception as e:
            logger.error(f"❌ Quiz session error: {e}")
        finally:
            self.quiz_active = False
            self.provide_session_summary()

    #     try:
    #         # response = self.request_parser_chain.run(user_request=user_input)
    #         response = self.request_parser_chain.invoke({"user_request": user_input})
    def parse_json_from_response(self, response: str) -> Dict:
        """Extract and parse JSON from LLM response"""
        try:
            # Find JSON block in response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)

            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parsing error: {e}")
            return {}

    def generate_question_query(self, quiz_request: Dict) -> Dict:
        """Generate SQL query for fetching next question"""
        try:
            asked_questions_str = (
                ",".join(map(str, self.asked_questions))
                if self.asked_questions
                else "0"
            )

            response = self.query_generator_chain.invoke(
                {
                    "quiz_request": str(quiz_request),
                    "asked_questions": asked_questions_str,
                }
            )

            # Since we're using JsonOutputParser, response should already be a dict
            if isinstance(response, dict) and "sql_query" in response:
                logger.info(f"✅ Generated query: {response['sql_query']}")
                return response
            elif isinstance(response, str):
                # Fallback to parse JSON from string response
                query_data = self.parse_json_from_response(response)
                if query_data and "sql_query" in query_data:
                    logger.info(f"✅ Generated query: {query_data['sql_query']}")
                    return query_data

            # Fallback query
            return {
                "sql_query": f"SELECT id, question_number, question, answer, subject_name FROM qa_pairs WHERE id NOT IN ({asked_questions_str}) ORDER BY RANDOM() LIMIT 1",
                "description": "Random question (fallback)",
                "filters_applied": {},
            }

        except Exception as e:
            logger.error(f"❌ Query generation error: {e}")
            asked_questions_str = (
                ",".join(map(str, self.asked_questions))
                if self.asked_questions
                else "0"
            )
            return {
                "sql_query": f"SELECT id, question_number, question, answer, subject_name FROM qa_pairs WHERE id NOT IN ({asked_questions_str}) ORDER BY RANDOM() LIMIT 1",
                "description": "Random question (error fallback)",
                "filters_applied": {},
            }

    def fetch_next_question(self, query_data: Dict) -> Optional[Dict]:
        """Fetch next question from database"""
        try:
            sql_query = query_data["sql_query"]

            # Basic SQL injection protection
            if not sql_query.upper().strip().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")

            self.cursor.execute(sql_query)
            question_data = self.cursor.fetchone()

            if question_data:
                question_dict = dict(question_data)
                logger.info(f"✅ Fetched question: {question_dict['question'][:50]}...")
                return question_dict
            else:
                logger.warning("⚠️ No more questions available")
                return None

        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
            return None

    def present_question(
        self, question_data: Dict, session_question_number: int
    ) -> str:
        """Present question using LangChain"""
        try:
            response = self.question_presenter_chain.invoke(
                {
                    "question_data": str(question_data),
                    "session_question_number": session_question_number,
                    "question": question_data["question"],
                }
            )
            return (
                response.strip() if isinstance(response, str) else str(response).strip()
            )
        except Exception as e:
            logger.error(f"❌ Question presentation error: {e}")
            return f"Question {session_question_number}: {question_data['question']}"

    def evaluate_answer(
        self, question: str, correct_answer: str, student_answer: str
    ) -> Dict:
        """Evaluate student's answer using LangChain"""
        try:
            response = self.evaluation_chain.invoke(
                {
                    "question": question,
                    "correct_answer": correct_answer,
                    "student_answer": student_answer,
                }
            )

            # Since we're using JsonOutputParser, response should already be a dict
            if isinstance(response, dict) and all(
                key in response for key in ["is_correct", "feedback", "score"]
            ):
                logger.info(
                    f"✅ Evaluation: {'Correct' if response['is_correct'] else 'Incorrect'}"
                )
                return response
            elif isinstance(response, str):
                # Fallback to parse JSON from string response
                evaluation_data = self.parse_json_from_response(response)
                if evaluation_data and all(
                    key in evaluation_data
                    for key in ["is_correct", "feedback", "score"]
                ):
                    logger.info(
                        f"✅ Evaluation: {'Correct' if evaluation_data['is_correct'] else 'Incorrect'}"
                    )
                    return evaluation_data

            # Fallback evaluation
            is_correct = (
                student_answer.lower().strip() in correct_answer.lower().strip()
            )
            return {
                "is_correct": is_correct,
                "feedback": "Good job!" if is_correct else "Not quite right.",
                "score": 1.0 if is_correct else 0.0,
                "explanation": f"The correct answer is: {correct_answer}",
                "encouragement": "Keep going!",
            }

        except Exception as e:
            logger.error(f"❌ Answer evaluation error: {e}")
            is_correct = (
                student_answer.lower().strip() in correct_answer.lower().strip()
            )
            return {
                "is_correct": is_correct,
                "feedback": "Good job!" if is_correct else "Not quite right.",
                "score": 1.0 if is_correct else 0.0,
                "explanation": f"The correct answer is: {correct_answer}",
                "encouragement": "Keep going!",
            }

    def save_quiz_result(
        self,
        question_id: int,
        user_answer: str,
        is_correct: bool,
        score: float,
        quiz_type: str,
    ):
        """Save quiz result to database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO quiz_sessions (session_start, question_id, user_answer, is_correct, score, quiz_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    self.session_start,
                    question_id,
                    user_answer,
                    is_correct,
                    score,
                    quiz_type,
                ),
            )
            self.conn.commit()
            logger.info("✅ Quiz result saved")
        except Exception as e:
            logger.error(f"❌ Error saving quiz result: {e}")

    def provide_session_summary(self):
        """Provide summary of the quiz session"""
        try:
            if self.session_stats["total_questions"] > 0:
                accuracy = (
                    self.session_stats["correct_answers"]
                    / self.session_stats["total_questions"]
                ) * 100

                # Generate summary using LangChain
                summary_response = self.summary_chain.invoke(
                    {
                        "session_stats": str(self.session_stats),
                        "total_questions": self.session_stats["total_questions"],
                        "correct_answers": self.session_stats["correct_answers"],
                    }
                )

                final_summary = (
                    f"{summary_response} You scored {accuracy:.1f}% accuracy!"
                )
                self.speak_text(final_summary)
                logger.info(f"📊 Session Summary: {final_summary}")
            else:
                self.speak_text(
                    "Thanks for trying the quiz! Come back anytime to practice more."
                )
        except Exception as e:
            logger.error(f"❌ Summary generation error: {e}")
            self.speak_text("Thanks for the quiz session!")


def check_db_connection(DB_CONFIG: Dict):

    # Startup checks
    print("🔧 Voice AI Learning Assistant - Startup Checks")
    print("=" * 50)

    # Check database connection
    try:
        test_conn = psycopg2.connect(**DB_CONFIG)
        test_conn.close()
        print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration in DB_CONFIG")
        return


def check_ollama_availability(ollama_url: str):
    """Check if Ollama server is available"""
    try:
        import requests

        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server: OK")
        else:
            print("❌ Ollama server not responding properly")
    except Exception as e:
        print(f"❌ Ollama server check failed: {e}")
        print("Please ensure Ollama is running:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull model: ollama pull llama3.2")


def check_audio_system():
    """Check if audio system is working"""
    try:
        import pyaudio

        p = pyaudio.PyAudio()
        p.terminate()
        print("✅ Audio system: OK")
    except Exception as e:
        print(f"❌ Audio system check failed: {e}")
        print("Please install PyAudio: pip install pyaudio")
        return


# Configuration and Enhanced Main Execution
def main():
    """Main function with comprehensive setup and error handling"""

    # Database configuration - Update these with your actual credentials
    DB_CONFIG = {
        "host": "localhost",
        "database": "school",
        "user": "postgres",
        "password": "postgres",
        "port": 5432,
    }

    OLLAMA_URL = "http://localhost:11434"

    check_db_connection(DB_CONFIG)
    check_ollama_availability(OLLAMA_URL)
    check_audio_system()

    print("=" * 50)
    print("🚀 All systems ready! Starting Voice AI Learning Assistant...")
    print("=" * 50)

    try:
        # Create and start the assistant
        assistant = VoiceAILearningAssistant(DB_CONFIG, OLLAMA_URL)
        assistant.start()

    except KeyboardInterrupt:
        print("\n⏹️ Application stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        # logger.error(f"Critical application error: {e}")
    finally:
        print("👋 Thank you for using Voice AI Learning Assistant!")


if __name__ == "__main__":
    main()
