import requests
from config import GEMINI_API_KEY

def compare_players(player1: str, player2: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = (
        "Compare the MLB performance of these two players as of the end of the 2023 season relative to their salaries. "
        "Consider stats like WAR, OPS, ERA, or other relevant metrics. "
        "If the players being compared do not play the same position, explain that this may not be a fair comparison."
        "Explain which player is performing better per dollar of their salary, show this as millions of dollars paid per WAR they provide. "
        "Also compare each player to the average of their position, and make a prediction on their future performance."
        "Provide your response in the format of displaying both players names, relevant stats, and contract values, followed by the WAR per million each player is paid, followed by a summarization of why the stat and pay discrepancies may exist, then conclude with your future performance prediction."
        "If on of the chose players is not a real person, mention that and then treat them as an average player of the same position as the other chosen player."
        "Use current public data only pulled from Baseball-Reference, and be specific with your analysis.\n\n"
        f"Player 1: {player1}\nPlayer 2: {player2}\n\nAnalysis:"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("⚠️ Gemini API error:", e)
        return "Sorry, we couldn't complete the comparison at this time."