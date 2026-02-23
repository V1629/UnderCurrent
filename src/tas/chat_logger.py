"""
TAS Chat Logger
===============

Logs continuous chat sessions with the TAS submodule, updating analysis and saving outputs to an Excel file.

Features:
- Interactive chat loop (user enters messages)
- Each message analyzed by TASAnalyzer
- Outputs appended to Excel file (using pandas)
- Session and user tracking
- Columns: timestamp, user_id, session_id, message, tense_class, hedge_score, zimbardo_profile, migration_event, flags

Usage:
------
python chat_logger.py
"""

import pandas as pd
import datetime
from analyzer import TASAnalyzer

EXCEL_PATH = "tas_chat_log.xlsx"

class ChatLogger:
    def __init__(self, user_id="anonymous", session_id="default"):
        self.analyzer = TASAnalyzer()
        self.user_id = user_id
        self.session_id = session_id
        self.df = pd.DataFrame(columns=[
            "timestamp", "user_id", "session_id", "message",
            "tense_class", "hedge_score", "zimbardo_profile", "migration_event", "flags"
        ])

    def log_message(self, message: str):
        output = self.analyzer.analyze(message, user_id=self.user_id, session_id=self.session_id)
        for sentence in output.sentences:
            row = {
                "timestamp": datetime.datetime.now().isoformat(),
                "user_id": self.user_id,
                "session_id": self.session_id,
                "message": sentence.text,
                "tense_class": sentence.tense_class_name,
                "hedge_score": sentence.hedge_score,
                "zimbardo_profile": output.session_zimbardo_delta,
                "migration_event": ", ".join(output.sentence_level_events),
                "flags": ", ".join(sentence.flags),
            }
            self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        self.df.to_excel(EXCEL_PATH, index=False)
        print(f"Logged {len(output.sentences)} sentences to {EXCEL_PATH}")

    def chat_loop(self):
        print(f"TAS Chat Logger started. User: {self.user_id}, Session: {self.session_id}")
        print("Type your message and press Enter. Type 'exit' to quit.")
        while True:
            msg = input("You: ")
            if msg.strip().lower() == "exit":
                print("Exiting chat logger.")
                break
            self.log_message(msg)

if __name__ == "__main__":
    logger = ChatLogger()
    logger.chat_loop()
