import aiohttp
import asyncio
import argparse
import time
from aiofiles import open as aio_open

async def fuzz(session, base_url, wordlist, depth, interactive, visited, semaphore):
    if depth == 0:
        return

    async with aio_open(wordlist, 'r') as words:
        tasks = []
        async for word in words:
            fuzz_dir = f'{base_url}/{word.strip()}'

            if fuzz_dir not in visited:
                visited.add(fuzz_dir)

                async with semaphore:
                    async with session.get(fuzz_dir) as response:
                        status = response.status

                        if status != 404:
                            print(f'status code: {status}')
                            print(await response.json(), fuzz_dir)
                            print()

                            wordlist_placeholder = wordlist
                            if interactive and depth > 1:
                                wordlist = input(f'Provide wordlist for: {base_url}/{word}')
                                print()

                            tasks.append(fuzz(session, fuzz_dir, wordlist, depth-1, interactive, visited, semaphore))
                            wordlist = wordlist_placeholder

        await asyncio.gather(*tasks)

async def main(url, wordlist, depth, interactive):
    base_url = url.rstrip('/')
    visited = set()
    semaphore = asyncio.Semaphore(1000)  # Adjust the limit based on your needs

    connector = aiohttp.TCPConnector(limit=1000)  # Adjust the limit based on your needs
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.perf_counter()
        await fuzz(session, base_url, wordlist, depth, interactive, visited, semaphore)
        end = time.perf_counter()
        print(end - start)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='fuzzer.py',
        description='lightweight python script to recursively fuzz for APIs and print the relevant json. Works recursively up to a user-specified depth')

    parser.add_argument('-u', '--url',
                        help='Specify URL to be fuzzed', required=True)

    parser.add_argument('-w', '--wordlist',
                        help='Specify wordlist for depth 1', required=True)

    parser.add_argument('-d', '--depth', type=int,
                        help='Specify the depth up to which APIs would be crawled', required=True)

    parser.add_argument('-i', '--interactive',
                        action='store_true', help='Allows the option to interactively specify wordlist for each depth', required=False)

    args = parser.parse_args()

    url = args.url
    wordlist = args.wordlist
    depth = args.depth
    interactive = args.interactive

    asyncio.run(main(url, wordlist, depth, interactive))
