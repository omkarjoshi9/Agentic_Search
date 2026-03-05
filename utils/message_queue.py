# utils/message_queue.py
from queue import Queue

# Global message queue that can be accessed from any thread
global_message_queue = Queue()