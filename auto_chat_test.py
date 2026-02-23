import subprocess
import time
import sys

# 30-40 test chat messages
MESSAGES = [
    "I'm building a startup.",
    "I will definitely launch next month.",
    "I used to run every day, but lately I've been getting back into it.",
    "I might kind of think about maybe exercising tomorrow.",
    "Nothing ever changes anyway.",
    "I think hard work matters.",
    "I believe in myself.",
    "Is it weird that I don't want to go back to work?",
    "How do you stay motivated when nothing is working?",
    "What's the fastest way to make a lot of money?",
    "How can I quit my job?",
    "How do I fix my relationship?",
    "Why am I so burned out?",
    "How do I start over?",
    "I always go to the gym on weekends.",
    "I think honesty is important.",
    "I have been through a lot.",
    "So I run into the store and see him.",
    "I would go if I had the time.",
    "I should have finished earlier.",
    "I'm worried about my future.",
    "I love my job, but the pay is low.",
    "My team is amazing, but the hours are long.",
    "I want to travel more.",
    "I feel stuck in my career.",
    "I wish I had more time for myself.",
    "I am constantly learning new things.",
    "I hope to get promoted soon.",
    "I regret not taking that opportunity.",
    "I am grateful for my friends.",
    "I am scared of failing.",
    "I want to make a difference.",
    "I am trying to be more mindful.",
    "I am looking for a new challenge.",
    "I am proud of what I've achieved.",
    "I am anxious about the future.",
    "I am excited for what's next.",
    # Additional diverse messages
    "I might go to the party if I finish work early.",
    "I absolutely will not give up.",
    "Maybe I'll try something new tomorrow.",
    "I used to think I couldn't change.",
    "I have no idea what to do next.",
    "I can't believe how much I've grown.",
    "If only I had listened to my parents.",
    "I suppose things could be worse.",
    "I am not sure if this is the right path.",
    "I definitely want to succeed.",
    "I wish things were different.",
    "I am determined to make this work.",
    "I feel like giving up sometimes.",
    "I am certain that I will achieve my goals.",
    "I might as well try.",
    "I am not afraid of failure anymore.",
    "I wonder what the future holds.",
    "I could have done better.",
    "I am hopeful for a positive outcome.",
    "I am not the same person I was last year.",
    "I am learning to accept myself.",
    "I am open to new experiences.",
    "I am working on my confidence.",
    "I am grateful for every opportunity.",
    "I am ready for a fresh start."
]

# Path to chat_logger.py (adjust if needed)
CHAT_LOGGER_PATH = "src/tas/chat_logger.py"

# Use pexpect if available, else fallback to subprocess with stdin
try:
    import pexpect
    def run_auto_chat():
        child = pexpect.spawn(f"python {CHAT_LOGGER_PATH}", encoding="utf-8")
        child.expect("Type your message and press Enter. Type 'exit' to quit.")
        for msg in MESSAGES:
            child.sendline(msg)
            time.sleep(0.2)
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print(child.before)
except ImportError:
    def run_auto_chat():
        print("pexpect not installed, using subprocess fallback (may not work interactively on all OSes)")
        proc = subprocess.Popen([sys.executable, CHAT_LOGGER_PATH], stdin=subprocess.PIPE, text=True)
        for msg in MESSAGES:
            proc.stdin.write(msg + "\n")
            proc.stdin.flush()
            time.sleep(0.2)
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        proc.stdin.close()
        proc.wait()

if __name__ == "__main__":
    run_auto_chat()
