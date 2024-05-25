import os
from typing import List, Optional
from langchain_core.language_models import LLM
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams


class WatsonxLLM():

    def __init__(self, credentials, model, params, project_id):
        self.credentials = credentials
        self.model = model
        self.params = params
        self.project_id = project_id

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        model_instance = Model(model_id=self.model,
                               params=self.params,
                               credentials=self.credentials,
                               project_id=self.project_id)
        response = model_instance.generate_text(prompt)
        return response


class Backend:

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.watsonx_api_key = os.getenv("WATSONX_API_KEY")
        self.watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
        self.backend = self.choose_backend()

    def choose_backend(self):
        if self.watsonx_api_key:
            credentials = {
                "url": "https://us-south.ml.cloud.ibm.com",
                "apikey": self.watsonx_api_key
            }
            params = {}
            return WatsonxLLM(credentials=credentials,
                              model="mistralai/mixtral-8x7b-instruct-v01",
                              params=params,
                              project_id=self.watsonx_project_id)
        elif self.openai_api_key:
            return LLM(api_key=self.openai_api_key, model_name="gpt-3.5-turbo")
        else:
            raise ValueError(
                "No valid API key found for either OpenAI or WatsonX.")

    def generate(self, prompt):
        return self.backend._call(prompt)


# Example usage
if __name__ == "__main__":
    backend = Backend()
    response = backend.generate(
        "Hello, how are you? please generate a response.")
    print(response)
