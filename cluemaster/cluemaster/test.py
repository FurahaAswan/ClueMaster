import asyncio

async def my_coroutine():
    for i in range(5):
        print(f"Doing something in iteration {i}")
        await asyncio.sleep(1)
        print(f"Done with iteration {i}")

if __name__ == "__main__":
    asyncio.run(my_coroutine())
