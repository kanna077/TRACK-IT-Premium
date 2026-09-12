"""Deterministic, explainable matching without external paid services."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date

from .models import Item


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a", "an", "and", "are", "at", "for", "from", "in", "is",
    "it", "near", "of", "on", "the", "to", "was", "with",
}


@dataclass(frozen=True)
class MatchResult:
    item: Item
    score: float
    explanation: list[str]


def normalize(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def tokens(value: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(normalize(value))
        if token not in STOP_WORDS
    ]


def item_document(item: Item) -> str:
    return " ".join(
        [
            item.title,
            item.category,
            item.brand,
            item.color,
            item.description,
            item.location,
        ]
    )


def cosine_text_score(left: str, right: str) -> float:
    left_counter = Counter(tokens(left))
    right_counter = Counter(tokens(right))
    if not left_counter or not right_counter:
        return 0.0

    vocabulary = set(left_counter) | set(right_counter)
    dot = sum(
        left_counter[word] * right_counter[word]
        for word in vocabulary
    )
    left_norm = math.sqrt(
        sum(value * value for value in left_counter.values())
    )
    right_norm = math.sqrt(
        sum(value * value for value in right_counter.values())
    )
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def date_score(left: date, right: date) -> float:
    difference = abs((left - right).days)
    if difference <= 1:
        return 1.0
    if difference <= 3:
        return 0.8
    if difference <= 7:
        return 0.5
    if difference <= 14:
        return 0.2
    return 0.0


def exact_score(left: str, right: str) -> float:
    left_value = normalize(left)
    right_value = normalize(right)
    return 1.0 if left_value and left_value == right_value else 0.0


def rank_candidates(
    source: Item,
    candidates: list[Item],
    limit: int = 8,
) -> list[MatchResult]:
    if not candidates:
        return []

    ranked: list[MatchResult] = []
    for candidate in candidates:
        text = cosine_text_score(
            item_document(source),
            item_document(candidate),
        )
        category = exact_score(source.category, candidate.category)
        color = exact_score(source.color, candidate.color)
        brand = exact_score(source.brand, candidate.brand)
        location = exact_score(source.location, candidate.location)
        date_value = date_score(source.event_date, candidate.event_date)

        weighted = (
            text * 0.45
            + category * 0.20
            + color * 0.10
            + brand * 0.08
            + location * 0.10
            + date_value * 0.07
        )

        explanation = []
        if category:
            explanation.append("Same category")
        if color:
            explanation.append("Same color")
        if brand:
            explanation.append("Same brand")
        if location:
            explanation.append("Same location")
        if date_value >= 0.8:
            explanation.append("Reported within 3 days")
        if text >= 0.45:
            explanation.append("Strong description similarity")
        elif text >= 0.2:
            explanation.append("Related description")

        ranked.append(
            MatchResult(
                item=candidate,
                score=round(min(weighted * 100, 100), 2),
                explanation=explanation or ["Low-confidence suggestion"],
            )
        )

    ranked.sort(key=lambda result: result.score, reverse=True)
    return ranked[:limit]
