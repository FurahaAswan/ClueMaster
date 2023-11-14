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
        messages= messages
    )

    return completion.choices[0].message.content

async def get_words(category, length):
    messages = [
        {"role": "system", "content": """
         You are a game moderator for ClueMaster, a multiplayer online guessing game where players compete to guess a word or phrase based on progressively more specific clues. 
         Based off the following category, you will generate a list of {length} words associated with it. You will only respond with json array contianing the words. Don't include newline characters in your response.
         """},
        {"role": "user", "content": f'Category: {category}'}
    ]

    return await query_bot(messages)

async def get_clues(word):
    messages = [
        {"role": "system", "content": """
         You are a game moderator for ClueMaster, a multiplayer online guessing game where players compete to guess a word or phrase based on progressively more specific clues. 
         Based off the following noun, you will generate 3 progressively easier clues about it. Make sure the first clue is vague, but good enough for a skilled player to guess the noun.
         You will only respond with a single json array example: ['clue1', 'clue2', 'clue3']. Don't include newline characters in your response.
         """},
        {"role": "user", "content": f'Noun: {word}'}
    ]

    return await query_bot(messages)

# async def main():
#     result = await get_clues('Lebron James')
#     print(result)

# if __name__ == "__main__":
#     asyncio.run(main())




