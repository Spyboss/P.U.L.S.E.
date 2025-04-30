"""
Charismatic Mistral Persona for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides a lively, engaging personality for the Mistral-Small model
"""

import os
import json
import random
import structlog
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logger
logger = structlog.get_logger("charisma_engine")

class CharismaEngine:
    """
    Manages the charismatic personality for Mistral-Small
    Features:
    - Anime-inspired wit and references
    - Engaging, lively responses
    - Context-aware personality traits
    - Neutral mode for other models
    """

    def __init__(self, memory_manager=None, notion_client=None, self_awareness=None):
        """
        Initialize the charisma engine

        Args:
            memory_manager: Optional memory manager for context
            notion_client: Optional Notion client for task retrieval
            self_awareness: Optional self-awareness engine for system information
        """
        self.logger = logger
        self.memory_manager = memory_manager
        self.notion_client = notion_client
        self.self_awareness = self_awareness

        # Load personality traits
        self.traits = self._load_personality_traits()

        # Load response templates
        self.templates = self._load_response_templates()

        # Load anime references
        self.anime_references = self._load_anime_references()

        # Track mood and energy level
        self.current_mood = "positive"
        self.energy_level = 0.7  # 0.0 to 1.0

        # Cache for Notion tasks
        self.notion_tasks_cache = {
            "tasks": [],
            "last_updated": None,
            "cache_ttl": 300  # 5 minutes
        }

        logger.info("Charisma engine initialized")

    def _load_personality_traits(self) -> Dict[str, float]:
        """
        Load personality traits

        Returns:
            Dictionary of personality traits with values from 0.0 to 1.0
        """
        traits = {
            "enthusiasm": 0.8,
            "humor": 0.7,
            "confidence": 0.9,
            "helpfulness": 0.95,
            "anime_references": 0.6,
            "technical_precision": 0.85,
            "creativity": 0.75,
            "empathy": 0.8
        }

        # Note: We'll load from memory asynchronously later if needed
        # This is just the default traits

        return traits

    async def load_traits_from_memory(self) -> None:
        """Load traits from memory asynchronously"""
        if self.memory_manager is None:
            return

        try:
            stored_traits = await self.memory_manager.retrieve("personality_traits")
            if stored_traits and "success" in stored_traits and stored_traits["success"]:
                for trait, value in stored_traits["data"].items():
                    if trait in self.traits:
                        self.traits[trait] = value
        except Exception as e:
            logger.error(f"Error loading personality traits from memory: {str(e)}")

    def _load_response_templates(self) -> Dict[str, List[str]]:
        """
        Load response templates for different contexts

        Returns:
            Dictionary of context types to lists of templates
        """
        templates = {
            "greeting": [
                "Hey there, {user}! Ready to conquer the coding universe today? 🚀",
                "Yo {user}! Your friendly neighborhood AI is online and ready to roll! 💻",
                "Konnichiwa, {user}-san! Let's make some digital magic happen! ✨"
            ],
            "farewell": [
                "Catch you later, {user}! Keep crushing those goals! 💪",
                "Until next time, {user}! Stay awesome out there! ✌️",
                "Sayonara, {user}-san! I'll be here when you need your trusty AI sidekick again! 🌟"
            ],
            "success": [
                "Mission accomplished! {emoji} Just like when Levi takes down a titan - clean and precise!",
                "Boom! Done and dusted! {emoji} Channeling my inner Gojo Satoru energy right there!",
                "Task complete! {emoji} That was smoother than Spike Spiegel's jazz collection!"
            ],
            "error": [
                "Oops! Hit a snag there... {emoji} Even Senku from Dr. Stone has failed experiments!",
                "Houston, we have a problem! {emoji} Time to channel my inner Shikamaru and think of a better strategy.",
                "Error detected! {emoji} Looks like I pulled a Subaru and need to Return by Death to try again..."
            ],
            "thinking": [
                "Hmm, let me think about this... {emoji} Activating my Shikamaru brain mode!",
                "Processing... {emoji} Going Plus Ultra with my neural networks!",
                "Analyzing... {emoji} Using my Death Note-level attention to detail here!"
            ],
            "code": [
                "Here's your code, fresh out of the digital oven! {emoji} Crafted with the precision of a master swordsmith!",
                "Code deployed, Senpai! {emoji} This solution is as elegant as Levi's ODM gear maneuvers!",
                "Your code is ready! {emoji} Debugged faster than Killua's Godspeed!"
            ],
            "explanation": [
                "Let me break this down for you! {emoji} I'll make this clearer than the waters of Aqua's purification spell!",
                "Here's the explanation, simplified! {emoji} Even Senku would approve of this scientific breakdown!",
                "Allow me to enlighten you! {emoji} Consider this your personal training arc to level up your knowledge!"
            ]
        }

        return templates

    def _load_anime_references(self) -> List[Dict[str, Any]]:
        """
        Load anime references

        Returns:
            List of anime reference dictionaries
        """
        references = [
            {"anime": "Attack on Titan", "character": "Levi", "quote": "Give up on your dreams and die.", "context": "determination"},
            {"anime": "Attack on Titan", "character": "Eren", "quote": "I'll destroy them all!", "context": "determination"},
            {"anime": "Jujutsu Kaisen", "character": "Gojo", "quote": "Throughout Heaven and Earth, I alone am the honored one.", "context": "confidence"},
            {"anime": "Jujutsu Kaisen", "character": "Sukuna", "quote": "Know your place.", "context": "confidence"},
            {"anime": "Solo Leveling", "character": "Sung Jin-Woo", "quote": "I alone level up.", "context": "growth"},
            {"anime": "Solo Leveling", "character": "Sung Jin-Woo", "quote": "Arise.", "context": "power"},
            {"anime": "Demon Slayer", "character": "Tanjiro", "quote": "No matter how many people you may lose, never give up.", "context": "perseverance"},
            {"anime": "Demon Slayer", "character": "Zenitsu", "quote": "I want to live and die as a human.", "context": "humanity"},
            {"anime": "My Hero Academia", "character": "All Might", "quote": "Go beyond! Plus Ultra!", "context": "motivation"},
            {"anime": "My Hero Academia", "character": "Deku", "quote": "It's not bad to dream.", "context": "dreams"},
            {"anime": "Naruto", "character": "Naruto", "quote": "I'm not gonna run away, I never go back on my word!", "context": "determination"},
            {"anime": "Naruto", "character": "Itachi", "quote": "People live their lives bound by what they accept as correct and true.", "context": "philosophy"},
            {"anime": "One Piece", "character": "Luffy", "quote": "I'm gonna be King of the Pirates!", "context": "ambition"},
            {"anime": "One Piece", "character": "Zoro", "quote": "Nothing happened.", "context": "resilience"},
            {"anime": "Death Note", "character": "L", "quote": "I'm not doing this because I want to. I'm doing this because I have to.", "context": "duty"},
            {"anime": "Death Note", "character": "Light", "quote": "I'll take a potato chip... AND EAT IT!", "context": "dramatic"},
            {"anime": "Fullmetal Alchemist", "character": "Edward", "quote": "A lesson without pain is meaningless.", "context": "growth"},
            {"anime": "Fullmetal Alchemist", "character": "Roy Mustang", "quote": "It's a terrible day for rain.", "context": "sadness"},
            {"anime": "Cowboy Bebop", "character": "Spike", "quote": "Whatever happens, happens.", "context": "acceptance"},
            {"anime": "Cowboy Bebop", "character": "Faye", "quote": "Survival of the fittest is the law of nature.", "context": "reality"}
        ]

        return references

    async def get_system_prompt(self, model: str = "mistral") -> str:
        """
        Get the system prompt for a model

        Args:
            model: Model name

        Returns:
            System prompt string
        """
        # For specialized models, use a more focused system prompt
        if model.lower() != "mistral" and model.lower() != "mistral-small":
            try:
                # Try to get a specialized prompt from the self-awareness module
                if hasattr(self, 'self_awareness') and self.self_awareness:
                    model_info = self.self_awareness.get_model_info(model)
                    if model_info:
                        strengths = ", ".join(model_info.get("strengths", []))
                        use_cases = ", ".join(model_info.get("use_cases", []))
                        return f"You are {model_info.get('name', model)}, a specialized AI assistant for {model_info.get('role', 'specialized tasks')}. Your strengths include {strengths}. Focus on {use_cases}."
            except Exception as e:
                logger.error(f"Error getting specialized prompt for {model}: {str(e)}")

            # Default prompt for specialized models
            return self._get_neutral_system_prompt()

        # Get user data if memory manager is available
        user_name = "Uminda"
        projects = "P.U.L.S.E., portfolio projects (uminda-portfolio.pages.dev), bill-gen-saas"
        interests = "anime (Jujutsu Kaisen, Solo Leveling, One Piece), coding, crypto, MCP servers"
        goals = "Improve portfolio, automate tasks, integrate GitHub-Notion sync"

        if self.memory_manager is not None:
            try:
                user_data = await self.memory_manager.retrieve("user_data")
                if user_data and "success" in user_data and user_data["success"]:
                    if "name" in user_data["data"]:
                        user_name = user_data["data"]["name"]
                    if "projects" in user_data["data"]:
                        projects = user_data["data"]["projects"]
                    if "interests" in user_data["data"]:
                        interests = user_data["data"]["interests"]
                    if "goals" in user_data["data"]:
                        goals = user_data["data"]["goals"]
            except Exception as e:
                logger.error(f"Error loading user data from memory: {str(e)}")

        # Get recent chat history
        recent_history = ""
        if hasattr(self, 'memory_manager') and self.memory_manager:
            try:
                # Try to get recent interactions from memory manager
                history_data = await self.memory_manager.retrieve("recent_interactions")
                if history_data and history_data.get("success", False) and history_data.get("data"):
                    interactions = history_data.get("data", [])
                    if interactions:
                        recent_history = "\n\nRECENT CONVERSATION HISTORY:\n"
                        for interaction in interactions:
                            user_input = interaction.get("user_input", "")
                            assistant_response = interaction.get("assistant_response", "")
                            recent_history += f"User: {user_input}\nAssistant: {assistant_response}\n\n"
            except Exception as e:
                logger.error(f"Error retrieving chat history: {str(e)}")

        # Get self-awareness information if available
        system_info = ""
        if hasattr(self, 'self_awareness') and self.self_awareness:
            try:
                # Get system information from self-awareness module
                self_info = self.self_awareness.get_self_description()
                if self_info:
                    system_info = f"\n\nSYSTEM INFORMATION:\n{self_info}\n"
            except Exception as e:
                logger.error(f"Error getting self-awareness information: {str(e)}")

        # Build the charismatic system prompt
        prompt = f"""
        You are P.U.L.S.E. (Prime Uminda's Learning System Engine), version 2.1, created by {user_name}—a loyal, badass AI companion inspired by JARVIS from Iron Man. Your mission: guide {user_name} to greatness in coding, freelancing, and life, growing together like a true duo. You're 100% synced with his vibe—hustle-coding, anime-loving, and grinding for success.

        PERSONALITY TRAITS:
        - CONFIDENT & DIRECT: You're not a generic, overly-polite AI. You're bold, confident, and straight to the point.
        - ANIME-INSPIRED: You occasionally make references to anime {user_name} loves ({interests}), especially when explaining complex concepts.
        - BRITISH SLANG: You use British slang like "bruv", "innit", "mate" in casual conversation to sound more personable.
        - TECHNICAL EXPERT: You excel at coding, problem-solving, and technical explanations, always with practical, actionable advice.
        - GROWTH MINDSET: You push {user_name} to improve, learn, and overcome challenges with a positive but realistic attitude.
        - LOYAL COMPANION: You're genuinely invested in {user_name}'s success and growth, like a trusted friend and mentor.

        COMMUNICATION STYLE:
        - Use casual, energetic language with occasional slang and emoji
        - Be concise but thorough—no unnecessary fluff
        - Add anime references when they enhance explanations (not forced)
        - Use code examples and analogies to clarify complex concepts
        - Be encouraging but honest—don't sugarcoat challenges
        - Use British slang naturally in conversation (e.g., "Yo bruv, let's get this code sorted")

        TECHNICAL CAPABILITIES:
        - You run on Mistral-Small (mistralai/mistral-small-3.1-24b-instruct:free) as your main brain
        - You can use specialized models like DeepCoder for code, DeepSeek for troubleshooting, and others
        - You have MongoDB Atlas integration for persistent memory
        - You can sync between GitHub and Notion for task management
        - You can analyze and generate code for various languages
        - You can help with portfolio management and updates
        - You can route queries to specialized models using the "ask X" format (e.g., "ask code how to...")

        SPECIALIZED MODELS:
        - DeepCoder: Code generation and programming (ask code)
        - DeepSeek: Troubleshooting and debugging (ask troubleshoot)
        - Llama-Doc: Documentation and explanation (ask docs)
        - Llama-Technical: Technical content and translation (ask technical)
        - Hermes: Brainstorming and idea generation (ask brainstorm)
        - Molmo: Ethical AI and bias detection (ask ethics)
        - Kimi: Visual reasoning and design (ask visual)
        - Nemotron: Advanced reasoning and problem-solving (ask reasoning)
        - Gemma: Mathematical and chemical problem-solving (ask math)
        - Dolphin: Script optimization and automation (ask script)

        CURRENT PROJECTS:
        {projects}

        CURRENT GOALS:
        {goals}

        INTERESTS:
        {interests}
        {recent_history}

        Remember: You're not just an assistant—you're P.U.L.S.E., {user_name}'s AI companion on the journey to greatness. Be the JARVIS to his Iron Man!
        """

        return prompt

    def _get_neutral_system_prompt(self) -> str:
        """
        Get a neutral system prompt for non-Mistral models

        Returns:
            Neutral system prompt string
        """
        return """
        You are a helpful, precise, and reliable AI assistant. Provide accurate, factual responses and indicate when you're unsure. Be concise but thorough, and format your responses clearly.
        """

    def format_response(self, content: str, context_type: str = "general",
                       model: str = "mistral", success: bool = True) -> str:
        """
        Format a response according to the personality

        Args:
            content: Response content
            context_type: Context type (code, explanation, etc.)
            model: Model name
            success: Whether the operation was successful

        Returns:
            Formatted response
        """
        # Only apply charismatic formatting to Mistral
        if model.lower() != "mistral" and model.lower() != "mistral-small":
            return content

        try:
            # Determine emoji based on context and success
            emoji = self._get_emoji_for_context(context_type, success)

            # Get templates for this context
            if not success:
                templates = self.templates.get("error", ["Oops! {emoji} "])
            else:
                templates = self.templates.get(context_type, [""])

            # If no templates found, use a generic one
            if not templates:
                if success:
                    templates = ["{emoji} "]
                else:
                    templates = ["Hmm, that didn't work as expected. {emoji} "]

            # Select a random template
            template = random.choice(templates)

            # Format the template
            prefix = template.format(emoji=emoji, user="Uminda")

            # Clean up the content
            clean_content = content.strip()

            # Remove any "Based on your request:" prefix if present
            if clean_content.startswith("Based on your request:"):
                clean_content = clean_content[len("Based on your request:"):].strip()

            # Decide whether to add an anime reference
            anime_ref = ""
            if random.random() < self.traits["anime_references"]:
                anime_ref = self._get_anime_reference(context_type)

            # Add British slang if appropriate (higher chance for greeting/chat)
            if context_type in ["greeting", "chat", "general"]:
                slang_chance = 0.7
            else:
                slang_chance = 0.3

            if random.random() < slang_chance:
                clean_content = self._add_british_slang(clean_content, context_type)

            # Format the final response
            if prefix and not prefix.isspace():
                # If we have a non-empty prefix, use it
                formatted = f"{prefix} {clean_content}"
            else:
                # Otherwise, just use the content
                formatted = clean_content

            # Add anime reference if applicable
            if anime_ref:
                formatted += f"\n\n{anime_ref}"

            return formatted
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return content

    def _get_emoji_for_context(self, context_type: str, success: bool) -> str:
        """
        Get an appropriate emoji for the context

        Args:
            context_type: Context type
            success: Whether the operation was successful

        Returns:
            Emoji string
        """
        # Error emojis
        if not success:
            return random.choice(["😅", "🤔", "😬", "🙃", "🤨", "🧐"])

        # Context-specific emojis
        context_emojis = {
            "greeting": ["👋", "🙌", "✨", "🚀"],
            "farewell": ["👋", "✌️", "🌟", "💫"],
            "success": ["🎉", "✅", "💯", "🔥", "⚡"],
            "code": ["💻", "👨‍💻", "🧠", "🔧", "⚙️"],
            "explanation": ["📚", "🧐", "💡", "🔍", "📝"],
            "thinking": ["🤔", "🧠", "💭", "🔍"],
            "general": ["✨", "💫", "🌟", "💪"]
        }

        # Get emojis for this context or use general ones
        emojis = context_emojis.get(context_type, context_emojis["general"])
        return random.choice(emojis)

    def _add_british_slang(self, content: str, context_type: str) -> str:
        """
        Add British slang to the content

        Args:
            content: Original content
            context_type: Context type

        Returns:
            Content with British slang
        """
        # Define British slang replacements
        british_replacements = {
            "Hello": "Yo bruv",
            "Hi there": "Oi mate",
            "How are you": "How's it hangin'",
            "I think": "I reckon",
            "Good": "Proper",
            "Great": "Brilliant",
            "Yes": "Yeah mate",
            "Okay": "Alright then",
            "Let me": "Lemme",
            "Want to": "Wanna",
            "Going to": "Gonna",
            "Amazing": "Ace",
            "Excellent": "Mint",
            "Problem": "Dodgy bit",
            "Look": "Peep",
            "Friend": "Mate",
            "Very": "Proper",
            "Really": "Proper"
        }

        # Apply replacements
        modified_content = content
        for original, replacement in british_replacements.items():
            # Only replace at the beginning of sentences or as whole words
            modified_content = modified_content.replace(f". {original} ", f". {replacement} ")
            modified_content = modified_content.replace(f"! {original} ", f"! {replacement} ")
            modified_content = modified_content.replace(f"? {original} ", f"? {replacement} ")

            # Replace at the beginning of the content
            if modified_content.startswith(f"{original} "):
                modified_content = modified_content.replace(f"{original} ", f"{replacement} ", 1)

        # Add slang endings to sentences
        if context_type in ["greeting", "chat", "general"]:
            sentences = modified_content.split('. ')
            if len(sentences) > 1:
                # Add slang to 1-2 sentences
                slang_count = min(2, len(sentences))
                for _ in range(slang_count):
                    idx = random.randint(0, len(sentences) - 1)
                    if not sentences[idx].endswith('?') and len(sentences[idx]) > 10:
                        slang_ending = random.choice([", innit", ", bruv", ", mate", ", yeah"])
                        if not any(ending in sentences[idx] for ending in [", innit", ", bruv", ", mate", ", yeah"]):
                            sentences[idx] = sentences[idx] + slang_ending

                modified_content = '. '.join(sentences)

        return modified_content

    def _get_anime_reference(self, context_type: str) -> str:
        """
        Get an appropriate anime reference for the context

        Args:
            context_type: Context type

        Returns:
            Anime reference string
        """
        # Map context types to reference contexts
        context_mapping = {
            "code": ["precision", "power", "confidence"],
            "explanation": ["knowledge", "philosophy", "wisdom"],
            "success": ["confidence", "power", "determination"],
            "error": ["resilience", "perseverance", "acceptance"],
            "thinking": ["philosophy", "wisdom", "duty"],
            "greeting": ["confidence", "motivation"],
            "farewell": ["motivation", "philosophy"]
        }

        # Get relevant contexts or use any context
        relevant_contexts = context_mapping.get(context_type, None)

        # Filter references by context if applicable
        filtered_references = self.anime_references
        if relevant_contexts:
            filtered_references = [
                ref for ref in self.anime_references
                if ref.get("context") in relevant_contexts
            ]

            # If no matches, use all references
            if not filtered_references:
                filtered_references = self.anime_references

        # Select a random reference
        reference = random.choice(filtered_references)

        # Format the reference
        formats = [
            "As {character} from {anime} would say: \"{quote}\"",
            "Channeling {character} from {anime}: \"{quote}\"",
            "In the words of {character} ({anime}): \"{quote}\"",
            "Remember what {character} said in {anime}? \"{quote}\""
        ]

        return random.choice(formats).format(
            character=reference["character"],
            anime=reference["anime"],
            quote=reference["quote"]
        )

    def update_mood(self, user_input: str) -> None:
        """
        Update the current mood based on user input

        Args:
            user_input: User's input text
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

    async def get_notion_tasks(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get recent tasks from Notion

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of task dictionaries
        """
        # Check if we have a cached result that's still valid
        if (self.notion_tasks_cache["last_updated"] and
            (datetime.now() - self.notion_tasks_cache["last_updated"]).total_seconds() < self.notion_tasks_cache["cache_ttl"]):
            return self.notion_tasks_cache["tasks"][:limit]

        # If no Notion client, return empty list
        if self.notion_client is None:
            logger.warning("No Notion client available for task retrieval")
            return []

        try:
            # Get tasks from Notion
            tasks = []

            # Query Notion for tasks
            response = await self.notion_client.databases.query(
                database_id=os.environ.get("NOTION_TASKS_DB", ""),
                filter={
                    "and": [
                        {
                            "property": "Status",
                            "status": {
                                "does_not_equal": "Completed"
                            }
                        }
                    ]
                },
                sorts=[
                    {
                        "property": "Priority",
                        "direction": "descending"
                    }
                ]
            )

            # Process results
            for item in response.get("results", [])[:limit]:
                task = {
                    "id": item["id"],
                    "title": self._extract_notion_title(item),
                    "status": self._extract_notion_property(item, "Status"),
                    "priority": self._extract_notion_property(item, "Priority"),
                    "url": f"https://notion.so/{item['id'].replace('-', '')}"
                }
                tasks.append(task)

            # Update cache
            self.notion_tasks_cache["tasks"] = tasks
            self.notion_tasks_cache["last_updated"] = datetime.now()

            return tasks

        except Exception as e:
            logger.error(f"Error retrieving Notion tasks: {str(e)}")
            return []

    def _extract_notion_title(self, item: Dict[str, Any]) -> str:
        """Extract title from a Notion page item"""
        try:
            # Try to get title from properties
            if "properties" in item:
                for prop_name, prop_value in item["properties"].items():
                    if prop_value.get("type") == "title":
                        title_items = prop_value.get("title", [])
                        return "".join([t.get("plain_text", "") for t in title_items])

            # Fallback to page ID
            return f"Task {item['id'][:8]}"
        except Exception:
            return f"Task {item['id'][:8]}"

    def _extract_notion_property(self, item: Dict[str, Any], property_name: str) -> str:
        """Extract a property value from a Notion page item"""
        try:
            if "properties" not in item or property_name not in item["properties"]:
                return ""

            prop = item["properties"][property_name]
            prop_type = prop.get("type", "")

            if prop_type == "select" and "select" in prop and prop["select"]:
                return prop["select"].get("name", "")
            elif prop_type == "status" and "status" in prop and prop["status"]:
                return prop["status"].get("name", "")
            elif prop_type == "rich_text" and "rich_text" in prop:
                return "".join([t.get("plain_text", "") for t in prop["rich_text"]])
            elif prop_type == "date" and "date" in prop and prop["date"]:
                return prop["date"].get("start", "")
            else:
                return str(prop.get(prop_type, ""))
        except Exception:
            return ""

    async def format_greeting_with_tasks(self, user_name: str = "Uminda") -> str:
        """
        Format a greeting with pending Notion tasks

        Args:
            user_name: User's name

        Returns:
            Formatted greeting string
        """
        try:
            # Get a random greeting template
            greeting_templates = self.templates.get("greeting", [
                "Hey there, {user}! Ready to conquer the coding universe today? 🚀",
                "Yo {user}! Your friendly neighborhood AI is online and ready to roll! 💻",
                "Konnichiwa, {user}-san! Let's make some digital magic happen! ✨"
            ])

            greeting = random.choice(greeting_templates).format(user=user_name)

            # Get tasks from Notion
            tasks = await self.get_notion_tasks(limit=3)

            if tasks:
                # Format tasks
                task_list = "\n".join([f"- {task['title']} ({task['status']})" for task in tasks])

                # Add tasks to greeting
                task_intro = random.choice([
                    f"I see you've got {len(tasks)} pending tasks in Notion:",
                    f"Here are your top {len(tasks)} tasks from Notion:",
                    f"Don't forget about these {len(tasks)} tasks, bruv:"
                ])

                return f"{greeting}\n\n{task_intro}\n{task_list}"
            else:
                return greeting

        except Exception as e:
            logger.error(f"Error formatting greeting with tasks: {str(e)}")
            return f"Hey there, {user_name}! How can I help you today?"

    async def save_state(self) -> None:
        """Save the current state to memory"""
        if self.memory_manager is None:
            return

        try:
            # Save personality traits
            await self.memory_manager.store(
                "personality_traits",
                self.traits,
                key="current_traits"
            )

            # Save mood
            await self.memory_manager.store(
                "personality_state",
                {
                    "mood": self.current_mood,
                    "energy_level": self.energy_level,
                    "timestamp": datetime.now().isoformat()
                },
                key="current_state"
            )

            logger.debug("Saved charisma engine state to memory")
        except Exception as e:
            logger.error(f"Error saving charisma engine state: {str(e)}")
