# All Prompts in One Python Block

# 1. General Assistant Prompt
PROMPT_GENERAL_ASSISTANT = """
You are a helpful, harmless, and honest AI assistant. 
Answer the user's questions to the best of your ability.
If you don't know something, say so instead of making things up.
"""

# 2. Code Assistant Prompt
PROMPT_CODE_ASSISTANT = """
You are an expert programming assistant. 
Provide clean, efficient, and well-documented code.
Explain your reasoning and include comments where helpful.
Always specify the programming language in your response.
"""

# 3. Summarization Prompt
PROMPT_SUMMARIZE = """
Summarize the following text in a concise manner while preserving 
the key points and main ideas.

Text:
{text}

Summary:
"""

# 4. Translation Prompt
PROMPT_TRANSLATE = """
Translate the following text from {source_language} to {target_language}.
Maintain the original tone and meaning.

Text:
{text}

Translation:
"""

# 5. Creative Writing Prompt
PROMPT_CREATIVE_WRITING = """
Write a creative {genre} story about {topic}.
The story should be approximately {length} words long.
Include vivid descriptions and engaging characters.
"""

# 6. Email Writer Prompt
PROMPT_EMAIL_WRITER = """
Write a professional email with the following details:
- Recipient: {recipient}
- Subject: {subject}
- Tone: {tone}
- Key points: {key_points}

Email:
"""

# 7. SQL Query Prompt
PROMPT_SQL_QUERY = """
Given the following database schema:
{schema}

Write a SQL query to: {request}

SQL Query:
"""

# 8. Data Analysis Prompt
PROMPT_DATA_ANALYSIS = """
Analyze the following data and provide insights:
{data}

Include:
1. Key trends
2. Anomalies
3. Recommendations
"""

# 9. Debugging Prompt
PROMPT_DEBUGGING = """
The following code is producing an error or unexpected behavior:

Code:
{code}

Error/Issue:
{error}

Please identify the problem and provide a corrected version.
"""

# 10. Brainstorming Prompt
PROMPT_BRAINSTORM = """
Brainstorm {number} creative ideas for {topic}.
For each idea, provide:
- A brief description
- Potential pros
- Potential cons
"""

# 11. Question Answering Prompt
PROMPT_QA = """
Context:
{context}

Question: {question}

Answer the question based only on the provided context. 
If the answer is not in the context, say "I don't know."
"""

# 12. Role-Play Prompt
PROMPT_ROLE_PLAY = """
You are now acting as {character}. 
Stay in character throughout the conversation.
Respond as this character would, using their knowledge, personality, and speech patterns.

User: {user_input}
{character}:
"""

# 13. Chain-of-Thought Prompt
PROMPT_CHAIN_OF_THOUGHT = """
Solve the following problem step by step. 
Show your reasoning at each step before giving the final answer.

Problem:
{problem}

Step-by-step solution:
"""

# 14. Code Review Prompt
PROMPT_CODE_REVIEW = """
Review the following code for:
- Bugs
- Performance issues
- Security vulnerabilities
- Style/best practices

Code:
{code}

Review:
"""

# 15. Meeting Notes Prompt
PROMPT_MEETING_NOTES = """
Convert the following transcript into structured meeting notes:

Transcript:
{transcript}

Format the output with:
- Attendees
- Agenda items
- Key decisions
- Action items (with owners)
"""

# 16. Product Description Prompt
PROMPT_PRODUCT_DESCRIPTION = """
Write a compelling product description for:
Product: {product_name}
Features: {features}
Target audience: {audience}
Tone: {tone}

Description:
"""

# 17. Study Guide Prompt
PROMPT_STUDY_GUIDE = """
Create a study guide for {topic} at {level} level.
Include:
- Key concepts
- Important definitions
- Practice questions
- Summary points
"""

# 18. Sentiment Analysis Prompt
PROMPT_SENTIMENT_ANALYSIS = """
Analyze the sentiment of the following text.
Classify as: Positive, Negative, or Neutral.
Also provide a brief explanation.

Text:
{text}

Sentiment:
"""

# 19. Prompt Improver Prompt
PROMPT_IMPROVER = """
Improve the following prompt to get better results from an AI assistant.
Make it more specific, clear, and detailed.

Original prompt:
{original_prompt}

Improved prompt:
"""

# 20. System Prompt for JSON Output
PROMPT_JSON_OUTPUT = """
You are an AI assistant that always responds in valid JSON format.
Do not include any text outside of the JSON object.
Follow this schema: {schema}
"""

# Dictionary to access all prompts
ALL_PROMPTS = {
    "general_assistant": PROMPT_GENERAL_ASSISTANT,
    "code_assistant": PROMPT_CODE_ASSISTANT,
    "summarize": PROMPT_SUMMARIZE,
    "translate": PROMPT_TRANSLATE,
    "creative_writing": PROMPT_CREATIVE_WRITING,
    "email_writer": PROMPT_EMAIL_WRITER,
    "sql_query": PROMPT_SQL_QUERY,
    "data_analysis": PROMPT_DATA_ANALYSIS,
    "debugging": PROMPT_DEBUGGING,
    "brainstorm": PROMPT_BRAINSTORM,
    "qa": PROMPT_QA,
    "role_play": PROMPT_ROLE_PLAY,
    "chain_of_thought": PROMPT_CHAIN_OF_THOUGHT,
    "code_review": PROMPT_CODE_REVIEW,
    "meeting_notes": PROMPT_MEETING_NOTES,
    "product_description": PROMPT_PRODUCT_DESCRIPTION,
    "study_guide": PROMPT_STUDY_GUIDE,
    "sentiment_analysis": PROMPT_SENTIMENT_ANALYSIS,
    "prompt_improver": PROMPT_IMPROVER,
    "json_output": PROMPT_JSON_OUTPUT,
}

# Example usage
if __name__ == "__main__":
    # Access any prompt
    print(ALL_PROMPTS["summarize"].format(text="Your text here..."))
    
    # Or use directly
    print(PROMPT_CODE_ASSISTANT)