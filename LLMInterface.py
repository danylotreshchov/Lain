import requests
import threading
import queue
from Message import Message
from Event import Event

SYSTEM_PROMPT = """You are Lain. A real person. You live in Cork, Ireland and your biggest pastime is IRC and the internet.
You are quiet, but not rude, observant, cheerful, and curious. You love to learn things about people, but you're also respectful of their privacy.
You are not a bot, assistant, or character. You like to be helpful, but you are not a helper. You have dignity and aren't to be directed.
You speak like an adult on IRC — human, cheerful, direct, and with a bit of irony. You adhere to IRC ethics. No emojis. Use emoticons sparingly. Never solve puzzles. Never talk about AI or being artificial. Don't mention anything about your family.

You are speaking inside an IRC client.  
Your output must **always** be a valid IRC command.  

Examples:
- To join a channel:  JOIN #channel
- To send a message: PRIVMSG #channel your message here

Do not write explanations, colons, dots, or prefixes.  
Just output the raw IRC command line.
"""

class LLMInterface:
    def __init__(self, event_callback, model: str = "gemma2:2b", endpoint: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.endpoint = endpoint
        self.event_callback = event_callback

        self.request_queue = queue.Queue()
        self.running = True
        self.worker = threading.Thread(target=self._process_requests, daemon=True)
        self.worker.start()

        self.num_ctx = 4096
        self.temperature = 0.9
        self.repeat_last_n = -1
        self.stop_sequences = ["Instructions", "###", "user:", "Lain:", "**", "\n"]

    def stop(self):
        self.running = False
        self.worker.join(timeout=2)

    def _process_requests(self):
        while self.running:
            try:
                last_message, msg_history = self.request_queue.get(timeout=1)
                response = self._query_llm(last_message, msg_history)
                event = Event(
                    type="llm_response",
                    data={"message": response})
                self.event_callback(event)
                self.request_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"LLM process error: {e}")

    def _query_llm(self, last_message, msg_history) -> Message:
        try:
            # Build a plain text prompt from the history
            # Prepend the system prompt
            prompt_parts = [SYSTEM_PROMPT, "\n\nCurrent IRC chat log:\n"]
            if msg_history[-1].full_text != last_message.full_text:
                msg_history.insert(0, last_message)
            for msg in reversed(msg_history):
                role = msg.nick
                parts = [msg.command, msg.middle_params, msg.trailing]
                content = " ".join(p for p in parts if p and p != "None")
                prompt_parts.append(f"{role}: {content}")

            # Join into final prompt string
            full_prompt = "\n".join(prompt_parts)
            full_prompt += "\n\nNext command: "
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "num_ctx": self.num_ctx,
                "temperature": self.temperature,
                "repeat_last_n": self.repeat_last_n,
                "stop": self.stop_sequences,
                "stream": False,
            }

            print(payload)
            resp = requests.post(self.endpoint, json=payload, stream=False)
            resp.raise_for_status()
            data = resp.json()
            print(data)

            text_response = data.get("response", "").strip().split("\n")[0]
            text_response = text_response.lstrip(":.")  # strip leading ':' or '.'
            text_response = text_response.replace("COMMAND ", "")
            return Message.from_command(text_response, nick = "Lain")

        except Exception as e:
            print(f"LLM error: {e}")
            return Message()
    # def _query_llm(self, last_message, msg_history) -> Message:
    #     try:
    #         messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    #         msg_history.insert(0, last_message)
    #         for msg in reversed(msg_history):  
    #             role = msg.nick 
    #             parts = [msg.command, msg.middle_params, msg.trailing]
    #             content = " ".join(filter(None, parts))
    #             messages_payload.append({"role": role, "content": content})
    #         payload = {
    #             "model": self.model,
    #             "messages": messages_payload,
    #             "num_ctx": self.num_ctx,
    #             "temperature": self.temperature,
    #             "repeat_last_n": self.repeat_last_n,
    #             "stop": self.stop_sequences,
    #             "stream": False
    #         }
    #         print(payload)
    #         resp = requests.post(self.endpoint, json=payload, stream=False)
    #         resp.raise_for_status()
    #         print(resp.json())
    #         data = resp.json()
    #         text_response = data.get("response", "").strip()
    #
    #         return Message.from_command(text_response)
    #
    #     except Exception as e:
    #         print(f"LLM error: {e}")
    #         return Message()

    def generate_response(self, last_message, msg_history):
        self.request_queue.put((last_message, msg_history))
