from bs4 import BeautifulSoup
import csv
import asyncio

from requests.sessions import Session

MAX_RETRIES = 3


def retry_request(max_retries=MAX_RETRIES):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for retry in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    print(f"Retry {retry + 1}/{max_retries} failed.")
                    print(f"Error: {str(e)}")

            raise

        return wrapper

    return decorator


def get_games_list(path: str):
    with open(path, "r") as f:
        urls = [line.strip() for line in f]
        return urls


def get_game_price(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        price_element = soup.find("td", {"class": "price js-price"})
        if price_element:
            return price_element.text.strip()
        else:
            return "0"
    except Exception as e:
        return f"Error: {str(e)}"


def make_csv(games: list[dict[str, str]]):
    with open("games_prices.csv", "w", newline="") as csvfile:
        fieldnames = ["Game", "Price (Euro)", "Link"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for game in games:
            writer.writerow(
                {
                    "Game": game["game"],
                    "Price (Euro)": game["price"],
                    "Link": game["link"],
                }
            )


@retry_request()
async def visit_url(link: str, session: Session):
    try:
        response = await asyncio.to_thread(session.get, link)
        print(f"Visiting {link}...")
        if response.status_code == 200:
            price = get_game_price(response.text)
            game_name = link.split("/")[-1]
            return {"game": game_name, "price": price, "link": link}
        else:
            print(f"Failed to fetch {link}")
    except Exception as e:
        print(f"Failed to visit {link}\nError: {str(e)}")
    return None


async def main():
    tasks = []
    session: Session = Session()
    for link in get_games_list("./games_list.txt"):
        task = asyncio.create_task(visit_url(link, session))
        tasks.append(task)

    games_data: list[dict[str, str]] = await asyncio.gather(*tasks)
    games = [game for game in games_data if game is not None]

    make_csv(games)


if __name__ == "__main__":
    asyncio.run(main())
