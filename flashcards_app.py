import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "flashcards.log")

class SafeStream:
    def __init__(self, filepath):
        self.filepath = filepath
        self._f = None
        try:
            self._f = open(filepath, "a", encoding="utf-8", errors="replace")
        except Exception:
            pass

    def write(self, text):
        if self._f:
            try:
                self._f.write(text)
                self._f.flush()
            except Exception:
                pass

    def flush(self):
        if self._f:
            try:
                self._f.flush()
            except Exception:
                pass

try:
    if sys.stdout is None or getattr(sys.stdout, 'encoding', None) != 'utf-8':
        sys.stdout = SafeStream(LOG_FILE)
    if sys.stderr is None or getattr(sys.stderr, 'encoding', None) != 'utf-8':
        sys.stderr = SafeStream(LOG_FILE)
except Exception:
    pass

import webview
from src import app_logic

FLASHCARDS_HTML = os.path.join(BASE_DIR, "ui", "flashcards.html")

class FlashcardsApi:
    def get_flashcard_decks(self):
        return app_logic.get_flashcard_decks()

    def get_deck_by_id(self, deck_id):
        return app_logic.get_deck_by_id(deck_id)

    def create_deck(self, name, description=""):
        return app_logic.create_deck(name, description)

    def update_deck(self, deck_id, name, description=""):
        return app_logic.update_deck(deck_id, name, description)

    def delete_deck(self, deck_id):
        return app_logic.delete_deck(deck_id)

    def add_card_to_deck(self, deck_id, word, meaning, example="", phonetic="", pos=""):
        return app_logic.add_card_to_deck(deck_id, word, meaning, example, phonetic, pos)

    def update_card_in_deck(self, deck_id, card_id, word, meaning, example="", phonetic="", pos="", learned=False):
        return app_logic.update_card_in_deck(deck_id, card_id, word, meaning, example, phonetic, pos, learned)

    def delete_card_from_deck(self, deck_id, card_id):
        return app_logic.delete_card_from_deck(deck_id, card_id)

    def toggle_card_learned(self, deck_id, card_id):
        return app_logic.toggle_card_learned(deck_id, card_id)

    def ai_suggest_vocab_card(self, word):
        return app_logic.ai_suggest_vocab_card(word)

def main():
    print("[FLASHCARDS] Starting Winter Arc Flashcards Engine...")
    api = FlashcardsApi()
    
    window = webview.create_window(
        title="Winter Arc // Vocabulary & Flashcards Engine",
        url=FLASHCARDS_HTML,
        width=1000,
        height=720,
        resizable=True,
        min_size=(780, 560),
        js_api=api
    )
    webview.start(debug=False)

if __name__ == "__main__":
    main()
