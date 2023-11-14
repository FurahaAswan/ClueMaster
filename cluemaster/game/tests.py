from django.test import TestCase
import asyncio

async def print_results(i):
    return print(i)

# Create your tests here.
async def test():
    for i in range(3):
        await print_results(i)
        await print_results(f'{i} #2')

asyncio.run(test())
