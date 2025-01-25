from openai import OpenAI
import time


class Model:
    def __init__(self, model, api_key, temperature=1, top_p=1, frequency_penalty=0):
        self.model = model
        self.api_key = api_key
        self.client = self.model_setup()
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty

    def model_setup(self):
        if "qwen" in self.model:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        elif "deepseek" in self.model:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        elif "gpt" in self.model or "o1" in self.model:  # based on the transit of the model
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://xiaoai.plus/v1",
            )
        elif "llama" in self.model:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.llama-api.com"
            )
        else:
            raise ValueError("Invalid model")
        return client

    def get_response(self, instruction, prompt, temperature=None):
        for _ in range(5):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "assistant", "content": instruction},
                        {"role": "user", "content": prompt, }
                    ],
                    model=self.model,
                    temperature=self.temperature if temperature is None else temperature,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                )
                response = chat_completion.choices[0].message.content
                if response:
                    return response
                else:
                    return ""
            except Exception as e:
                print('[ERROR]', e)
                time.sleep(1)


    def get_response_few_shot(self, messages, temperature=None):
        for _ in range(5):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=self.temperature if temperature is None else temperature,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                )
                response = chat_completion.choices[0].message.content
                if response:
                    return response
                else:
                    return ""
            except Exception as e:
                print('[ERROR]', e)
                time.sleep(1)