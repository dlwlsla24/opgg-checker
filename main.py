"""
op.gg 게임 접속 감지 -> 디스코드 알림
GitHub Actions에서 5분마다 실행, 또는 로컬에서 직접 실행 가능.

환경변수:
  SUMMONER_NAME  소환사 이름
  TAG            태그라인 (기본: KR1)
  REGION         리전 (기본: kr)
  DISCORD_WEBHOOK_URL  디스코드 웹훅 URL
"""

import os
import json
import requests
from playwright.sync_api import sync_playwright

SUMMONER_NAME = os.environ["SUMMONER_NAME"]
TAG = os.environ.get("TAG", "KR1")
REGION = os.environ.get("REGION", "kr")
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

OPGG_URL = f"https://op.gg/lol/summoners/{REGION}/{SUMMONER_NAME}-{TAG}/ingame"
STATE_FILE = "state.json"


def check_in_game() -> bool:
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(OPGG_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            content = page.text_content("body") or ""
            return "is not in an active game" not in content
        finally:
            browser.close()


def send_discord(message: str):
    resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
    print(f"Discord: {resp.status_code}")


def load_state() -> bool:
    try:
        with open(STATE_FILE) as f:
            return json.load(f).get("was_in_game", False)
    except FileNotFoundError:
        return False


def save_state(in_game: bool):
    with open(STATE_FILE, "w") as f:
        json.dump({"was_in_game": in_game}, f)


def main():
    was_in_game = load_state()
    in_game = check_in_game()

    print(f"이전: {'게임중' if was_in_game else '대기'} -> 현재: {'게임중' if in_game else '대기'}")

    if in_game and not was_in_game:
        send_discord(f"🎮 **{SUMMONER_NAME}#{TAG}** 님이 게임을 시작했습니다!\n{OPGG_URL}")
    elif not in_game and was_in_game:
        send_discord(f"🏁 **{SUMMONER_NAME}#{TAG}** 님의 게임이 종료되었습니다.")

    save_state(in_game)


if __name__ == "__main__":
    main()
