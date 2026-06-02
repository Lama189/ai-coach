from enum import Enum


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class FitnessGoal(str, Enum):
    LOSE_WEIGHT = "lose_weight"
    GAIN_MUSCLE = "gain_muscle"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    GENERAL_FITNESS = "general_fitness"


class UserGender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class MuscleGroup(str, Enum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CORE = "core"
    FULL_BODY = "full_body"
    CARDIO = "cardio"