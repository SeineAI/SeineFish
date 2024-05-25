from dataclasses import dataclass


@dataclass
class Options:
    github_token: str
    openai_api_key: str
    watsonx_api_key: str
    watsonx_project_id: str
    github_repository: str
    github_event_path: str
    github_event_name: str
