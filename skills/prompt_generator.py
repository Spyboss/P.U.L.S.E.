"""
Prompt Generator for General Pulse

This module provides template-based prompt generation for various AI models
and combines outputs from multiple models into cohesive prompts.
"""

import os
import json
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Add parent directory to path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import default_logger as logger

class PromptGenerator:
    """
    Generates dynamic, context-aware prompts for Cursor AI and other models.
    Uses Jinja2 templating to create specialized prompts for different use cases
    and can combine outputs from multiple models into cohesive prompts.
    """
    
    def __init__(self, templates_dir=None):
        """
        Initialize the prompt generator with templates directory.
        
        Args:
            templates_dir (str, optional): Path to templates directory. 
                If None, defaults to 'templates' in the same directory.
        """
        if templates_dir is None:
            # Default to 'templates' in the same directory as this file
            templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../templates")
        
        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize default templates if they don't exist
        self._ensure_default_templates()
        
        # Load all templates
        self.templates = self._load_templates()
        logger.info(f"Prompt Generator initialized with {len(self.templates)} templates")
    
    def _ensure_default_templates(self):
        """Create default templates if they don't exist."""
        default_templates = {
            "code_generation.j2": """Generate {{ language }} code for {{ project_type }}:

Requirements:
{% for req in requirements %}
- {{ req }}
{% endfor %}

Technical specifications:
- Framework: {{ framework }}
- API integrations: {{ api_integrations|join(', ') }}
{% if style_guide %}
- Style guide: {{ style_guide }}
{% endif %}

Ensure the code is:
- Well-documented with comments
- Follows best practices for {{ language }}
- Includes error handling
- Is optimized for performance

Additional context:
{{ additional_context }}
""",
            "commit_message.j2": """Generate a concise, informative git commit message for changes to '{{ file_path }}'
in the repository {{ owner }}/{{ repo }}. The changes are:

{{ diff }}

Make the commit message less than 100 characters, slightly snarky, and professional.
Do not include quotes around the message.
""",
            "combined_portfolio.j2": """Create a {{ deepseek.framework }} portfolio website with the following:

Technical Stack:
{% for tech in deepseek.technologies %}
- {{ tech }}
{% endfor %}

Design Trends (2025):
{% for trend in grok.trends %}
- {{ trend.name }}: {{ trend.description }}
{% endfor %}

Content:
{{ claude.bio }}

The site should be responsive, performant, and showcase the portfolio items in a modern layout.
Use {{ deepseek.styling }} for styling and {{ deepseek.animation }} for animations.
"""
        }
        
        for filename, content in default_templates.items():
            file_path = os.path.join(self.templates_dir, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.debug(f"Created default template: {filename}")
    
    def _load_templates(self):
        """Load all templates from the templates directory."""
        templates = {}
        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.j2')]
        
        for filename in template_files:
            template_name = os.path.splitext(filename)[0]
            templates[template_name] = self.env.get_template(filename)
            
        return templates
    
    def generate_prompt(self, template_name, context_data):
        """
        Generate a prompt using the specified template and context data.
        
        Args:
            template_name (str): Name of the template to use (without extension)
            context_data (dict): Data to fill the template with
            
        Returns:
            str: The generated prompt
            
        Raises:
            ValueError: If the template doesn't exist
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found. Available templates: {', '.join(self.templates.keys())}")
        
        template = self.templates[template_name]
        try:
            prompt = template.render(**context_data)
            logger.debug(f"Generated prompt using template '{template_name}'")
            return prompt
        except Exception as e:
            logger.error(f"Error generating prompt with template '{template_name}': {str(e)}", exc_info=True)
            raise
    
    def combine_model_outputs(self, outputs, prompt_type):
        """
        Combine outputs from multiple models into a single prompt.
        
        Args:
            outputs (dict): Dictionary mapping model names to their outputs
            prompt_type (str): Type of prompt to generate (e.g., 'portfolio', 'code')
            
        Returns:
            str: Combined prompt
            
        Raises:
            ValueError: If the combined template doesn't exist
        """
        combined_template = f"combined_{prompt_type}"
        if combined_template not in self.templates:
            raise ValueError(f"Combined template '{combined_template}' not found")
        
        return self.generate_prompt(combined_template, outputs)
    
    def create_cursor_prompt(self, task_data, model_outputs):
        """
        Create a specialized prompt for Cursor AI based on task data and model outputs.
        
        Args:
            task_data (dict): Information about the task
            model_outputs (dict): Outputs from various AI models
            
        Returns:
            str: Prompt formatted for Cursor AI
        """
        # Combine all data into a single context
        context = {
            "task": task_data,
            **model_outputs
        }
        
        # Determine the appropriate template based on task type
        task_type = task_data.get("type", "general")
        template_name = f"cursor_{task_type}"
        
        # Fall back to combined template if specific cursor template doesn't exist
        if template_name not in self.templates:
            template_name = f"combined_{task_type}"
            
            # Fall back to generic cursor template if combined template doesn't exist
            if template_name not in self.templates:
                template_name = "cursor_generic"
                
                # Create a basic generic template if it doesn't exist
                if template_name not in self.templates:
                    generic_template = """
                    {{ task.description }}
                    
                    {% if deepseek %}
                    Technical recommendations:
                    {{ deepseek }}
                    {% endif %}
                    
                    {% if grok %}
                    Current trends:
                    {{ grok }}
                    {% endif %}
                    
                    {% if claude %}
                    Content suggestions:
                    {{ claude }}
                    {% endif %}
                    """
                    
                    with open(os.path.join(self.templates_dir, f"{template_name}.j2"), 'w') as f:
                        f.write(generic_template)
                    
                    # Reload templates
                    self.templates = self._load_templates()
        
        return self.generate_prompt(template_name, context)
    
    def add_template(self, template_name, template_content):
        """
        Add a new template or update an existing one.
        
        Args:
            template_name (str): Name of the template (without extension)
            template_content (str): Jinja2 template content
            
        Returns:
            bool: True if successful
        """
        filename = f"{template_name}.j2"
        file_path = os.path.join(self.templates_dir, filename)
        
        with open(file_path, 'w') as f:
            f.write(template_content)
        
        # Reload templates
        self.templates = self._load_templates()
        logger.info(f"Added/updated template: {template_name}")
        
        return True
    
    def get_template_content(self, template_name):
        """
        Get the content of a template.
        
        Args:
            template_name (str): Name of the template (without extension)
            
        Returns:
            str: Template content
            
        Raises:
            ValueError: If the template doesn't exist
        """
        filename = f"{template_name}.j2"
        file_path = os.path.join(self.templates_dir, filename)
        
        if not os.path.exists(file_path):
            raise ValueError(f"Template '{template_name}' not found")
        
        with open(file_path, 'r') as f:
            return f.read()
    
    def list_templates(self):
        """
        List all available templates.
        
        Returns:
            list: Names of all available templates
        """
        return list(self.templates.keys())


# Example usage
if __name__ == "__main__":
    # Initialize the prompt generator
    generator = PromptGenerator()
    
    # Sample data for a portfolio project
    portfolio_data = {
        "deepseek": {
            "framework": "Next.js",
            "technologies": ["React", "Tailwind CSS", "Framer Motion", "Supabase"],
            "styling": "Tailwind CSS with custom theme",
            "animation": "Framer Motion for page transitions"
        },
        "grok": {
            "trends": [
                {"name": "Neobrutalism", "description": "Bold typography, bright colors, raw edges"},
                {"name": "Glassmorphism", "description": "Frosted glass effect with depth"},
                {"name": "Soft gradients", "description": "Subtle color transitions in backgrounds"}
            ]
        },
        "claude": {
            "bio": "Alex is a creative developer who blends code and design to build unique digital experiences."
        }
    }
    
    # Generate a combined prompt for a portfolio project
    try:
        prompt = generator.combine_model_outputs(portfolio_data, "portfolio")
        print("=== Generated Prompt ===")
        print(prompt)
    except ValueError as e:
        print(f"Error: {e}")
        
    # List all available templates
    print("\n=== Available Templates ===")
    for template in generator.list_templates():
        print(f"- {template}") 