import os
import random
import webbrowser
import difflib
from anthropic import Anthropic
from openai import OpenAI
from huggingface_hub import InferenceClient

# Initialize API clients (you'll need to set up your API keys)
client_anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
client_gpt = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
client_llama = InferenceClient(token=os.environ.get("HUGGINGFACE_TOKEN"))

def generate_gpt_response(prompt, model="gpt-4", max_tokens=300):
    try:
        response = client_gpt.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating GPT response: {str(e)}"

def generate_claude_response(prompt, model="claude-3-sonnet-20240229", max_tokens=300):
    try:
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        response = client_anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages
        )
        if response.content:
            return response.content[0].text.strip()
        else:
            return "Claude couldn't generate a response."
    except Exception as e:
        return f"Error generating Claude response: {str(e)}"

def generate_llama_response(prompt, max_length=100):
    try:
        response = client_llama.text_generation(
            prompt,
            model="meta-llama/Llama-2-7b-chat-hf",
            max_new_tokens=max_length,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
        )
        
        if not response:
            return "Llama couldn't generate a joke."
        
        if isinstance(response, str):
            return response.strip()
        
        if hasattr(response, 'generated_text'):
            return response.generated_text.strip()
        
        return "Error: Unexpected response format from Llama."
    
    except Exception as e:
        return f"Error generating Llama response: {str(e)}"

class Contestant:
    def __init__(self, name, role, model):
        self.name = name
        self.role = role
        self.model = model
        self.score = 0

    def tell_joke(self, theme):
        prompt = f"You are {self.name}. {self.role} Tell a joke about {theme}."
        if self.model.startswith("claude"):
            return generate_claude_response(prompt, self.model)
        elif self.model.startswith("gpt"):
            return generate_gpt_response(prompt, self.model)
        elif self.model == "llama":
            return generate_llama_response(prompt)

class Host:
    def __init__(self):
        self.name = "AIexA Trebek"
        self.role = "A 1980's game show host with zingy one-liners."
        self.used_themes = []

    def introduce(self):
        prompt = f"""You are {self.name}. {self.role} Introduce the AI comedy contest. 
        Include a brief introduction of yourself and the following contestants:
        1. Gepetto: A 1990's stand-up comedian
        2. Chattie: A 1980's comedian known for innuendo-filled one-liners
        3. Claude: A French sarcastic comedian
        4. Llama: A witty AI comedian with a penchant for wordplay and clever observations
        Keep it concise and entertaining."""
        return generate_gpt_response(prompt)

    def select_theme(self):
        max_attempts = 5
        similarity_threshold = 0.6

        for _ in range(max_attempts):
            prompt = f"You are {self.name}. {self.role} Suggest a random theme for a comedy contest joke. Be creative and diverse. Respond with just the theme, one to three words maximum."
            theme = generate_gpt_response(prompt).lower()

            if not any(difflib.SequenceMatcher(None, theme, used_theme).ratio() > similarity_threshold for used_theme in self.used_themes):
                self.used_themes.append(theme)
                return theme.capitalize()

        return theme.capitalize()

    def judge_joke(self, joke, theme):
        prompt = f"""You are {self.name}. {self.role} Judge this joke on the theme '{theme}' using the following criteria:
        1. Overall (1-10)
        2. Humor (1-10)
        3. Relevance to theme (1-10)
        4. Creativity (1-10)
        
        Provide a very short comment after the scores.
        
        Joke: {joke}
        
        Respond in this format:
        Overall: [score]
        Humor: [score]
        Relevance: [score]
        Creativity: [score]
        Comment: [Your brief comment]
        """
        judgment = generate_gpt_response(prompt)
        
        # Extract scores and comment from judgment
        import re
        scores = {}
        for category in ['Overall', 'Humor', 'Relevance', 'Creativity']:
            match = re.search(rf'{category}: (\d+)', judgment)
            scores[category.lower()] = int(match.group(1)) if match else 5
        
        comment_match = re.search(r'Comment: (.+)$', judgment, re.MULTILINE)
        comment = comment_match.group(1) if comment_match else "No comment provided."
        
        return scores, comment

    def declare_winner(self, contestants):
        winner = max(contestants, key=lambda x: x.score)
        prompt = f"You are {self.name}. {self.role} Declare {winner.name} as the winner of the comedy contest and give a short outro."
        return generate_gpt_response(prompt)

def generate_comedy_contest_html():
    host = Host()
    contestants = [
        Contestant("Gepetto", "A 1990's stand-up comedian that tells short funny observational jokes on the theme. No more than four sentences per joke. Make it sound like spoken language with occasional filler-words.", "gpt-4"),
        Contestant("Chattie", "A 1980's comedian telling funny innuendo-filled one-liners on the theme.", "gpt-3.5-turbo"),
        Contestant("Claude", "A french sarcastic comedian telling funny jokes in french. The jokes should be on the theme. Put an english literal translation after the joke and format it as a separate paragraph.", "claude-3-sonnet-20240229"),
        Contestant("Llama", "A witty AI comedian with a penchant for wordplay and clever observations.", "llama")
    ]

    intro = host.introduce()
    rounds = []

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Comedy Contest</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .joke {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
            .host {{ font-style: italic; color: #0066cc; }}
            .host-name {{ font-weight: bold; color: #0066cc; }}
            .scores {{ margin-bottom: 10px; }}
            .scores p {{ margin: 5px 0; }}
            .judgment {{ font-style: italic; color: #666; }}
        </style>
    </head>
    <body>
        <h1>AI Comedy Contest</h1>
        <p class="host"><span class="host-name">{host.name}:</span> {intro}</p>
    """

    for _ in range(3):
        theme = host.select_theme()
        html += f'<p class="host"><span class="host-name">{host.name}:</span> Our theme for this round is: {theme}</p>'
        round_jokes = []
        for contestant in contestants:
            joke = contestant.tell_joke(theme)
            scores, comment = host.judge_joke(joke, theme)
            contestant.score += scores['overall']
            round_jokes.append({
                "contestant": contestant.name,
                "joke": joke,
                "scores": scores,
                "comment": comment
            })
        rounds.append({"theme": theme, "jokes": round_jokes})

    for round in rounds:
        html += f"""
        <h2>Round: {round['theme']}</h2>
        """
        for joke in round['jokes']:
            html += f"""
            <h3>{joke['contestant']}</h3>
            <div class="joke">{joke['joke']}</div>
            <div class="scores">
                <p>Overall: {joke['scores']['overall']}</p>
                <p>Humor: {joke['scores']['humor']}</p>
                <p>Relevance: {joke['scores']['relevance']}</p>
                <p>Creativity: {joke['scores']['creativity']}</p>
            </div>
            <p class="host"><span class="host-name">{host.name}:</span> {joke['comment']}</p>
            """

    outro = host.declare_winner(contestants)
    html += f"""
        <p class="host"><span class="host-name">{host.name}:</span> {outro}</p>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    contest_html = generate_comedy_contest_html()
    
    # Create an HTML file
    with open("comedy_contest.html", "w", encoding="utf-8") as f:
        f.write(contest_html)
    
    # Open the HTML file in the default web browser
    webbrowser.open('file://' + os.path.realpath("comedy_contest.html"))
