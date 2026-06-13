from enum import Enum

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


class InsightTag(str, Enum):
    injury     = "injury"
    progress   = "progress"
    fatigue    = "fatigue"
    preference = "preference"
    schedule   = "schedule"
    nutrition  = "nutrition"
    technique  = "technique"
    mental     = "mental"


INSIGHT_TAG_LABELS: dict[InsightTag, str] = {
    InsightTag.injury:     "🤕 Травма / Боль",
    InsightTag.progress:   "📈 Прогресс",
    InsightTag.fatigue:    "😴 Усталость",
    InsightTag.preference: "❤️ Предпочтения",
    InsightTag.schedule:   "📅 Расписание",
    InsightTag.nutrition:  "🍎 Питание",
    InsightTag.technique:  "🏋️ Техника",
    InsightTag.mental:     "🧠 Ментальное",
}


def get_insight_tag_keyboard() -> ReplyKeyboardMarkup:
    tags = list(INSIGHT_TAG_LABELS.values())

    keyboard = [
        [KeyboardButton(text=tags[i]), KeyboardButton(text=tags[i + 1])]
        for i in range(0, len(tags), 2)
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )
