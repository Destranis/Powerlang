# Powerlang
A versatile language learning tool designed for focused vocabulary practice, featuring a Spaced Repetition System (SRS), quizzes, flashcards, and an online translator with Text-to-Speech (TTS) support.

## About The Project

Powerlang began as a simple idea for two friends learning new languages (Swedish and Dutch) and evolved into a feature-rich desktop application for Windows. It is built with Python and the wxPython GUI toolkit.
The core philosophy of Powerlang is to provide a robust, private, and offline-first environment for building and studying your own vocabulary lists. You control your data, and you control your learning schedule with a powerful SRS inspired by applications like Anki.

## Features

Powerlang is organized into several key modules to create a complete learning workflow:

### 1. Database Management

* Create Multiple Dictionaries: Organize your vocabulary into different sets (e.g., "Swedish Nouns," "Dutch Verbs," "Business Phrases").
* Full Word Management: Easily add, edit, and delete words and their translations within any dictionary.
* Delete Dictionaries: Remove entire dictionaries and all their associated words when they are no longer needed.
* Import & Export:
* Export to CSV: Save your entire word database to a universal .csv file, which can be opened in Excel, Google Sheets, or any text editor for manual editing or backup.
* Import from CSV: Quickly add words in bulk by importing a .csv file. The application will automatically create new dictionaries if they don't exist.

### 2. Learning Modes

* Spaced Repetition System (SRS): The primary and most efficient way to study. Under the "Learn" menu, select "Review Due Words" to be quizzed only on the words the algorithm determines you are close to forgetting. After seeing the answer, you grade yourself ("Forgot," "Hard," "Good," "Easy"), and Powerlang automatically calculates the next time you need to see that word.
*Practice Quiz: A classic 20-question quiz that pulls random words from your entire database. After the quiz, you are immediately re-tested on any words you got wrong.
* Simple Flashcards: A straightforward way to quickly review words. A word is shown, and clicking "Show Answer" reveals its translation before moving to the next card.

### 3. Online Tools

* Online Translator: Translate words or phrases between any of the supported languages using a reliable public API. The translator provides multiple translations and their quality scores.
* Add to Database: After translating a word, a button appears allowing you to instantly add the best translation to one of your dictionaries, creating a seamless workflow from discovery to study.

### 4. Accessibility & Usability

* Text-to-Speech (TTS): Hear the pronunciation of words in any supported language. "Speak" buttons are available in the database, quiz, review, and translator panels.
* Audio Caching: The TTS system saves audio files to a local tts_cache folder to make subsequent requests instant.
* Cache Management: The cache can be enabled or disabled in the Settings menu to control disk space usage.
* Accessible UI: All input fields are properly labeled, and critical feedback is provided via modal dialogs to ensure full compatibility with screen readers.

### 5. Settings

* Language Selection: Choose your native and learning languages from an extensive list. This choice determines the default languages in the translator and the TTS voices used during study sessions.
* Cache Control: Enable or disable the TTS audio cache.

## Getting Started

### Using the release file

The easiest way to run the program is to download the latest release and run the exe file. However, it's also possible to run Powerlang from source.

### Running from source

To get a local copy up and running, follow these simple steps.

### Prerequisites

You must have Python 3 installed on your system. You can download it from [python.org](the official website.)

### Installation

* Place all project files (powerlang.py, database.py, tts_handler.py) in a single folder.
* Create a requirements.txt file in that folder with the following content:
wxPython
gTTS
requests
playsound==1.2.2
* Open a terminal or command prompt in that folder and install the required libraries:
pip install -r requirements.txt

## Usage

To run the application, navigate to the project folder in your terminal and execute the main Python script:
python powerlang.py
On the first run, the application will automatically create two items in the folder:
* powerlang.db: The SQLite database file where all your dictionaries and words are stored.
* tts_cache/: A folder where temporary audio files for the Text-to-Speech feature are saved.
File Structure
* powerlang.py: The main application file. Contains the MainFrame and all the UI panels (DatabasePanel, QuizPanel, etc.).
* database.py: A dedicated module for all database interactions (creating, reading, updating, and deleting data from the SQLite file).
* tts_handler.py: A dedicated module for handling all Text-to-Speech functionality, including audio generation and caching.
* powerlang.db: (Auto-generated) The SQLite database file.
* tts_cache/: (Auto-generated) The directory for storing cached audio files.

