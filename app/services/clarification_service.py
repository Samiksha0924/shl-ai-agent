class ClarificationService:

    QUESTIONS = {
        "role":
            "Which role are you hiring for?",

        "purpose":
            "Is this for hiring or employee development?",

        "experience_level":
            "Is this for graduates, entry-level, or experienced professionals?",

        "max_duration":
            "Do you have a preferred assessment duration?",

        "audience":
            "Who is this assessment meant for? Please provide the job level, role, or years of experience.",

        "purpose":
            "Is this for hiring or employee development?",
       "max_duration":
            "Do you have a preferred assessment duration?"
            
    
}
    

    def generate(self, missing_fields: list[str]) -> str:

        if not missing_fields:
            return ""

        return self.QUESTIONS.get(
            missing_fields[0],
            "Could you provide a little more information?"
        )