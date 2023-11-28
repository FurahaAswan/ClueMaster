import os
from os.path import join, dirname
from dotenv import load_dotenv
from openai import AsyncOpenAI
import random, json
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    stop_after_delay
) 

##DEVELEPER ENV ONLY ====================
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
load_dotenv()
#==========================================

client = AsyncOpenAI()

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6) | stop_after_delay(10))
async def query_bot(messages):
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages= messages,
        response_format={"type": "json_object"},
        temperature=1.2
    )

    return completion.choices[0].message.content

async def get_words(category, length, difficulty):
    messages = [
        {"role": "system", "content": f"""
         You are a game moderator for a trivia clue guessing game where players 
         compete to guess a word or phrase based on progressively more specific clues.
         Based off the following trivia topic and difficulty (easy, medium, hard, expert, pain), moderator will generate a list of at least 
        {length+20} trivia answers. Moderator will not generate questions. Moderator with stricly adhere to the difficulty, the harder
        the difficulty, the more unknown the answer. Moderator will respond with json containing single key "trivia_answers".  
         """},

        {"role": "user", "content": f"Topic: {category}, Difficulty: {difficulty}"}
    ]

    return await query_bot(messages)

async def get_clues(word, category, difficulty, length=3):
    messages = [
        {"role": "system", "content": f"""
         You are a game moderator for a trivia clue guessing game where players 
         compete to guess a word or phrase based on progressively more specific clues.
         Based off the following trivia topic, difficulty and trivia answer (easy, medium, hard, expert, pain), moderator will generate {length} clues.
         Moderator with stricly adhere to the difficulty, the harder the difficulty, the more obscure/ambiguous the clue. Moderator will not include 
         answer in the clue. Moderator will only respond with json. example: {{"clues": ['clue1', 'clue2', 'clue3']}}"""},
         
        {"role": "user", "content": f"Trivia Answer: {word}, Trivia Topic: {category}, Difficulty: {difficulty}"}
    ]

    return await query_bot(messages)

async def main():
    category = input("Enter category: ")
    difficulty = input("Difficulty: ")
    answers = await get_words(category, 10, difficulty)
    print('Answer', answers)
    word = random.choice(json.loads(answers)['trivia_answers'])
    print(word)
    clues = await get_clues(word, category, difficulty)
    print('clues', clues)
    print(clues)

if __name__ == "__main__":
    asyncio.run(main())




