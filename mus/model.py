from openai import OpenAI
import time


class Model:
    def __init__(self, model, api_key, temperature=1):
        self.model = model
        self.api_key = api_key
        self.client = self.model_setup()
        self.temperature = temperature

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

    def get_response(self, instruction, prompt):
        for _ in range(5):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "assistant", "content": instruction},
                        {"role": "user", "content": prompt, }
                    ],
                    model=self.model,
                    temperature=self.temperature
                )
                response = chat_completion.choices[0].message.content
                if response:
                    return response
                else:
                    return ""
            except Exception as e:
                print('[ERROR]', e)
                time.sleep(1)
