from groq import Groq

from app.core.config import get_settings


class GroqClient:

    def __init__(self):

        settings = get_settings()

        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )

        self.model = settings.MODEL_NAME

    def chat(self, system_prompt: str, user_prompt: str):

        response = self.client.chat.completions.create(

            model=self.model,

            temperature=0,

            response_format={
                "type": "json_object"
            },

            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return response.choices[0].message.content