import os
from openai import OpenAI
import time

class Model:
    def __init__(self, model, temperature):
        self.model_name = model
        self.client = self.model_setup()
        if temperature is not None:
            self.temperature = temperature

    def model_setup(self):
        api_key = os.environ['LLM_API_KEY']
        if "qwen" in self.model_name:
            client = OpenAI(
                api_key=api_key,
                base_url="",
            )
        elif "deepseek" in self.model_name:
            client = OpenAI(
                api_key=api_key,
                base_url="",
            )
        elif "gpt" in self.model_name or "o1" in self.model_name or "o3" in self.model_name:
            client = OpenAI(
                api_key=api_key,
                base_url="",
            )
        elif "llama" in self.model_name:
            client = OpenAI(
                api_key=api_key,
                base_url=""
            )
        else:
            raise ValueError("Invalid model")

        return client

    def get_response_sample(self, instruction, prompt, n=20, use_model_settings=None):
        try:
            if use_model_settings is None:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_name,
                    n=n
                )
                responses = [chat_completion.choices[i].message.content for i in range(n)]
                return responses
            else:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_name,
                    temperature=self.temperature,
                    n=n
                )
                responses = [chat_completion.choices[i].message.content for i in range(n)]
                return responses
        except Exception as e:
            print('[ERROR]', e)
            time.sleep(5)

    def get_response(self, instruction, prompt, use_model_settings=None):
        try:
            if use_model_settings is None:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_name,
                )
            else:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_name,
                    temperature=0,
                    top_p=0.95,
                    frequency_penalty=0,
                )
            response = chat_completion.choices[0].message.content
            if response:
                return response
            else:
                return ""
        except Exception as e:
            print('[ERROR]', e)
            time.sleep(5)
