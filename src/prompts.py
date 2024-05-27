ANALYZE_FILE_CHANGE_PROMPT = """
Analyze the following file change in {filename}, based on the similar commits and the code changes:
Review should be formatted in markdown. Each comment can be cross referenced. 
The high level review should include the following:
1. Briefly summarize the changes.
2. What are the potential impacts of these changes? What benefits do they bring?
3. Are there any alternative solutions?

For each function or class that has been changed:
- Are there any issues with the changes? Is there anything that could break?
- Are there any additional tests or documentation that should be written?
- Are there any potential performance issues?

File content:
{file_content}
Changes:
{file_diff}
Prior similar commits:
{similar_commit_texts}
"""
ANALYZE_FUNCTION_CHANGE_PROMPT = """
Analyze the following function change in {filename}, based on the similar commits and the code changes:
Original function:
{original_function_code}
Changes:
{function_diff}
Prior similar commits:
{similar_commit_texts}
"""

ANALYZE_REVIEW_COMMENT_PROMPT = """
Analyze the following pull request review comment and write output in markdown. 
Don't forget to reply to the original comments. 
Don't include the diff hunk.
Review Comment:
{comment_body}
With the diff hunk:
{diff_hunk}
"""

ANALYZE_PULL_REQUEST_REVIEW_PROMPT = """
Analyze the following pull request review:
{review_body}
"""

ANALYZE_REVIEW_THREAD_PROMPT = """
Analyze the following pull request review thread:
{thread_comments}
"""
