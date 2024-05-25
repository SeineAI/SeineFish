ANALYZE_FILE_CHANGE_PROMPT = """
Analyze the following file change in {filename}:

File content:
{file_content}
Changes:
{file_diff}
"""
ANALYZE_FUNCTION_CHANGE_PROMPT = """
Analyze the following function change in {filename}:
Original function:
{original_function_code}
Changes:
{function_diff}
"""

ANALYZE_REVIEW_COMMENT_PROMPT = """
Analyze the following pull request review comment:
{comment_body}
"""

ANALYZE_PULL_REQUEST_REVIEW_PROMPT = """
Analyze the following pull request review:
{review_body}
"""

ANALYZE_REVIEW_THREAD_PROMPT = """
Analyze the following pull request review thread:
{thread_comments}
"""
