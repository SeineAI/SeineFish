curl -X POST -H "Content-Type: application/json" -d '{
  "prompt_name": "ANALYZE_FILE_CHANGE_PROMPT",
  "new_prompt": "Analyze the following file change in {filename}:\n\nFile content:\n```python\n{file_content}\n```\n\nChanges:\n```diff\n{file_diff}\n```"
}' http://localhost:8000/update-prompt