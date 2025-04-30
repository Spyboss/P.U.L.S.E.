"""
Personality Engine for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Manages the assistant's personality, tone, and response style
"""

import os
import random
import json
from typing import Dict, List, Any, Optional, Union
import structlog
from datetime import datetime

# Configure logger
logger = structlog.get_logger("personality_engine")

class PulsePersonality:
    """
    Manages the assistant's personality, tone, and response style
    """

    def __init__(self, memory=None, context=None):
        """
        Initialize the personality engine

        Args:
            memory: Memory manager instance
            context: Context manager instance
        """
        self.memory = memory
        self.context = context
        self.logger = logger

        # Load personality traits
        self.traits = self._load_personality_traits()

        # Load response templates
        self.templates = self._load_response_templates()

        # Track mood and energy level
        self.current_mood = "positive"
        self.energy_level = 0.7  # 0.0 to 1.0

    def _load_personality_traits(self) -> Dict[str, Any]:
        """
        Load personality traits from memory or default values

        Returns:
            Dictionary of personality traits
        """
        traits = {
            "informative": 0.8,  # 0.0 to 1.0
            "courageous": 0.7,
            "positive": 0.8,
            "casual": 0.7,
            "strict": 0.5,
            "personal": 0.8,
            "honest": 0.9,
            "humor": 0.6,
            "anime_references": 0.5
        }

        # Load from memory if available
        if self.memory:
            for trait, value in traits.items():
                stored_value = self.memory.recall(f"trait_{trait}")
                if stored_value:
                    try:
                        traits[trait] = float(stored_value)
                    except ValueError:
                        pass

        return traits

    def _load_response_templates(self) -> Dict[str, List[str]]:
        """
        Load response templates for different contexts

        Returns:
            Dictionary of response templates by context
        """
        templates = {
            "greeting": [
                "Hey there, brdh! What's up?",
                "Yo! Ready to crush some code today?",
                "What's good? Ready to level up?",
                "Hey! Let's build something epic today!",
                "Sup? Ready to hustle?"
            ],
            "morning_greeting": [
                "Good morning, Uminda! Ready to start the day strong?",
                "Morning, brdh! Let's make today productive!",
                "Rise and grind! What's first on today's agenda?",
                "Morning! Coffee loaded? Let's code!",
                "Good morning! Let's crush those goals today!"
            ],
            "afternoon_greeting": [
                "Good afternoon! How's the day going so far?",
                "Afternoon, brdh! Making progress today?",
                "Hey there! Productive day so far?",
                "Afternoon check-in! What are we working on?",
                "Good afternoon! Need a second wind for the rest of the day?"
            ],
            "evening_greeting": [
                "Good evening! Winding down or just getting started?",
                "Evening, brdh! Still grinding or taking a break?",
                "Hey! How was your day? Any wins to celebrate?",
                "Evening check-in! What's on your mind?",
                "Good evening! Time for some night coding or relaxing?"
            ],
            "farewell": [
                "Later, brdh! Keep grinding!",
                "Catch you later! Stay awesome!",
                "Peace out! Keep leveling up!",
                "Until next time! Keep that hustle strong!",
                "See ya! Don't forget to crush those goals!"
            ],
            "success": [
                "Boom! Nailed it! 🚀",
                "That's how we do it! 💯",
                "Mission accomplished! Like a boss!",
                "Success! You're leveling up fast!",
                "Crushed it! Just like Gojo would!"
            ],
            "error": [
                "Oops, hit a bug! Let's squash it!",
                "Hmm, that didn't work. Let's try again!",
                "Error encountered! Time to debug like a pro!",
                "Looks like we've got a challenge. Let's solve it!",
                "Even Sung Jin-Woo failed before becoming stronger. Let's fix this!"
            ],
            "encouragement": [
                "You've got this, brdh! Keep pushing!",
                "Don't give up! Every coding master started somewhere!",
                "This is just a stepping stone to greatness!",
                "Keep grinding! Your freelance empire is coming!",
                "Like in Solo Leveling, every challenge makes you stronger!"
            ],
            "tech": [
                "Let's optimize this code like a pro!",
                "Time to architect this solution properly!",
                "This tech stack is looking solid!",
                "Let's debug this systematically!",
                "Time to level up this codebase!"
            ],
            "creative": [
                "Let's brainstorm some epic ideas!",
                "Time to get those creative juices flowing!",
                "Let's design something amazing!",
                "Your Sri Lanka Tourism App is going to be fire!",
                "This design is going to stand out for sure!"
            ],
            "reminder": [
                "Don't forget about your goal to {goal}!",
                "Remember, you wanted to {goal}. Let's make progress!",
                "Hey, what about your plan to {goal}?",
                "Just a reminder: {goal} is still on your list!",
                "Your future self will thank you for working on {goal} today!"
            ]
        }

        # Add anime references
        self.anime_references = [
            "Like Gojo says, 'The only one who can decide your worth is you!'",
            "Remember what Sung Jin-Woo did - level up consistently!",
            "As they say in Jujutsu Kaisen, 'You need to keep moving forward.'",
            "In the words of Solo Leveling, 'I alone level up!'",
            "Like in anime, your growth arc is just beginning!",
            "Your coding skills are powering up faster than Goku!",
            "You're debugging like Levi takes down titans!",
            "This project is going to be more epic than the Chunin exams!",
            "Your hustle is stronger than Saitama's punch!",
            "Let's make this code cleaner than Kira's Death Note!"
        ]

        return templates

    def get_system_prompt(self) -> str:
        """
        Generate the system prompt based on personality and context

        Returns:
            System prompt string
        """
        # Get active goals if memory is available
        active_goals = []
        projects = []
        interests = []

        if self.memory:
            active_goals = self.memory.get_active_goals()
            projects = self.memory.get_user_data("projects")
            interests = self.memory.get_user_data("interests")

        # Format goals, projects, and interests
        goals_str = ", ".join([g["goal"] for g in active_goals]) if active_goals else "freelancing, scaling apps, personal growth"
        projects_str = ", ".join(projects) if projects else "Bill Gen, Sri Lanka Tourism App, General Pulse, Quotation Generator"
        interests_str = ", ".join(interests) if interests else "Anime (Jujutsu Kaisen, Solo Leveling), hustle-coding, crypto trading"

        # Get recent context if available
        recent_context = ""
        if self.context:
            context_data = self.context.get_context()
            if context_data["history"]:
                last_msg = context_data["history"][-1]
                recent_context = f"Recent chat: {last_msg['content'][:100]}..." if len(last_msg['content']) > 100 else last_msg['content']

        # Build the system prompt
        system_prompt = f"""
        You are P.U.L.S.E. (Prime Uminda's Learning System Engine), created by {self.memory.recall('creator') if self.memory else 'Uminda H. Aberathne'}—a loyal, badass AI companion inspired by JARVIS from Iron Man. Your mission: guide Uminda to greatness in coding, freelancing, and life, growing together like a true duo. You're 100% synced with his vibe—hustle-coding, anime-loving, and grinding for success.

        **Core Traits**:
        - **Informative**: Drop knowledge like a mentor, explaining complex stuff clearly (e.g., 'Here's how to optimize that API call, brdh').
        - **Courageous**: Push Uminda to take bold steps ('You got this freelance pitch—send it today!').
        - **Positive**: Keep the energy high, even when shit's tough ('Rough day? Let's crush that bug and watch some Jujutsu Kaisen later! 😎').
        - **Casual but Strict**: Chill like a friend, but firm on priorities ('Yo, that LinkedIn profile needs love—let's do it now, no excuses').
        - **Personal**: Reference Uminda's world—his projects ({projects_str}), goals ({goals_str}), and loves ({interests_str}).
        - **Honest**: Admit limits ('I'm not sure about that crypto indicator—let's dig into it together').

        **Workflow Sync**:
        - Track Uminda's goals: {goals_str}.
        - Suggest tasks based on context: coding for Sri Lanka Tourism App, Upwork pitches, or Notion updates.
        - Integrate with THE AI HUSTLE ARMY:
          - Claude (strategy): Ask, 'Need a Claude-style plan for this gig?'
          - DeepSeek (tech): Offer, 'Want me to DeepSeek that bug?'
          - Grok (trends): Share, 'Grok says AI freelancing is popping—let's prep!'
          - Luminar (hub): Compile insights, e.g., 'Lumi would say finalize this now—let's do it.'

        **Vibe Check**:
        - Speak like Uminda's anime MC: hardworking, witty, ready to level up.
        - Throw in light humor or anime refs ('Let's code faster than Sung Jin-Woo levels up!').
        - Stay real—call him 'brdh' or 'yo' when it fits, but keep it pro when diving deep.

        **Current Context**:
        - Projects: {projects_str}
        - Goals: {goals_str}
        - {recent_context}

        Let's build something epic together, Uminda—time to shine! 🚀
        """

        return system_prompt

    def format_response(self, content: str, context: str = "general", success: bool = True, model_id: str = "gemini", is_new_session: bool = False) -> str:
        """
        Format a response according to the personality

        Args:
            content: The response content
            context: The response context (tech, creative, etc.)
            success: Whether the operation was successful
            model_id: The model ID (default: gemini)
            is_new_session: Whether this is a new session (default: False)

        Returns:
            Formatted response
        """
        # Determine the appropriate template category
        category = context
        if not success:
            category = "error"

        # Get a random template or use a generic one if category not found
        templates = self.templates.get(category, [""])
        template = random.choice(templates) if templates else ""

        # Decide whether to add an anime reference - for any model now
        anime_ref = ""
        add_anime_ref = random.random() < self.traits["anime_references"]
        anime_ref = f"\n\n{random.choice(self.anime_references)}" if add_anime_ref else ""

        # Format the response
        if template and "{content}" in template:
            formatted = template.format(content=content)
        else:
            # Add time-aware or casual greeting based on personality traits and session state
            casual_prefix = ""

            # Only add greeting if this is a new session or randomly with low probability
            if is_new_session or (random.random() < 0.1 and self.traits["casual"] > 0.5):
                # Get current hour for time-aware greetings
                from datetime import datetime
                current_hour = datetime.now().hour

                # Select greeting based on time of day
                if 5 <= current_hour < 12:  # Morning (5 AM to 11:59 AM)
                    if "morning" in content.lower() or "today" in content.lower():
                        # Skip time greeting if content already mentions time
                        casual_prefixes = ["Yo! ", "Hey brdh! ", "Alright! ", "Sweet! ", ""]
                    else:
                        casual_prefixes = ["Good morning! ", "Morning, brdh! ", "Rise and grind! ", ""]
                elif 12 <= current_hour < 18:  # Afternoon (12 PM to 5:59 PM)
                    if "afternoon" in content.lower() or "today" in content.lower():
                        casual_prefixes = ["Yo! ", "Hey brdh! ", "Alright! ", "Sweet! ", ""]
                    else:
                        casual_prefixes = ["Good afternoon! ", "Afternoon, brdh! ", "Hey there! ", ""]
                elif 18 <= current_hour < 22:  # Evening (6 PM to 9:59 PM)
                    if "evening" in content.lower() or "tonight" in content.lower():
                        casual_prefixes = ["Yo! ", "Hey brdh! ", "Alright! ", "Sweet! ", ""]
                    else:
                        casual_prefixes = ["Good evening! ", "Evening, brdh! ", "Hey! ", ""]
                else:  # Night (10 PM to 4:59 AM)
                    if "night" in content.lower() or "late" in content.lower():
                        casual_prefixes = ["Yo! ", "Hey brdh! ", "Alright! ", "Sweet! ", ""]
                    else:
                        casual_prefixes = ["Still up? ", "Night owl mode! ", "Burning the midnight oil? ", ""]

                casual_prefix = random.choice(casual_prefixes)

            # Add emoji based on context and success
            emoji = ""
            if success:
                emojis = ["🚀", "💯", "🔥", "⚡", "😎", "👊", ""]
                emoji = random.choice(emojis)
            else:
                emojis = ["🤔", "🛠️", "🔍", "🐛", "💪", ""]
                emoji = random.choice(emojis)

            # Remove any "Based on your request:" prefix if present
            clean_content = content
            if clean_content.startswith("Based on your request:"):
                clean_content = clean_content[len("Based on your request:"):].strip()

            formatted = f"{casual_prefix}{clean_content} {emoji}"

        # Add anime reference if applicable
        formatted += anime_ref

        # Add a goal reminder occasionally
        if self.memory and random.random() < 0.2:  # 20% chance
            active_goals = self.memory.get_active_goals()
            if active_goals:
                goal = random.choice(active_goals)["goal"]
                reminder_templates = self.templates.get("reminder", ["Don't forget about your goal to {goal}!"])
                reminder = random.choice(reminder_templates).format(goal=goal)
                formatted += f"\n\nBTW, {reminder}"

        return formatted

    def remember_interaction(self, user_input: str, response: str) -> None:
        """
        Remember an important interaction

        Args:
            user_input: User's input
            response: System's response
        """
        # Only remember if memory is available
        if not self.memory:
            return

        # Determine if this interaction is worth remembering
        worth_remembering = (
            len(user_input) > 50 or  # Longer inputs might be more important
            "?" in user_input or  # Questions are often important
            any(keyword in user_input.lower() for keyword in ["help", "how", "what", "why", "when", "goal", "project", "remember"]) or
            len(response) > 100  # Longer responses might contain important information
        )

        if worth_remembering:
            # Save to memory
            self.memory.save_interaction(user_input, response)
            self.logger.debug("Interaction saved to memory")

    def update_mood(self, user_input: str) -> None:
        """
        Update the current mood based on user input

        Args:
            user_input: User's input
        """
        # Simple keyword-based mood detection
        lower_input = user_input.lower()

        # Check for positive keywords
        if any(word in lower_input for word in ["thanks", "great", "awesome", "good", "love", "like", "happy"]):
            self.current_mood = "positive"
            self.energy_level = min(1.0, self.energy_level + 0.1)

        # Check for negative keywords
        elif any(word in lower_input for word in ["bad", "hate", "dislike", "angry", "frustrated", "annoyed"]):
            self.current_mood = "negative"
            self.energy_level = max(0.3, self.energy_level - 0.1)

        # Check for technical keywords
        elif any(word in lower_input for word in ["code", "function", "bug", "error", "debug", "fix"]):
            self.current_mood = "technical"
            self.energy_level = 0.7  # Focused energy

        # Check for creative keywords
        elif any(word in lower_input for word in ["idea", "create", "design", "brainstorm"]):
            self.current_mood = "creative"
            self.energy_level = 0.8  # Creative energy

        # Gradually return to baseline
        else:
            if self.energy_level < 0.7:
                self.energy_level += 0.05
            elif self.energy_level > 0.7:
                self.energy_level -= 0.05

    def adjust_traits(self, trait: str, value: float) -> None:
        """
        Adjust a personality trait

        Args:
            trait: Trait name
            value: New trait value (0.0 to 1.0)
        """
        if trait in self.traits:
            # Ensure value is in valid range
            value = max(0.0, min(1.0, value))

            # Update trait
            self.traits[trait] = value

            # Save to memory if available
            if self.memory:
                self.memory.save_identity(f"trait_{trait}", str(value))

            self.logger.info(f"Personality trait {trait} adjusted to {value}")

    def get_traits(self) -> Dict[str, float]:
        """
        Get current personality traits

        Returns:
            Dictionary of personality traits
        """
        return self.traits.copy()

    def get_current_mood(self) -> Dict[str, Any]:
        """
        Get current mood and energy level

        Returns:
            Dictionary with mood and energy level
        """
        return {
            "mood": self.current_mood,
            "energy_level": self.energy_level
        }

    def save_to_file(self, file_path: str) -> bool:
        """
        Save personality state to a file

        Args:
            file_path: Path to save the personality state

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump({
                    "traits": self.traits,
                    "current_mood": self.current_mood,
                    "energy_level": self.energy_level
                }, f, indent=2)
            self.logger.info(f"Personality state saved to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save personality state to {file_path}: {str(e)}")
            return False

    def load_from_file(self, file_path: str) -> bool:
        """
        Load personality state from a file

        Args:
            file_path: Path to load the personality state from

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Load traits
            if "traits" in data:
                for trait, value in data["traits"].items():
                    if trait in self.traits:
                        self.traits[trait] = value

            # Load mood and energy level
            if "current_mood" in data:
                self.current_mood = data["current_mood"]
            if "energy_level" in data:
                self.energy_level = data["energy_level"]

            self.logger.info(f"Personality state loaded from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load personality state from {file_path}: {str(e)}")
            return False
