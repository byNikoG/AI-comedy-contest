import os
import random
import webbrowser
import difflib
from anthropic import Anthropic
from openai import OpenAI

# Initialize API clients (you'll need to set up your API keys)
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class Contestant:
    def __init__(self, name, role, model):
        self.name = name
        self.role = role
        self.model = model
        self.score = 0

    def tell_joke(self, theme):
        prompt = f"You are {self.name}. {self.role} Tell a joke about {theme}."
        if self.model == "claude-3-sonnet":
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            response = anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                messages=messages
            )
            if response.content:
                return response.content[0].text.strip()
            else:
                return "Claude couldn't generate a joke."
        elif self.model.startswith("gpt"):
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()

class Host:
    def __init__(self):
        self.name = "AIexA Trebek"
        self.role = "A 1980's game show host with zingy one-liners."
        self.used_themes = []

    def introduce(self):
        prompt = f"""You are {self.name}. {self.role} Briefly introduce the AI comedy contest. 
        Include a brief introduction of yourself and the following contestants:
        1. Gepetto (GPT-4): A 1990's stand-up comedian
        2. Chattie (GPT-3.5-turbo): A 1980's comedian known for innuendo-filled one-liners
        3. Claude: A French sarcastic comedian
        Keep it short, concise and entertaining."""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def select_theme(self):
        max_attempts = 5
        similarity_threshold = 0.6

        for _ in range(max_attempts):
            prompt = f"You are {self.name}. {self.role} Suggest a random theme for a comedy contest joke. Be creative and diverse. Respond with just the theme, one to three words maximum."
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            theme = response.choices[0].message.content.strip().lower()

            # Check similarity with previous themes
            if not any(difflib.SequenceMatcher(None, theme, used_theme).ratio() > similarity_threshold for used_theme in self.used_themes):
                self.used_themes.append(theme)
                return theme.capitalize()

        # If we couldn't get a unique theme after max_attempts, use the last generated one
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
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        judgment = response.choices[0].message.content.strip()
        
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
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

def generate_comedy_contest_html():
    host = Host()
    contestants = [
        Contestant("Gepetto", "A 1990's stand-up comedian that tells short funny observational jokes on the theme. No more than four sentences per joke. Make it sound like spoken language with occasional filler-words.", "gpt-4"),
        Contestant("Chattie", "A 1980's comedian telling funny innuendo-filled one-liners on the theme.", "gpt-3.5-turbo"),
        Contestant("Claude", "A french sarcastic comedian telling funny jokes on the theme in french. Start a new paragraph and put an english literal translation of the joke and format it as a separate paragraph.", "claude-3-sonnet")
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
