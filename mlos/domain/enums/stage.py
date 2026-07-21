from enum import Enum


class Stage(str, Enum):
    PROBLEM_UNDERSTANDING = "Problem Understanding"
    DATA_UNDERSTANDING = "Data Understanding"
    DATA_PREPARATION = "Data Preparation"
    FEATURE_ENGINEERING = "Feature Engineering"
    BASELINE_MODELING = "Baseline Modeling"
    MODEL_IMPROVEMENT = "Model Improvement"
    EVALUATION = "Evaluation"
    COMMUNICATION = "Communication"
    PORTFOLIO_REVIEW = "Portfolio Review"