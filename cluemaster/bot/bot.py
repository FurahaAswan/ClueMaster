import os
from os.path import join, dirname
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pathlib import Path
import asyncio

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
load_dotenv()

client = AsyncOpenAI()

async def query_bot(messages):
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages= messages,
        temperature=1.1
    )

    return completion.choices[0].message.content

async def get_words(category, length, difficulty):
    messages = [
        {"role": "system", "content": f"""
         You are a game moderator for ClueMaster, a multiplayer online guessing game where players compete to guess a word or phrase based on progressively more specific clues. 
         Based off the following trivia topic and difficulty, you will generate a list of at least 20 trivia answers. Be sure to strictly adhere to the difficulty and taylor 
         the response to it, do not hold back. The harder the difficulty, the more unknown your response. You will only respond with json containing the answers, use a single key 
         "words". Don't include newline characters in your response."""},
        {"role": "user", "content": f'Topic: {category}, Difficulty: {difficulty}'}
    ]

    return await query_bot(messages)

async def get_clues(word, category, difficulty):
    messages = [
        {"role": "system", "content": f"""
         You are a game moderator for ClueMaster, a multiplayer online guessing game where players compete to guess a word or phrase based on progressively more specific clues. 
         Based off the following noun, category, and difficulty, you will generate 3 progressively easier clues/trivia questions about it. Be sure to strictly adhere to the difficulty and taylor 
         the response to it, do not hold back. The harder the difficulty, the more obscure your response. Under no circumstances will you include the noun in the clue.
         You will only respond with json. example: {{"clues": ['clue1', 'clue2', 'clue3']}}. Don't include newline characters in your response.
         """},
        {"role": "user", "content": f'Noun: {word}, Category: {category}, Difficulty: {difficulty}'}
    ]

    return await query_bot(messages)

async def main():
    result = await get_clues('Gary Trent Jr.', 'NBA Players drafted after the 10th pick', 'Easy')
    print(result)

if __name__ == "__main__":
    asyncio.run(main())




