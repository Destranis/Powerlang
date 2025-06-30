# powerlang.py
# The main application file for the Powerlang language learning tool.

import wx
import database
import random
import threading
import urllib.parse
import requests
import json
import os
import sys
from datetime import date, timedelta
import tts_handler
from translations import set_language, _, get_translated_lang_name # MODIFIED

# --- Global App Settings ---
app_settings = {'native_language': 'English', 'learning_language': 'Swedish', 'keep_tts_cache': True, 'ui_language': 'en'}
# NEW: Expanded language list
lang_codes = {
    "Arabic": "ar", "Chinese (Mandarin)": "zh-CN", "Dutch": "nl", "English": "en", 
    "Finnish": "fi", "French": "fr", "German": "de", "Hungarian": "hu", 
    "Italian": "it", "Japanese": "ja", "Norwegian": "no", "Polish": "pl", 
    "Portuguese": "pt", "Russian": "ru", "Spanish": "es", "Swedish": "sv", 
    "Turkish": "tr"
}

def load_settings():
    global app_settings
    if os.path.exists('settings.json'):
        try:
            with open('settings.json', 'r') as f:
                app_settings.update(json.load(f))
        except (IOError, json.JSONDecodeError):
            save_settings()
    else:
        save_settings()

def save_settings():
    with open('settings.json', 'w') as f:
        json.dump(app_settings, f, indent=4)

# --- Dialogs ---
class LanguageSelectDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Welcome to Powerlang!")
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        choices = ["English", "Русский (Russian)", "Magyar (Hungarian)"]
        self.lang_choice = wx.Choice(self, choices=choices)
        self.lang_choice.SetSelection(0)
        main_sizer.Add(wx.StaticText(self, label="Please select your preferred language for the interface:"), 0, wx.ALL, 10)
        main_sizer.Add(self.lang_choice, 0, wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(self.CreateStdDialogButtonSizer(wx.OK), 0, wx.ALIGN_CENTER|wx.ALL, 10)
        self.SetSizerAndFit(main_sizer)
        self.Center()
    def get_lang_code(self):
        return ["en", "ru", "hu"][self.lang_choice.GetSelection()]

class WordDialog(wx.Dialog):
    def __init__(self, parent, title, native="", learned="", notes=""):
        super().__init__(parent, title=title, size=(400, 220))
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(3, 2, 10, 10)
        self.native_text = wx.TextCtrl(self, value=native)
        self.learned_text = wx.TextCtrl(self, value=learned)
        self.notes_text = wx.TextCtrl(self, value=notes)
        grid_sizer.Add(wx.StaticText(self, label=_("&Native Word:")), 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.native_text, 1, wx.EXPAND)
        grid_sizer.Add(wx.StaticText(self, label=_("&Learned Word:")), 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.learned_text, 1, wx.EXPAND)
        grid_sizer.Add(wx.StaticText(self, label=_("&Notes:")), 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.notes_text, 1, wx.EXPAND)
        grid_sizer.AddGrowableCol(1, 1)
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 15)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        self.SetSizer(main_sizer)
        self.Center()
    def get_values(self):
        return {"native": self.native_text.GetValue(), "learned": self.learned_text.GetValue(), "notes": self.notes_text.GetValue()}

class SettingsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Settings"))
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- NEW: Create a map from translated names back to English keys ---
        self.english_lang_map = {get_translated_lang_name(name): name for name in lang_codes.keys()}
        all_langs_sorted = sorted(list(self.english_lang_map.keys()))

        lang_box = wx.StaticBox(self, label=_("My Languages"))
        lang_sizer = wx.StaticBoxSizer(lang_box, wx.VERTICAL)
        native_sizer = wx.FlexGridSizer(1, 2, 5, 5)
        native_sizer.Add(wx.StaticText(self, label=_("My Native Language:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.native_lang_choice = wx.Choice(self, choices=all_langs_sorted)
        self.native_lang_choice.SetStringSelection(get_translated_lang_name(app_settings['native_language']))
        native_sizer.Add(self.native_lang_choice, 1, wx.EXPAND)
        learned_sizer = wx.FlexGridSizer(1, 2, 5, 5)
        learned_sizer.Add(wx.StaticText(self, label=_("Language I'm Learning:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.learned_lang_choice = wx.Choice(self, choices=all_langs_sorted)
        self.learned_lang_choice.SetStringSelection(get_translated_lang_name(app_settings['learning_language']))
        learned_sizer.Add(self.learned_lang_choice, 1, wx.EXPAND)
        lang_sizer.Add(native_sizer, 1, wx.EXPAND | wx.ALL, 5)
        lang_sizer.Add(learned_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        ui_lang_box = wx.StaticBox(self, label=_("Application Language"))
        ui_lang_sizer = wx.StaticBoxSizer(ui_lang_box, wx.VERTICAL)
        ui_choices = ["English", "Русский (Russian)", "Magyar (Hungarian)"]
        self.ui_lang_choice = wx.Choice(self, choices=ui_choices)
        ui_lang_code_map = {"en": "English", "ru": "Русский (Russian)", "hu": "Magyar (Hungarian)"}
        self.ui_lang_choice.SetStringSelection(ui_lang_code_map[app_settings['ui_language']])
        ui_lang_sizer.Add(self.ui_lang_choice, 0, wx.EXPAND | wx.ALL, 5)
        ui_lang_sizer.Add(wx.StaticText(self, label=_("Requires restart to take full effect.")), 0, wx.ALL, 5)
        
        cache_box = wx.StaticBox(self, label=_("Audio Cache"))
        cache_sizer = wx.StaticBoxSizer(cache_box, wx.VERTICAL)
        self.cache_checkbox = wx.CheckBox(self, label=_("Keep audio files for faster loading"))
        self.cache_checkbox.SetValue(app_settings['keep_tts_cache'])
        cache_sizer.Add(self.cache_checkbox, 0, wx.ALL, 5)
        
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK)
        main_sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(ui_lang_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(cache_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.SetSizerAndFit(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        
    def on_ok(self, event):
        global app_settings
        ui_selection_map = {"English": "en", "Русский (Russian)": "ru", "Magyar (Hungarian)": "hu"}
        new_ui_lang = ui_selection_map[self.ui_lang_choice.GetStringSelection()]
        self.Parent.needs_restart = (new_ui_lang != app_settings['ui_language'])
        
        # --- NEW: Convert translated names back to English keys before saving ---
        app_settings['native_language'] = self.english_lang_map[self.native_lang_choice.GetStringSelection()]
        app_settings['learning_language'] = self.english_lang_map[self.learned_lang_choice.GetStringSelection()]
        app_settings['keep_tts_cache'] = self.cache_checkbox.IsChecked()
        app_settings['ui_language'] = new_ui_lang
        
        save_settings()
        self.EndModal(wx.ID_OK)

# --- All Main Panels (Code shortened for brevity, no logical changes) ---
class DatabasePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.dictionaries, self.current_dict_id = {}, None
        main_sizer, control_sizer = wx.BoxSizer(wx.VERTICAL), wx.BoxSizer(wx.HORIZONTAL)
        self.dict_choice, self.delete_dict_button = wx.Choice(self), wx.Button(self, label=_("Delete This Dictionary"))
        self.Bind(wx.EVT_CHOICE, self.on_dict_selected, self.dict_choice), self.Bind(wx.EVT_BUTTON, self.on_delete_dictionary, self.delete_dict_button)
        control_sizer.Add(wx.StaticText(self, label=_("Dictionary:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5), control_sizer.Add(self.dict_choice, 1, wx.EXPAND | wx.RIGHT, 10), control_sizer.Add(self.delete_dict_button, 0)
        main_sizer.Add(control_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.word_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.word_list.InsertColumn(0, _("Native Word"), width=200), self.word_list.InsertColumn(1, _("Learned Word"), width=200), self.word_list.InsertColumn(2, _("Notes"), width=300)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_word_deselected, self.word_list), self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_word_selected, self.word_list)
        main_sizer.Add(self.word_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_button, self.edit_button, self.delete_button = wx.Button(self, label=_("Add Word...")), wx.Button(self, label=_("Edit Word...")), wx.Button(self, label=_("Delete Word"))
        self.speak_button = wx.Button(self, label=_("Speak Learned Word"))
        self.edit_button.Disable(), self.delete_button.Disable(), self.speak_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.on_add_word, self.add_button), self.Bind(wx.EVT_BUTTON, self.on_edit_word, self.edit_button), self.Bind(wx.EVT_BUTTON, self.on_delete_word, self.delete_button), self.Bind(wx.EVT_BUTTON, self.on_speak, self.speak_button)
        button_sizer.Add(self.add_button), button_sizer.Add(self.edit_button, 0, wx.LEFT, 5), button_sizer.Add(self.delete_button, 0, wx.LEFT, 5), button_sizer.AddStretchSpacer(), button_sizer.Add(self.speak_button, 0, wx.LEFT, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(main_sizer), self.populate_dictionaries()
    def populate_dictionaries(self):
        self.dict_choice.Clear(), self.word_list.DeleteAllItems(), self.edit_button.Disable(), self.delete_button.Disable(), self.speak_button.Disable()
        db_dicts = database.get_dictionaries()
        self.dictionaries = {name: id for id, name in db_dicts}
        if db_dicts: self.dict_choice.AppendItems([name for id, name in db_dicts]), self.dict_choice.SetSelection(0), self.on_dict_selected(None), self.delete_dict_button.Enable()
        else: self.current_dict_id, self.add_button.Disable(), self.delete_dict_button.Disable()
    def populate_words(self):
        self.word_list.DeleteAllItems(), self.edit_button.Disable(), self.delete_button.Disable(), self.speak_button.Disable()
        if self.current_dict_id is not None:
            self.add_button.Enable()
            for word_id, native, learned, notes in database.get_words(self.current_dict_id):
                index = self.word_list.InsertItem(self.word_list.GetItemCount(), native)
                self.word_list.SetItem(index, 1, learned), self.word_list.SetItem(index, 2, notes if notes else ""), self.word_list.SetItemData(index, word_id)
    def on_dict_selected(self, event):
        selected_name = self.dict_choice.GetStringSelection()
        if selected_name in self.dictionaries: self.current_dict_id = self.dictionaries[selected_name], self.populate_words()
    def on_delete_dictionary(self, event):
        if not self.current_dict_id: return
        dict_name = self.dict_choice.GetStringSelection()
        with wx.MessageDialog(self, _("Are you sure you want to permanently delete the entire dictionary '{name}' and all the words in it?").format(name=dict_name), _("Confirm Delete Dictionary"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING) as dlg:
            if dlg.ShowModal() == wx.ID_YES: database.delete_dictionary(self.current_dict_id), self.populate_dictionaries()
    def on_word_selected(self, event): self.edit_button.Enable(), self.delete_button.Enable(), self.speak_button.Enable()
    def on_word_deselected(self, event):
        if self.word_list.GetSelectedItemCount() == 0: self.edit_button.Disable(), self.delete_button.Disable(), self.speak_button.Disable()
    def on_add_word(self, event): self.GetParent().add_word_to_db()
    def on_edit_word(self, event):
        if (idx := self.word_list.GetFirstSelected()) == -1: return
        word_id, native, learned, notes = self.word_list.GetItemData(idx), self.word_list.GetItemText(idx), self.word_list.GetItem(idx, 1).GetText(), self.word_list.GetItem(idx, 2).GetText()
        self.GetParent().add_word_to_db(word_id=word_id, native=native, learned=learned, notes=notes)
    def on_delete_word(self, event):
        if (idx := self.word_list.GetFirstSelected()) == -1: return
        word_id, native_word = self.word_list.GetItemData(idx), self.word_list.GetItemText(idx)
        with wx.MessageDialog(self, _("Are you sure you want to delete the word '{word}'?").format(word=native_word), _("Confirm Delete"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING) as dlg:
            if dlg.ShowModal() == wx.ID_YES: database.delete_word(word_id), self.populate_words()
    def on_speak(self, event):
        if (idx := self.word_list.GetFirstSelected()) == -1: return
        learned_word, lang_code = self.word_list.GetItem(idx, 1).GetText(), lang_codes.get(app_settings['learning_language'])
        if learned_word and lang_code: threading.Thread(target=tts_handler.speak, args=(learned_word, lang_code, app_settings['keep_tts_cache']), daemon=True).start()

class ReviewPanel(wx.Panel): # ... (code is unchanged)
    def __init__(self, parent):
        super().__init__(parent)
        self.due_cards, self.current_card = [], None
        main_sizer, review_box = wx.BoxSizer(wx.VERTICAL), wx.StaticBox(self, label=_("Review Due Words"))
        sizer = wx.StaticBoxSizer(review_box, wx.VERTICAL)
        self.card_count_text, self.question_text = wx.StaticText(self, label=""), wx.StaticText(self, label=_("Loading..."))
        self.question_text.SetFont(wx.Font(36, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.show_answer_button = wx.Button(self, label=_("Show Answer"))
        self.Bind(wx.EVT_BUTTON, self.on_show_answer, self.show_answer_button)
        sizer.Add(self.card_count_text, 0, wx.ALL | wx.ALIGN_CENTER, 10), sizer.Add(self.question_text, 1, wx.EXPAND | wx.ALL, 20), sizer.Add(self.show_answer_button, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 20), self.SetSizer(main_sizer), self.start_review_session()
    def start_review_session(self):
        self.due_cards = database.get_due_cards()
        if not self.due_cards: wx.MessageBox(_("No words are due for review today. Great job!"), _("Review Complete"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel)
        else: self.load_next_card()
    def load_next_card(self):
        if not self.due_cards: wx.MessageBox(_("All words for this session have been reviewed!"), _("Review Complete"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel); return
        self.current_card = self.due_cards.pop(0)
        native = self.current_card[1]
        self.question_text.SetLabel(native)
        self.card_count_text.SetLabel(_("{count} words remaining.").format(count=len(self.due_cards) + 1))
        self.Layout()
        lang_code = lang_codes.get(app_settings['native_language'])
        if native and lang_code: threading.Thread(target=tts_handler.speak, args=(native, lang_code, app_settings['keep_tts_cache']), daemon=True).start()
    def on_show_answer(self, event):
        word_id, native, learned, easiness, interval, _ = self.current_card
        wx.MessageBox(_("The answer is:\n\n{answer}").format(answer=learned), _("Answer"), wx.OK | wx.ICON_INFORMATION)
        lang_code = lang_codes.get(app_settings['learning_language'])
        if learned and lang_code: threading.Thread(target=tts_handler.speak, args=(learned, lang_code, app_settings['keep_tts_cache']), daemon=True).start()
        choices = [_("Forgot (review in 1 day)"), _("Hard"), _("Good"), _("Easy")]
        with wx.SingleChoiceDialog(self, _("How well did you know it?"), _("Grade Yourself"), choices) as grade_dlg:
            if grade_dlg.ShowModal() == wx.ID_OK:
                quality = [0, 3, 4, 5][grade_dlg.GetSelection()]
                if quality < 3: interval = 1
                else:
                    easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
                    if quality == 3: interval = round(interval * 1.2)
                    elif quality == 4: interval = round(interval * easiness)
                    elif quality == 5: interval = round(interval * easiness * 1.3)
                    if interval == 0: interval = 1
                database.update_word_srs(word_id, easiness, interval, date.today() + timedelta(days=interval))
        self.load_next_card()

class QuizPanel(wx.Panel): # ... (code is unchanged)
    def __init__(self, parent):
        super().__init__(parent)
        self.session_words, self.incorrect_words, self.state, self.current_q_num = [], [], 'quiz', 0
        self.current_question, self.current_answer = None, None
        main_sizer, self.quiz_box = wx.BoxSizer(wx.VERTICAL), wx.StaticBox(self, label=_("Quiz"))
        quiz_sizer = wx.StaticBoxSizer(self.quiz_box, wx.VERTICAL)
        question_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.question_text = wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
        self.question_text.SetFont(wx.Font(24, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.speak_button = wx.Button(self, label=_("Speak"))
        question_sizer.Add(self.question_text, 1, wx.ALIGN_CENTER_VERTICAL), question_sizer.Add(self.speak_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        self.answer_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_check_answer, self.answer_input)
        self.check_button, self.close_button = wx.Button(self, label=_("Check Answer")), wx.Button(self, label=_("End Quiz Early"))
        self.Bind(wx.EVT_BUTTON, self.on_check_answer, self.check_button), self.Bind(wx.EVT_BUTTON, self.on_speak, self.speak_button), self.Bind(wx.EVT_BUTTON, lambda e: self.GetParent().show_database_panel(), self.close_button)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.check_button, 0, wx.RIGHT, 5), button_sizer.Add(self.close_button, 0, wx.LEFT, 5)
        quiz_sizer.Add(wx.StaticText(self, label=_("Translate the following:")), 0, wx.ALL, 10), quiz_sizer.Add(question_sizer, 0, wx.EXPAND | wx.ALL, 10), quiz_sizer.Add(self.answer_input, 0, wx.EXPAND | wx.ALL, 10), quiz_sizer.Add(button_sizer, 0, wx.CENTER | wx.ALL, 10)
        main_sizer.Add(quiz_sizer, 0, wx.EXPAND | wx.ALL, 20), self.SetSizerAndFit(main_sizer), self.start_session()
    def start_session(self):
        self.session_words = database.get_random_words(20)
        if not self.session_words: wx.MessageBox(_("Not enough words in database for a quiz."), _("Quiz Empty"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel); return
        self.load_next_word()
    def load_next_word(self):
        word_list = self.session_words if self.state == 'quiz' else self.incorrect_words
        if self.current_q_num >= len(word_list): self.end_phase(); return
        native, learned = word_list[self.current_q_num]
        is_native_question = random.choice([True,False])
        self.current_question, self.current_answer = (native, learned) if is_native_question else (learned, native)
        self.question_lang_code = lang_codes.get(app_settings['native_language']) if is_native_question else lang_codes.get(app_settings['learning_language'])
        self.question_text.SetLabel(self.current_question)
        self.answer_input.SetValue("")
        self.answer_input.SetFocus()
        self.GetParent().SetStatusText(_("Question {current} of {total}").format(current=self.current_q_num + 1, total=len(word_list)))
        self.on_speak(None)
    def on_check_answer(self, event):
        user_answer, correct_answer = self.answer_input.GetValue().strip().lower(), self.current_answer.strip().lower()
        if user_answer == correct_answer: wx.MessageBox(_("Correct!"), _("Result"), wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(_("Incorrect.\nThe correct answer is: {answer}").format(answer=self.current_answer), _("Result"), wx.OK | wx.ICON_ERROR)
            if self.state == 'quiz': self.incorrect_words.append(self.session_words[self.current_q_num])
        self.current_q_num += 1
        self.load_next_word()
    def end_phase(self):
        if self.state == 'quiz':
            if not self.incorrect_words: wx.MessageBox(_("Quiz complete! You got all 20 words correct!"), _("Perfect!"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel); return
            wx.MessageBox(_("Initial quiz complete. Now let's retry the {count} words you missed.").format(count=len(self.incorrect_words)), _("Retry Phase"), wx.OK | wx.ICON_INFORMATION)
            self.state, self.current_q_num = 'retry', 0
            self.quiz_box.SetLabel(_("Quiz - Retrying Incorrect Words")), self.load_next_word()
        else: wx.MessageBox(_("Retry phase complete! Well done."), _("Quiz Finished"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel)
    def on_speak(self, event):
        if self.current_question and self.question_lang_code: threading.Thread(target=tts_handler.speak, args=(self.current_question, self.question_lang_code, app_settings['keep_tts_cache']), daemon=True).start()

class FlashcardPanel(wx.Panel): # ... (code is unchanged)
    def __init__(self, parent):
        super().__init__(parent)
        self.session_words, self.current_answer, self.current_index = [], "", 0
        main_sizer, fc_box = wx.BoxSizer(wx.VERTICAL), wx.StaticBox(self, label=_("Flashcards"))
        sizer = wx.StaticBoxSizer(fc_box, wx.VERTICAL)
        self.card_count_text, self.word_text = wx.StaticText(self, label=""), wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
        self.word_text.SetFont(wx.Font(36, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.show_answer_button, self.close_button = wx.Button(self, label=_("Show Answer")), wx.Button(self, label=_("End Session"))
        self.Bind(wx.EVT_BUTTON, self.on_show_answer, self.show_answer_button), self.Bind(wx.EVT_BUTTON, lambda e: self.GetParent().show_database_panel(), self.close_button)
        sizer.Add(self.card_count_text, 0, wx.ALL | wx.ALIGN_CENTER, 10), sizer.Add(self.word_text, 1, wx.EXPAND | wx.ALL, 20), sizer.Add(self.show_answer_button, 0, wx.EXPAND | wx.ALL, 10), sizer.Add(self.close_button, 0, wx.ALIGN_CENTER | wx.TOP, 10)
        main_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 20), self.SetSizer(main_sizer), self.start_session()
    def start_session(self):
        self.session_words = database.get_random_words(15)
        if not self.session_words: wx.MessageBox(_("No words in database for flashcards."), _("Empty"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel); return
        self.current_index = -1
        self.load_next_card()
    def load_next_card(self):
        self.current_index += 1
        if self.current_index >= len(self.session_words): wx.MessageBox(_("Flashcard session complete!"), _("Finished"), wx.OK | wx.ICON_INFORMATION), wx.CallAfter(self.GetParent().show_database_panel); return
        native, learned = self.session_words[self.current_index]
        is_native_question = random.choice([True,False])
        question, answer = (native, learned) if is_native_question else (learned, native)
        lang_code = lang_codes.get(app_settings['native_language']) if is_native_question else lang_codes.get(app_settings['learning_language'])
        self.word_text.SetLabel(question)
        self.current_answer = answer
        self.card_count_text.SetLabel(_("Card {current} of {total}").format(current=self.current_index + 1, total=len(self.session_words)))
        self.Layout()
        if question and lang_code: threading.Thread(target=tts_handler.speak, args=(question, lang_code, app_settings['keep_tts_cache']), daemon=True).start()
    def on_show_answer(self, event): wx.MessageBox(_("The answer is:\n\n{answer}").format(answer=self.current_answer), _("Answer"), wx.OK | wx.ICON_INFORMATION), self.load_next_card()

class OnlineDictPanel(wx.Panel): # ... (code is unchanged)
    def __init__(self, parent):
        super().__init__(parent)
        self.last_search_term, self.last_best_translation = None, None
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        lang_sizer = wx.BoxSizer(wx.HORIZONTAL)
        all_langs_sorted = sorted(list(lang_codes.keys()))
        self.source_lang_choice, self.target_lang_choice = wx.Choice(self, choices=all_langs_sorted), wx.Choice(self, choices=all_langs_sorted)
        self.source_lang_choice.SetStringSelection(app_settings['native_language']), self.target_lang_choice.SetStringSelection(app_settings['learning_language'])
        lang_sizer.Add(wx.StaticText(self, label=_("From:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5), lang_sizer.Add(self.source_lang_choice, 1, wx.EXPAND | wx.RIGHT, 10), lang_sizer.Add(wx.StaticText(self, label=_("To:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5), lang_sizer.Add(self.target_lang_choice, 1, wx.EXPAND)
        search_box = wx.StaticBox(self, label=_("&Word to Translate"))
        search_sizer = wx.StaticBoxSizer(search_box, wx.HORIZONTAL)
        self.search_input, self.search_button = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER), wx.Button(self, label=_("Translate"))
        search_sizer.Add(self.search_input, 1, wx.EXPAND | wx.RIGHT, 5), search_sizer.Add(self.search_button, 0)
        self.Bind(wx.EVT_BUTTON, self.on_search, self.search_button), self.Bind(wx.EVT_TEXT_ENTER, self.on_search, self.search_input)
        self.results_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.results_text.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_to_db_button, self.speak_button, self.close_button = wx.Button(self, label=_("Add to Database...")), wx.Button(self, label=_("Speak Translation")), wx.Button(self, label=_("Close"))
        button_sizer.Add(self.add_to_db_button), button_sizer.Add(self.speak_button, 0, wx.LEFT, 10), button_sizer.AddStretchSpacer(), button_sizer.Add(self.close_button)
        self.add_to_db_button.Disable(), self.speak_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.on_add_to_db, self.add_to_db_button), self.Bind(wx.EVT_BUTTON, self.on_speak, self.speak_button), self.Bind(wx.EVT_BUTTON, lambda e: self.GetParent().show_database_panel(), self.close_button)
        main_sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 10), main_sizer.Add(search_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main_sizer.Add(self.results_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10), main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(main_sizer)
    def on_search(self, event):
        word, source_name, target_name = self.search_input.GetValue().strip(), self.source_lang_choice.GetStringSelection(), self.target_lang_choice.GetStringSelection()
        if not word: return
        self.search_button.Disable(), self.add_to_db_button.Disable(), self.speak_button.Disable()
        self.last_search_term, self.last_best_translation = None, None
        self.results_text.SetValue(_("Translating '{word}' from {source} to {target}...").format(word=word, source=source_name, target=target_name)), self.GetParent().SetStatusText(_("Translating {word}...").format(word=word))
        threading.Thread(target=self._get_advanced_translation, args=(word, source_name, target_name), daemon=True).start()
    def _get_advanced_translation(self, word, source_name, target_name):
        try:
            source_code, target_code = lang_codes.get(source_name), lang_codes.get(target_name)
            if not (source_code and target_code): wx.CallAfter(self._update_results, _("Error: Language not configured.")); return
            encoded_word = urllib.parse.quote(word)
            url = f"https://api.mymemory.translated.net/get?q={encoded_word}&langpair={source_code}|{target_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['responseStatus'] != 200: wx.CallAfter(self._update_results, _("API Error: {details}").format(details=data.get('responseDetails', 'Unknown error')))
            else:
                output = [_("Found {count} translation matches for '{word}':\n").format(count=len(data['matches']), word=word)]
                best_translation = data['responseData']['translatedText']
                for match in data['matches']:
                    output.append(f"- \"{match.get('translation', 'N/A')}\""), output.append(f"  (Source: {match.get('source', 'N/A')}, Quality: {int(float(match.get('quality', 0)) * 100)}%)")
                wx.CallAfter(self._update_results, "\n".join(output), word, best_translation)
        except requests.exceptions.RequestException as e: wx.CallAfter(self._update_results, _("A network error occurred:\n{error}").format(error=e))
        except Exception as e: wx.CallAfter(self._update_results, _("A critical error occurred:\n\n{type}: {error}").format(type=type(e).__name__, error=e))
    def _update_results(self, text, original_word=None, best_translation=None):
        self.results_text.SetValue(text), self.search_button.Enable(), self.GetParent().SetStatusText(_("Translation complete."))
        if original_word and best_translation: self.last_search_term, self.last_best_translation = original_word, best_translation; self.add_to_db_button.Enable(), self.speak_button.Enable()
    def on_add_to_db(self, event):
        if self.last_search_term and self.last_best_translation:
            source_lang = self.source_lang_choice.GetStringSelection()
            native = self.last_search_term if source_lang == app_settings['native_language'] else self.last_best_translation
            learned = self.last_best_translation if source_lang == app_settings['native_language'] else self.last_search_term
            self.GetParent().add_word_to_db(native=native, learned=learned)
    def on_speak(self, event):
        target_lang, lang_code = self.target_lang_choice.GetStringSelection(), lang_codes.get(self.target_lang_choice.GetStringSelection())
        if self.last_best_translation and lang_code: threading.Thread(target=tts_handler.speak, args=(self.last_best_translation, lang_code, app_settings['keep_tts_cache']), daemon=True).start()

class PronunciationPanel(wx.Panel): # ... (code is unchanged)
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        practice_box = wx.StaticBox(self, label=_("Practice Pronunciation in {lang}").format(lang=app_settings['learning_language']))
        sizer = wx.StaticBoxSizer(practice_box, wx.VERTICAL)
        self.text_input = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        self.text_input.SetHint(_("Type or paste any text here to practice..."))
        self.speak_button, self.close_button = wx.Button(self, label=_("Speak Text")), wx.Button(self, label=_("Close"))
        self.Bind(wx.EVT_BUTTON, self.on_speak, self.speak_button)
        self.Bind(wx.EVT_BUTTON, lambda e: self.GetParent().show_database_panel(), self.close_button)
        sizer.Add(self.text_input, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.speak_button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer.Add(self.close_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        main_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 20)
        self.SetSizer(main_sizer)
    def on_speak(self, event):
        text, lang_code = self.text_input.GetValue().strip(), lang_codes.get(app_settings['learning_language'])
        if text and lang_code: threading.Thread(target=tts_handler.speak, args=(text, lang_code, app_settings['keep_tts_cache']), daemon=True).start()
        elif not text: wx.MessageBox(_("Please enter some text to speak."), _("Input Required"), wx.OK | wx.ICON_INFORMATION)

# --- Main Application Frame ---
class MainFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=parent, title="Powerlang", size=(800, 600))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)
        self.current_content = None
        self.needs_restart = False
        self.create_menubar()
        self.CreateStatusBar()
        self.show_database_panel()
        self.Center()
        self.Show()
    def switch_panel(self, new_panel_class):
        if self.current_content: self.current_content.Destroy()
        self.current_content = new_panel_class(self)
        self.main_sizer.Add(self.current_content, 1, wx.EXPAND)
        self.Layout()
    def show_database_panel(self): self.switch_panel(DatabasePanel)
    def show_review_panel(self): self.switch_panel(ReviewPanel)
    def show_quiz_panel(self): self.switch_panel(QuizPanel)
    def show_flashcards_panel(self): self.switch_panel(FlashcardPanel)
    def show_online_dict_panel(self): self.switch_panel(OnlineDictPanel)
    def show_pronunciation_panel(self): self.switch_panel(PronunciationPanel)
    def create_menubar(self):
        menu_bar = wx.MenuBar()
        ID_MENU_REVIEW, ID_MENU_QUIZ_TEST, ID_MENU_PRONUNCIATION = wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef()
        ID_MENU_DB_CREATE, ID_MENU_DB_EDIT, ID_MENU_FLASHCARDS, ID_MENU_ONLINE_DICT = wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef()
        ID_MENU_SETTINGS, ID_MENU_SETTINGS_EXPORT, ID_MENU_SETTINGS_IMPORT = wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef()
        learn_menu, database_menu, flashcards_menu, online_dict_menu, settings_menu, file_menu = wx.Menu(), wx.Menu(), wx.Menu(), wx.Menu(), wx.Menu(), wx.Menu()
        learn_menu.Append(ID_MENU_REVIEW, _("&Review Due Words"))
        learn_menu.AppendSeparator()
        learn_menu.Append(ID_MENU_QUIZ_TEST, _("&Practice Quiz (Random)"))
        learn_menu.Append(ID_MENU_PRONUNCIATION, _("&Pronunciation Practice"))
        database_menu.Append(ID_MENU_DB_CREATE, _("&Create New Dictionary..."))
        database_menu.Append(ID_MENU_DB_EDIT, _("&View/Edit Dictionaries"))
        flashcards_menu.Append(ID_MENU_FLASHCARDS, _("&Start Session"))
        online_dict_menu.Append(ID_MENU_ONLINE_DICT, _("&Online Translator..."))
        settings_menu.Append(ID_MENU_SETTINGS, _("Change &Settings..."))
        settings_menu.AppendSeparator()
        settings_menu.Append(ID_MENU_SETTINGS_EXPORT, _("&Export Database..."))
        settings_menu.Append(ID_MENU_SETTINGS_IMPORT, _("&Import Database..."))
        exit_item = file_menu.Append(wx.ID_EXIT, _("&Exit"))
        menu_bar.Append(learn_menu, _("&Learn"))
        menu_bar.Append(database_menu, _("&Database"))
        menu_bar.Append(flashcards_menu, _("F&lashcards"))
        menu_bar.Append(online_dict_menu, _("Online &Tools"))
        menu_bar.Append(settings_menu, "&Settings")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, lambda e: self.show_review_panel(), id=ID_MENU_REVIEW)
        self.Bind(wx.EVT_MENU, lambda e: self.show_quiz_panel(), id=ID_MENU_QUIZ_TEST)
        self.Bind(wx.EVT_MENU, lambda e: self.show_pronunciation_panel(), id=ID_MENU_PRONUNCIATION)
        self.Bind(wx.EVT_MENU, self.on_db_create, id=ID_MENU_DB_CREATE)
        self.Bind(wx.EVT_MENU, lambda e: self.show_database_panel(), id=ID_MENU_DB_EDIT)
        self.Bind(wx.EVT_MENU, lambda e: self.show_flashcards_panel(), id=ID_MENU_FLASHCARDS)
        self.Bind(wx.EVT_MENU, lambda e: self.show_online_dict_panel(), id=ID_MENU_ONLINE_DICT)
        self.Bind(wx.EVT_MENU, self.on_settings, id=ID_MENU_SETTINGS)
        self.Bind(wx.EVT_MENU, self.on_export, id=ID_MENU_SETTINGS_EXPORT)
        self.Bind(wx.EVT_MENU, self.on_import, id=ID_MENU_SETTINGS_IMPORT)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)
    def add_word_to_db(self, word_id=None, native="", learned="", notes=""):
        title = _("Edit Word") if word_id else _("Add New Word")
        dictionaries = database.get_dictionaries()
        if not dictionaries: wx.MessageBox(_("You must create at least one dictionary before adding words."), _("No Dictionaries Found"), wx.OK | wx.ICON_ERROR); return
        with WordDialog(self, title, native, learned, notes) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                values = dlg.get_values()
                if not (values['native'].strip() and values['learned'].strip()): wx.MessageBox(_("Native and Learned fields cannot be empty."), _("Input Error"), wx.OK | wx.ICON_ERROR); return
                dict_names = [d[1] for d in dictionaries]
                with wx.SingleChoiceDialog(self, _("Choose a dictionary to save to:"), _("Select Dictionary"), dict_names) as choice_dlg:
                    if choice_dlg.ShowModal() == wx.ID_OK:
                        selected_dict_id = [d[0] for d in dictionaries if d[1] == choice_dlg.GetStringSelection()][0]
                        if word_id: database.update_word(word_id, values['native'], values['learned'], values['notes'])
                        else: database.add_word(values['native'], values['learned'], values['notes'], selected_dict_id)
                        if isinstance(self.current_content, DatabasePanel): self.current_content.populate_words()
    def on_db_create(self, event):
        with wx.TextEntryDialog(self, _('Enter the name for the new dictionary:'), _('Create Dictionary')) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                dict_name = dlg.GetValue().strip()
                if dict_name:
                    if not database.create_dictionary(dict_name): wx.MessageBox(_("A dictionary named '{name}' already exists.").format(name=dict_name), _("Error"), wx.OK | wx.ICON_ERROR)
                    elif isinstance(self.current_content, DatabasePanel): self.current_content.populate_dictionaries()
    def on_settings(self, event):
        self.needs_restart = False
        with SettingsDialog(self) as dlg:
            dlg.ShowModal()
        if self.needs_restart:
            with wx.MessageDialog(self, _("Settings have been saved. A restart is required to apply all changes.\n\nRestart now?"), _("Restart Now?"), wx.YES_NO | wx.ICON_QUESTION) as restart_dlg:
                if restart_dlg.ShowModal() == wx.ID_YES:
                    wx.GetApp().restart_app()
    def on_export(self, event):
        with wx.FileDialog(self, _("Save Database Export"), wildcard=_("CSV files (*.csv)|*.csv"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL: return
            try: wx.MessageBox(_("Successfully exported {count} words.").format(count=database.export_all_to_csv(dlg.GetPath())), _("Export Complete"), wx.OK | wx.ICON_INFORMATION)
            except Exception as e: wx.MessageBox(_("An error occurred during export:\n{error}").format(error=e), _("Export Error"), wx.OK | wx.ICON_ERROR)
    def on_import(self, event):
        with wx.FileDialog(self, _("Open Database Import File"), wildcard=_("CSV files (*.csv)|*.csv"), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL: return
            try:
                count = database.import_from_csv(dlg.GetPath())
                wx.MessageBox(_("Successfully imported {count} words.").format(count=count), _("Import Complete"), wx.OK | wx.ICON_INFORMATION)
                if isinstance(self.current_content, DatabasePanel): self.current_content.populate_dictionaries()
            except Exception as e: wx.MessageBox(_("An error occurred during import:\n{error}").format(error=e), _("Import Error"), wx.OK | wx.ICON_ERROR)

# --- Main App Class to handle restart ---
class App(wx.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = None
        self.init_main_frame()
    def init_main_frame(self):
        self.frame = MainFrame(None)
        self.frame.Show()
    def restart_app(self):
        self.frame.Close()
        wx.CallLater(100, self.do_restart)
    def do_restart(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

# --- Application Entry Point ---
if __name__ == '__main__':
    start_app = False
    if not os.path.exists('settings.json'):
        pre_app = wx.App()
        with LanguageSelectDialog(None) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                lang_code = dlg.get_lang_code()
                app_settings['ui_language'] = lang_code
                save_settings()
                set_language(lang_code)
                start_app = True
            else:
                start_app = False
        pre_app.Destroy()
    else:
        load_settings()
        set_language(app_settings.get('ui_language', 'en'))
        start_app = True

    if start_app:
        database.init_database()
        app = App()
        app.MainLoop()