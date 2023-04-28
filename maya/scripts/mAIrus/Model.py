import threading
import openai
from abc import *
from common.utils import *
from PySide2.QtCore import *


class Model(ABC):
    @abstractmethod
    def __init__(self, model_name, beautified_name, max_tokens, temperature, top_p):
        super().__init__()
        self._model_name = model_name
        self.__beautified_name = beautified_name
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._top_p = top_p
        self.__current_request_thread = None

    # Getter of the model name
    def get_model_name(self):
        return self._model_name

    # Getter of the name beautified
    def get_beautified_name(self):
        return self.__beautified_name

    # Launch request according to the model
    @abstractmethod
    def request(self, system_prompt, prompt):
        pass


class ChatCompletionModel(Model):
    def request(self, system_prompt, prompt):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "Okay, I'll answer to your request now"},
            {"role": "user", "content": prompt},
        ]
        max_tokens = self._max_tokens
        for msg_data in messages:
            max_tokens -= len(msg_data["role"]) + len(msg_data["content"])
        request_response = openai.ChatCompletion.create(
            model=self._model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
        )
        return request_response.choices[0].message.content.strip(" \n")


class ChatGPT4(ChatCompletionModel):
    def __init__(self, temperature, top_p):
        super(ChatGPT4, self).__init__(
            model_name="gpt-4",
            beautified_name="GPT-4",
            max_tokens=8192,
            temperature=temperature,
            top_p=top_p)


class ChatGPT3_5(ChatCompletionModel):
    def __init__(self, temperature, top_p):
        super(ChatGPT3_5, self).__init__(
            model_name="gpt-3.5-turbo",
            beautified_name="GPT-3.5",
            max_tokens=4096,
            temperature=temperature,
            top_p=top_p)


class ChatGPT3(Model):
    def __init__(self, temperature, top_p):
        super(ChatGPT3, self).__init__(
            model_name="text-davinci-003",
            beautified_name="GPT-3",
            max_tokens=4097,
            temperature=temperature,
            top_p=top_p)

    def request(self, system_prompt, prompt):
        final_prompt = f'System: {system_prompt} Artist: {prompt}\nAI:'
        max_tokens = self._max_tokens - len(final_prompt)
        request_response = openai.Completion.create(
            model=self._model_name,
            prompt=final_prompt,
            max_tokens=max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
        )
        return request_response.choices[0].text.strip(" \n")


# Request executed on a distinct thread
class Request(QThread):
    request_ended = Signal(str)

    def __init__(self, parent, model, system_prompt, prompt):
        super().__init__(parent)
        self.__model = model
        self.__system_prompt = system_prompt
        self.__prompt = prompt

    def run(self):
        result_request = self.__model.request(self.__system_prompt, self.__prompt)
        self.request_ended.emit(result_request)
