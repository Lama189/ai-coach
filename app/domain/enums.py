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


class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class InsightTag(str, Enum):
    injury      = "injury"       # травма, боль, дискомфорт
    progress    = "progress"     # прогресс, личный рекорд
    fatigue     = "fatigue"      # усталость, перетренированность
    preference  = "preference"   # предпочтения, что нравится/не нравится
    schedule    = "schedule"     # расписание, время тренировок
    nutrition   = "nutrition"    # питание, восстановление
    technique   = "technique"    # техника, форма выполнения
    mental      = "mental"       # мотивация, психологическое состояние


class Location(str, Enum):
    gym     = "gym"
    home    = "home"
    outdoor = "outdoor"


class MovementPattern(str, Enum):
    PUSH_HORIZONTAL = "push_horizontal"
    PUSH_VERTICAL = "push_vertical"
    PULL_HORIZONTAL = "pull_horizontal"
    PULL_VERTICAL = "pull_vertical"
    SQUAT = "squat"
    HINGE = "hinge"
    LUNGE = "lunge"
    CARRY = "carry"
    CORE = "core"


class Constraint(str, Enum):
    NO_OVERHEAD = "no_overhead"          
    NO_SHOULDER_LOAD = "no_shoulder_load"
    NO_KNEE_LOAD = "no_knee_load"       
    NO_HINGE = "no_hinge"             
    NO_HORIZONTAL_PRESS = "no_horizontal_press"  
    NO_CARRY = "no_carry"               
    NO_BARBELL = "no_barbell"         