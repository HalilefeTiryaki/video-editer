import json
import os
from typing import List, Tuple

import httpx


def _format_words(words: List[str]) -> str:
    return ", ".join(words) if words else ""


def template_generator(
    level: str,
    topic: str,
    age_group: str,
    duration: int,
    activity_types: List[str],
    theme_words: List[str],
) -> Tuple[List[str], List[str]]:
    words_hint = _format_words(theme_words)
    activities = ", ".join(activity_types)

    templates = {
        "A1": [
            ("Lücken ausfüllen: ___ heiße Anna.", "Ich heiße Anna."),
            ("Wortschatz: Schreibe 3 Wörter zum Thema '{topic}'.", "Beispiel: Schule, Lehrer, Heft."),
            ("Artikel einsetzen: ___ Haus ist groß.", "Das Haus ist groß."),
            ("Satz ordnen: (geht / die / Schule / in / Ali)", "Ali geht in die Schule."),
            ("Kurze Antwort: Wo wohnst du?", "Ich wohne in ..."),
        ],
        "A2": [
            ("Lücken ausfüllen: ___ Mann ist Lehrer.", "Der Mann ist Lehrer."),
            ("Richtig oder falsch: Ich fahre morgen nach Berlin.", "Richtig."),
            ("Frage bilden: (du / gehen / heute / wohin)", "Wohin gehst du heute?"),
            ("Satz ergänzen: Ich habe ___ Uhr Unterricht.", "Ich habe um acht Uhr Unterricht."),
            ("Wortschatz: Nenne 4 Wörter zu '{topic}'.", "Beispiel: Buch, Stift, Tafel, Klasse."),
        ],
        "B1": [
            ("Satz verbinden: Ich lerne Deutsch. Ich möchte studieren.", "Ich lerne Deutsch, weil ich studieren möchte."),
            ("Lücken ausfüllen: Wenn ich Zeit habe, ___ ich Sport.", "Wenn ich Zeit habe, mache ich Sport."),
            ("Kurztext: Schreibe 3 Sätze über '{topic}'.", "Beispiel: Ich mag ..."),
            ("Wortschatz: Erkläre das Wort '{word}'.", "Beispiel: ..."),
            ("Satz umformen: Ich kann nicht kommen. (wegen)", "Ich kann wegen der Arbeit nicht kommen."),
        ],
        "B2": [
            ("Argumentieren: Nenne zwei Gründe für '{topic}'.", "Beispiel: Erstens ..., zweitens ..."),
            ("Lücken ausfüllen: Obwohl es regnete, ___ wir spazieren.", "Obwohl es regnete, gingen wir spazieren."),
            ("Paraphrase: Formuliere den Satz um: 'Es ist wichtig, Deutsch zu lernen.'", "Deutsch zu lernen ist wichtig."),
            ("Wortschatz: Verwende '{word}' in einem Satz.", "Beispiel: ..."),
            ("Kurztext: Schreibe eine Meinung zu '{topic}'.", "Beispiel: Ich finde, dass ..."),
        ],
    }

    selected = templates.get(level, templates["A1"])
    content: List[str] = []
    solutions: List[str] = []

    question_count = 10 if duration <= 20 else 12 if duration <= 30 else 15
    index = 0
    while len(content) < question_count:
        prompt, solution = selected[index % len(selected)]
        prompt = prompt.format(topic=topic, word=theme_words[index % len(theme_words)] if theme_words else topic)
        solution = solution.format(topic=topic, word=theme_words[index % len(theme_words)] if theme_words else topic)
        content.append(f"{len(content) + 1}) {prompt} [{activities} | {age_group}]".strip())
        solutions.append(f"{len(solutions) + 1}) {solution}")
        index += 1

    if words_hint:
        content.append(f"Hinweis-Wörter: {words_hint}")
        solutions.append(f"Hinweis-Wörter: {words_hint}")

    return content, solutions


def openai_generator(
    level: str,
    topic: str,
    age_group: str,
    duration: int,
    activity_types: List[str],
    theme_words: List[str],
) -> Tuple[List[str], List[str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    prompt = (
        "Erstelle ein DaZ-Arbeitsblatt in einfachem Deutsch. "
        f"Niveau: {level}. Thema: {topic}. Altersgruppe: {age_group}. "
        f"Dauer: {duration} Minuten. Aktivitäten: {', '.join(activity_types)}. "
        f"Wörterliste: {', '.join(theme_words) if theme_words else 'keine'}. "
        "Gib 10-15 nummerierte Aufgaben und danach die Lösungen. "
        "Antwortformat als JSON mit Feldern 'content' und 'solutions' (beide Arrays)."
    )

    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Du bist ein Assistent für DaZ-Arbeitsblätter."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    content_text = data["choices"][0]["message"]["content"]
    parsed = json.loads(content_text)
    return parsed["content"], parsed["solutions"]
