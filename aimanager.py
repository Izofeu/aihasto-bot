from google import genai
from google.genai import types

class aimanager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.aiclient = genai.Client(api_key = self.cfg.loadtoken(self.cfg.get("aitokenfile")))
        
    def generateprompt(self, context, prompt):
        response = self.aiclient.models.generate_content(
            model = "gemini-2.0-flash",
            contents = prompt,
            config = types.GenerateContentConfig(
                max_output_tokens = 1200,
                safety_settings = [
                    types.SafetySetting(
                        category = "HARM_CATEGORY_HARASSMENT",
                        threshold = "BLOCK_LOW_AND_ABOVE",
                    ),
                    types.SafetySetting(
                        category = "HARM_CATEGORY_HATE_SPEECH",
                        threshold = "BLOCK_LOW_AND_ABOVE",
                    ),
                    types.SafetySetting(
                        category = "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold = "BLOCK_LOW_AND_ABOVE",
                    ),
                    types.SafetySetting(
                        category = "HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold = "BLOCK_LOW_AND_ABOVE",
                    ),
                    types.SafetySetting(
                        category = "HARM_CATEGORY_CIVIC_INTEGRITY",
                        threshold = "BLOCK_LOW_AND_ABOVE",
                    )
                    ]
                )
            )
        return response
        
    def generatepromptnosafety(self, context, prompt):
        response = self.aiclient.models.generate_content(
            model = "gemini-2.0-flash",
            contents = prompt,
            config = types.GenerateContentConfig(
                max_output_tokens = 1000
                )
            )
        return response