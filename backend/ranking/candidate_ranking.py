def calculate_score(similarity, skill_match, experience):

    score = (
        similarity * 0.5 +
        skill_match * 0.3 +
        experience * 0.2
    )

    return score