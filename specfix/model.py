import configparser
from os.path import dirname, abspath
from openai import OpenAI
import time

config = configparser.ConfigParser()
config.read(dirname(abspath(__file__)) + '/../.config')


class Model:
    def __init__(self, model, temperature=0):
        self.model_name = model
        self.client = self.model_setup()
        self.temperature = temperature

    def model_setup(self):
        if "qwen" in self.model_name:
            # api_key = config['API_KEY']['fireworksai_key']
            api_key = config['API_KEY']['aliyun_key']
            client = OpenAI(
                api_key=api_key,
                # base_url="https://api.fireworks.ai/inference/v1",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        elif "deepseek" in self.model_name:
            # api_key = config['API_KEY']['deepseek_key']
            # api_key = config['API_KEY']['fireworksai_key']
            # api_key = config['API_KEY']['aliyun_key']
            api_key = config['API_KEY']['bytedance_key']
            # api_key = config['API_KEY']['closeai_key']
            client = OpenAI(
                api_key=api_key,
                # base_url="https://api.deepseek.com"
                # base_url="https://api.fireworks.ai/inference/v1"
                # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                base_url="https://ark.cn-beijing.volces.com/api/v3"
                # base_url="https://api.openai-proxy.org/v1",
            )
        elif "gpt" in self.model_name or "o1" in self.model_name or "o3" in self.model_name:  # based on the transit of the model
            # api_key = config['API_KEY']['xiaoai_key']
            api_key = config['API_KEY']['closeai_key']
            client = OpenAI(
                api_key=api_key,
                # base_url="https://xiaoai.plus/v1",
                base_url="https://api.openai-proxy.org/v1",
            )
        elif "llama" in self.model_name:
            api_key = config['API_KEY']['fireworksai_key']
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.fireworks.ai/inference/v1"
            )
        else:
            raise ValueError("Invalid model")

        return client

    def get_response_sample(self, instruction, prompt, n=20, use_model_settings=None):
        for _ in range(5):
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
        for _ in range(5):
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
                        # top_p=0.95,
                        # frequency_penalty=0,
                        # presence_penalty=0,
                    )
                response = chat_completion.choices[0].message.content
                if response:
                    return response
                else:
                    return ""
            except Exception as e:
                print('[ERROR]', e)
                time.sleep(5)
