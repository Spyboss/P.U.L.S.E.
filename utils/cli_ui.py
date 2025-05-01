"""
CLI UI for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides a terminal-based UI for system monitoring and model testing
"""

import structlog
import asyncio
import sys
from typing import Dict, Any, List

# Try to import rich for better terminal UI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    # from rich.syntax import Syntax  # Uncomment if needed for syntax highlighting
    # from rich.live import Live  # Uncomment if needed for future features
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Try to import prompt_toolkit for better input handling
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style
    from prompt_toolkit.history import InMemoryHistory
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

# Configure logger
logger = structlog.get_logger("cli_ui")

class PulseCLIUI:
    """
    Terminal-based UI for General Pulse
    """

    def __init__(self, agent=None):
        """
        Initialize the CLI UI

        Args:
            agent: The Pulse Agent instance
        """
        self.agent = agent
        self.console = Console() if RICH_AVAILABLE else None

        # Initialize prompt toolkit session if available
        if PROMPT_TOOLKIT_AVAILABLE:
            # Define a style for the prompt
            style = Style.from_dict({
                'prompt': 'bold cyan',
            })

            # Create a history object
            history = InMemoryHistory()

            # Create a prompt session
            self.prompt_session = PromptSession(
                history=history,
                style=style,
                complete_in_thread=True,
                complete_while_typing=True
            )
        else:
            self.prompt_session = None

    def display_system_vitals(self, system_status: Dict[str, Any]):
        """
        Display system vitals in a nice table

        Args:
            system_status: System status dictionary
        """
        if not RICH_AVAILABLE:
            # Fallback to plain text
            print("\n=== SYSTEM VITALS ===")
            print(f"Memory: {system_status['memory']['used']} / {system_status['memory']['total']} ({system_status['memory']['percent']}%)")
            print(f"Disk: {system_status['disk']['used']} / {system_status['disk']['total']} ({system_status['disk']['percent']}%)")
            print(f"CPU: {system_status['cpu']['percent']}% used")
            print(f"Processor: {system_status['cpu'].get('processor', 'Unknown')}")
            return

        # Create a table for system vitals
        table = Table(title="System Vitals")

        # Add columns
        table.add_column("Resource", style="cyan")
        table.add_column("Usage", style="magenta")
        table.add_column("Status", style="bold")

        # Add memory row
        memory_status = "green" if system_status['memory']['percent'] < 70 else "yellow" if system_status['memory']['percent'] < 90 else "red"
        table.add_row(
            "Memory",
            f"{system_status['memory']['used']} / {system_status['memory']['total']} ({system_status['memory']['percent']}%)",
            "✅ Good" if memory_status == "green" else "⚠️ Warning" if memory_status == "yellow" else "❌ Critical",
            style=memory_status
        )

        # Add disk row
        disk_status = "green" if system_status['disk']['percent'] < 70 else "yellow" if system_status['disk']['percent'] < 90 else "red"
        table.add_row(
            "Disk",
            f"{system_status['disk']['used']} / {system_status['disk']['total']} ({system_status['disk']['percent']}%)",
            "✅ Good" if disk_status == "green" else "⚠️ Warning" if disk_status == "yellow" else "❌ Critical",
            style=disk_status
        )

        # Add CPU row
        cpu_status = "green" if system_status['cpu']['percent'] < 70 else "yellow" if system_status['cpu']['percent'] < 90 else "red"
        table.add_row(
            "CPU",
            f"{system_status['cpu']['percent']}% used",
            "✅ Good" if cpu_status == "green" else "⚠️ Warning" if cpu_status == "yellow" else "❌ Critical",
            style=cpu_status
        )

        # Add processor row
        table.add_row("Processor", system_status['cpu'].get('processor', 'Unknown'), "", style="blue")

        # Print the table
        self.console.print(table)

    def display_model_status(self, model_stats: Dict[str, Any], available_models: Dict[str, List[str]]):
        """
        Display model status in a nice table

        Args:
            model_stats: Model usage statistics
            available_models: Available models by type
        """
        if not RICH_AVAILABLE:
            # Fallback to plain text
            print("\n=== MODEL STATUS ===")
            print(f"Mistral Small: {model_stats.get('mistral', {}).get('calls', 0)} calls")
            print(f"OpenRouter: {model_stats.get('openrouter', {}).get('calls', 0)} calls")
            print(f"Local: {model_stats.get('local', {}).get('calls', 0)} calls")
            return

        # Create a table for model status
        table = Table(title="AI Model Status")

        # Add columns
        table.add_column("Model", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Calls", style="yellow")
        table.add_column("Status", style="bold")

        # Add Mistral Small row
        table.add_row(
            "Mistral Small",
            "OpenRouter",
            str(model_stats.get('mistral', {}).get('calls', 0)),
            "Available" if "mistral" in available_models and available_models["mistral"] else "Unavailable",
            style="green" if "mistral" in available_models and available_models["mistral"] else "red"
        )

        # Add OpenRouter row
        table.add_row(
            "OpenRouter",
            "Multiple",
            str(model_stats.get('openrouter', {}).get('calls', 0)),
            "Available" if "openrouter" in available_models and available_models["openrouter"] else "Unavailable",
            style="green" if "openrouter" in available_models and available_models["openrouter"] else "red"
        )

        # Add Local row
        table.add_row(
            "Local",
            "DistilBERT",
            str(model_stats.get('local', {}).get('calls', 0)),
            "Available" if "local" in available_models and available_models["local"] else "Unavailable",
            style="green" if "local" in available_models and available_models["local"] else "red"
        )

        # Print the table
        self.console.print(table)

    def display_openrouter_models(self, model_orchestrator):
        """
        Display OpenRouter models in a nice table

        Args:
            model_orchestrator: The model orchestrator instance
        """
        if not RICH_AVAILABLE or not model_orchestrator or not hasattr(model_orchestrator, 'free_models'):
            # Fallback to plain text or skip if no model orchestrator
            if not model_orchestrator or not hasattr(model_orchestrator, 'free_models'):
                print("\n=== OPENROUTER MODELS ===")
                print("No model orchestrator available")
                return

            print("\n=== OPENROUTER MODELS ===")
            try:
                # Import model roles from config
                from configs.models import MODEL_ROLES

                for model_key, model_info in MODEL_ROLES.items():
                    if model_info['api_type'] == 'openrouter':
                        model_status = "Available" if model_orchestrator.openrouter else "Unavailable"
                        print(f"{model_info['name']} ({model_info['role']}): {model_status}")
            except ImportError:
                # Fallback if config not available
                specialized_models = {
                    "deepseek": "DeepSeek (Troubleshooting)",
                    "deepcoder": "DeepCoder (Code Generation)",
                    "llama-doc": "Llama-Doc (Documentation)",
                    "mistral-small": "Mistral-Small (Trends)",
                    "llama-content": "Llama-Content (Content Creation)",
                    "llama-technical": "Llama-Technical (Technical Translation)",
                    "hermes": "Hermes (Brainstorming)",
                    "olmo": "Olmo (Ethical AI)",
                    "mistralai": "MistralAI (Task Automation)",
                    "kimi": "Kimi (Visual Reasoning)",
                    "nemotron": "Nemotron (Advanced Reasoning)"
                }

                for model_key, model_display in specialized_models.items():
                    model_status = "Available" if model_orchestrator.openrouter else "Unavailable"
                    print(f"{model_display}: {model_status}")
            return

        # Create a table for OpenRouter models
        table = Table(title="OpenRouter Models")

        # Add columns
        table.add_column("Model", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Status", style="bold")
        table.add_column("Model ID", style="dim")

        try:
            # Import model roles from config
            from configs.models import MODEL_ROLES

            # Add rows for each model from configuration
            for _, model_info in MODEL_ROLES.items():
                if model_info['api_type'] == 'openrouter':
                    model_status = "Available" if model_orchestrator.openrouter else "Unavailable"

                    table.add_row(
                        model_info['name'],
                        model_info['role'],
                        "Available" if model_orchestrator.openrouter else "Unavailable",
                        model_info['model_id'],
                        style="green" if model_orchestrator.openrouter else "red"
                    )
        except ImportError:
            # Fallback if config not available
            specialized_models = {
                "deepseek": ("DeepSeek", "Troubleshooting"),
                "deepcoder": ("DeepCoder", "Code Generation"),
                "llama-doc": ("Llama-Doc", "Documentation"),
                "mistral-small": ("Mistral-Small", "Trends"),
                "llama-content": ("Llama-Content", "Content Creation"),
                "llama-technical": ("Llama-Technical", "Technical Translation"),
                "hermes": ("Hermes", "Brainstorming"),
                "olmo": ("Olmo", "Ethical AI"),
                "mistralai": ("MistralAI", "Task Automation"),
                "kimi": ("Kimi", "Visual Reasoning"),
                "nemotron": ("Nemotron", "Advanced Reasoning")
            }

            # Add rows for each specialized model
            for model_key, (model_name, role) in specialized_models.items():
                model_status = "Available" if model_orchestrator.openrouter else "Unavailable"
                model_id = model_orchestrator.free_models.get(model_key, "Unknown")

                table.add_row(
                    model_name,
                    role,
                    "Available" if model_orchestrator.openrouter else "Unavailable",
                    model_id,
                    style="green" if model_orchestrator.openrouter else "red"
                )

        # Print the table
        self.console.print(table)

    async def test_model(self, model_name: str, query: str = "Hello, how are you?"):
        """
        Test a specific model with a query

        Args:
            model_name: Name of the model to test
            query: Query to send to the model

        Returns:
            Dictionary with success status and response information
        """
        if not self.agent or not self.agent.model_orchestrator:
            print(f"Cannot test model {model_name}: No model orchestrator available")
            return {"success": False, "error": "No model orchestrator available"}

        # Special handling for Gemini/Mistral - redirect to Mistral Small via OpenRouter
        if model_name.lower() == "gemini":
            if RICH_AVAILABLE:
                self.console.print("\n[bold yellow]Note: 'gemini' is deprecated. Redirecting to Mistral Small via OpenRouter.[/bold yellow]")
            else:
                print("\nNote: 'gemini' is deprecated. Redirecting to Mistral Small via OpenRouter.")
            model_name = "mistral-small"

        # Special handling for Mistral Small - test directly using the model orchestrator via OpenRouter
        if model_name.lower() == "mistral-small":
            if not self.agent or not hasattr(self.agent, 'model_orchestrator'):
                if RICH_AVAILABLE:
                    self.console.print("\n[bold red]Cannot test Mistral Small via OpenRouter: No model orchestrator available[/bold red]")
                else:
                    print("\nCannot test Mistral Small via OpenRouter: No model orchestrator available")
                return {"success": False, "error": "No model orchestrator available"}

            try:
                # Test the API key first
                api_key_result = await self.agent.model_orchestrator.check_openrouter_api_key()

                if not api_key_result["success"]:
                    if RICH_AVAILABLE:
                        self.console.print(f"\n[bold red]OpenRouter API key test failed: {api_key_result.get('error', 'Unknown error')}[/bold red]")
                    else:
                        print(f"\nOpenRouter API key test failed: {api_key_result.get('error', 'Unknown error')}")
                    return {"success": False, "error": api_key_result.get('error', 'Unknown error')}

                # Now test with a query
                if RICH_AVAILABLE:
                    self.console.print("\n[bold blue]Testing Mistral Small model via OpenRouter with query: What is machine learning? Keep it brief.[/bold blue]")
                else:
                    print("\nTesting Mistral Small model via OpenRouter with query: What is machine learning? Keep it brief.")

                # Call Mistral Small directly through the model orchestrator
                test_query = "What is machine learning? Keep it brief."
                mistral_result = await self.agent.model_orchestrator.test_main_brain(test_query)

                if mistral_result and mistral_result.get("success", False):
                    if RICH_AVAILABLE:
                        self.console.print(Panel(
                            f"[bold green]Test successful![/bold green]\n\n[cyan]Query:[/cyan] {test_query}\n\n[yellow]Response:[/yellow] {mistral_result.get('content', '')}\n\n[dim]Model: {mistral_result.get('model_id', 'mistralai/mistral-small-3.1-24b-instruct:free')}[/dim]",
                            title="Mistral Small Test",
                            border_style="green"
                        ))
                    else:
                        print("\nTest successful!")
                        print(f"Query: {test_query}")
                        print(f"Response: {mistral_result.get('content', '')}")
                        print(f"Model: {mistral_result.get('model_id', 'mistralai/mistral-small-3.1-24b-instruct:free')}")
                    return {"success": True, "model": mistral_result.get('model_id', 'mistralai/mistral-small-3.1-24b-instruct:free'), "response": mistral_result.get('content', '')}
                else:
                    if RICH_AVAILABLE:
                        self.console.print(Panel(
                            f"[bold red]Test failed![/bold red]\n\n[cyan]Query:[/cyan] {test_query}\n\n[red]Error:[/red] {mistral_result.get('error', 'Unknown error')}",
                            title="Mistral Small Test",
                            border_style="red"
                        ))
                    else:
                        print("\nTest failed!")
                        print(f"Query: {test_query}")
                        print(f"Error: {mistral_result.get('error', 'Unknown error')}")
                    return {"success": False, "error": mistral_result.get('error', 'Unknown error')}
            except Exception as e:
                if RICH_AVAILABLE:
                    self.console.print(f"\n[bold red]Error testing Mistral Small: {str(e)}[/bold red]")
                else:
                    print(f"\nError testing Mistral Small: {str(e)}")
                return {"success": False, "error": f"Error testing Mistral Small: {str(e)}"}

        if not RICH_AVAILABLE:
            print(f"\n=== TESTING MODEL: {model_name} ===")
            print(f"Query: {query}")
            print("Testing...")

            try:
                response = await self.agent._query_specific_model(model_name, query)
                if response:
                    # Extract model name from response if it's in the format [model_name] content
                    model_used = model_name
                    content = response
                    if response.startswith('[') and ']' in response:
                        model_part, content = response.split(']', 1)
                        model_used = model_part[1:].strip()
                    print(f"Model: {model_used}")
                    print(f"Response: {content}")
                    return {"success": True, "model": model_used, "response": content}
                else:
                    print("No response received")
                    return {"success": False, "error": "No response received"}
            except Exception as e:
                print(f"Error: {str(e)}")
                return {"success": False, "error": str(e)}

        # Create a spinner for the test
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Testing model {model}...".format(model=model_name)),
            console=self.console
        ) as progress:
            progress.add_task("Testing...", total=None)

            try:
                # Call the model with a timeout
                try:
                    # Set a timeout for the model query
                    response = await asyncio.wait_for(
                        self.agent._query_specific_model(model_name, query),
                        timeout=45  # 45 second timeout
                    )

                    # Display the result - response is a string, not a dictionary
                    if response:
                        # Extract model name from response if it's in the format [model_name] content
                        model_used = model_name
                        content = response
                        if response.startswith('[') and ']' in response:
                            model_part, content = response.split(']', 1)
                            model_used = model_part[1:].strip()

                        self.console.print(Panel(
                            f"[bold green]Test successful![/bold green]\n\n[cyan]Query:[/cyan] {query}\n\n[yellow]Response:[/yellow] {content}",
                            title=f"Model Test: {model_used}",
                            border_style="green"
                        ))
                        return {"success": True, "model": model_used, "response": content}
                    else:
                        self.console.print(Panel(
                            f"[bold red]Test failed![/bold red]\n\n[cyan]Query:[/cyan] {query}\n\n[red]Error:[/red] No response received",
                            title=f"Model Test: {model_name}",
                            border_style="red"
                        ))
                        return {"success": False, "error": "No response received"}
                except asyncio.TimeoutError:
                    self.console.print(Panel(
                        f"[bold yellow]Test timed out![/bold yellow]\n\n[cyan]Query:[/cyan] {query}\n\n[yellow]Warning:[/yellow] The request took too long and was cancelled after 45 seconds.",
                        title=f"Model Test: {model_name}",
                        border_style="yellow"
                    ))
                    return {"success": False, "error": "Request timed out after 45 seconds"}
                except asyncio.CancelledError:
                    self.console.print(Panel(
                        f"[bold yellow]Test cancelled![/bold yellow]\n\n[cyan]Query:[/cyan] {query}\n\n[yellow]Info:[/yellow] The request was cancelled.",
                        title=f"Model Test: {model_name}",
                        border_style="yellow"
                    ))
                    return {"success": False, "error": "Request was cancelled"}  # Return result for cancelled requests
            except Exception as e:
                self.console.print(Panel(
                    f"[bold red]Test failed with exception![/bold red]\n\n[cyan]Query:[/cyan] {query}\n\n[red]Error:[/red] {str(e)}",
                    title=f"Model Test: {model_name}",
                    border_style="red"
                ))
                return {"success": False, "error": str(e)}

    async def handle_offline_mode(self, enable: bool = True) -> None:
        """
        Handle offline mode toggle

        Args:
            enable: Whether to enable or disable offline mode
        """
        if not self.agent or not hasattr(self.agent, 'model_interface'):
            if RICH_AVAILABLE:
                self.console.print("[bold red]Cannot toggle offline mode: No model interface available[/bold red]")
            else:
                print("Cannot toggle offline mode: No model interface available")
            return

        try:
            # Toggle offline mode
            result = await self.agent.model_interface.toggle_offline_mode(enable)

            if RICH_AVAILABLE:
                if result["success"]:
                    status = "enabled" if result["offline_mode"] else "disabled"
                    # Use static formatting instead of dynamic
                    if result['offline_mode']:
                        self.console.print(Panel(
                            f"[bold green]Offline mode {status}[/bold green]\n\n"
                            f"{result['message']}",
                            title="Offline Mode",
                            border_style="green"
                        ))
                    else:
                        self.console.print(Panel(
                            f"[bold yellow]Offline mode {status}[/bold yellow]\n\n"
                            f"{result['message']}",
                            title="Offline Mode",
                            border_style="yellow"
                        ))
                else:
                    self.console.print(Panel(
                        f"[bold red]Failed to {'enable' if enable else 'disable'} offline mode[/bold red]\n\n"
                        f"{result['message']}",
                        title="Offline Mode",
                        border_style="red"
                    ))
            else:
                if result["success"]:
                    status = "enabled" if result["offline_mode"] else "disabled"
                    print(f"Offline mode {status}")
                    print(f"{result['message']}")
                else:
                    print(f"Failed to {'enable' if enable else 'disable'} offline mode")
                    print(f"{result['message']}")

            # Run a system check to update status
            await self.run_system_check()

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error toggling offline mode: {str(e)}[/bold red]")
            else:
                print(f"Error toggling offline mode: {str(e)}")

    async def run_system_check(self):
        """
        Run a comprehensive system check
        """
        if not self.agent:
            print("Cannot run system check: No agent available")
            return

        # Get system status
        try:
            from utils.system_utils import get_system_status
            system_status = get_system_status()
        except ImportError:
            # Fallback if system_utils is not available
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            system_status = {
                "cpu": {
                    "percent": psutil.cpu_percent(),
                    "processor": "Unknown"
                },
                "memory": {
                    "used": f"{memory.used / (1024 * 1024 * 1024):.2f}GB",
                    "total": f"{memory.total / (1024 * 1024 * 1024):.2f}GB",
                    "percent": memory.percent
                },
                "disk": {
                    "used": f"{disk.used / (1024 * 1024 * 1024):.2f}GB",
                    "total": f"{disk.total / (1024 * 1024 * 1024):.2f}GB",
                    "percent": disk.percent
                }
            }

        # Get model stats
        model_stats = {}
        available_models = {}
        if self.agent.model_orchestrator:
            model_stats = self.agent.model_orchestrator.get_usage_stats()
            available_models = self.agent.model_orchestrator.get_available_models()

        if not RICH_AVAILABLE:
            print("\n=== SYSTEM CHECK ===")
            self.display_system_vitals(system_status)
            self.display_model_status(model_stats, available_models)
            self.display_openrouter_models(self.agent.model_orchestrator)
            return

        # Display header
        self.console.print(Panel(
            "[bold cyan]Running comprehensive system check for P.U.L.S.E.[/bold cyan]",
            border_style="cyan"
        ))

        # Display system vitals
        self.display_system_vitals(system_status)

        # Display model status
        self.display_model_status(model_stats, available_models)

        # Display OpenRouter models
        self.display_openrouter_models(self.agent.model_orchestrator)

        # Display Ollama status
        if self.agent and hasattr(self.agent, 'model_interface') and self.agent.model_interface:
            try:
                # Force parameter to False to respect offline mode setting
                status = await self.agent.model_interface.check_status(force=False)
                ollama_status = status["ollama"]
                offline_mode = status["offline_mode"]
                distilbert_available = status["distilbert_available"]
                distilbert_initialized = status["distilbert_initialized"]
                internet_available = status["internet_available"]

                if RICH_AVAILABLE:
                    if ollama_status["running"]:
                        models_str = ", ".join(ollama_status["models"]) if ollama_status["models"] else "None"
                        memory_usage = f"{ollama_status.get('memory_usage', 0):.2f}GB" if ollama_status.get('memory_usage', 0) > 0 else "Unknown"
                        system_memory = ollama_status.get("system_memory", {})
                        free_memory = system_memory.get("free_gb", 0)
                        memory_percent = system_memory.get("percent_used", 0)

                        status_color = "green"
                        status_text = "Running"
                        if offline_mode:
                            status_text += " (Offline Mode)"

                        self.console.print(Panel(
                            f"[bold green]Ollama Status: {status_text}[/bold green]\n\n"
                            f"Models Loaded: {models_str}\n"
                            f"Memory Usage: {memory_usage}\n"
                            f"System Memory: {free_memory:.2f}GB free ({memory_percent}% used)\n"
                            f"Internet: {'Available' if internet_available else 'Not Available'}\n"
                            f"DistilBERT: {'Available' if distilbert_available else 'Not Available'} {'(Initialized)' if distilbert_initialized else ''}",
                            title="Ollama",
                            border_style=status_color
                        ))
                    else:
                        status_color = "yellow"
                        message = "[bold yellow]Ollama Status: Not Running"
                        if offline_mode:
                            message += " (Offline Mode)"
                        message += "[/bold yellow]"

                        system_memory = ollama_status.get("system_memory", {})
                        free_memory = system_memory.get("free_gb", 0)
                        memory_percent = system_memory.get("percent_used", 0)

                        if not ollama_status["executable_found"]:
                            message += "\n\nOllama executable not found. Please install Ollama from https://ollama.com"

                        if ollama_status.get("error"):
                            message += f"\n\nError: {ollama_status['error']}"

                        message += f"\n\nSystem Memory: {free_memory:.2f}GB free ({memory_percent}% used)\n"
                        message += f"Internet: {'✅ Available' if internet_available else '❌ Not Available'}\n"
                        message += f"DistilBERT: {'✅ Available' if distilbert_available else '❌ Not Available'} {'(Initialized)' if distilbert_initialized else ''}"

                        self.console.print(Panel(message, title="Ollama", border_style=status_color))
                else:
                    print("\n=== OLLAMA STATUS ===")
                    status_text = "Running" if ollama_status["running"] else "Not Running"
                    if offline_mode:
                        status_text += " (Offline Mode)"

                    print(f"🚀 Ollama Status: {status_text}")

                    if ollama_status["running"]:
                        models_str = ", ".join(ollama_status["models"]) if ollama_status["models"] else "None"
                        memory_usage = f"{ollama_status.get('memory_usage', 0):.2f}GB" if ollama_status.get('memory_usage', 0) > 0 else "Unknown"
                        print(f"Models Loaded: {models_str}")
                        print(f"Memory Usage: {memory_usage}")
                    else:
                        if not ollama_status["executable_found"]:
                            print("Ollama executable not found. Please install Ollama from https://ollama.com")
                        if ollama_status.get("error"):
                            print(f"Error: {ollama_status['error']}")

                    system_memory = ollama_status.get("system_memory", {})
                    free_memory = system_memory.get("free_gb", 0)
                    memory_percent = system_memory.get("percent_used", 0)
                    print(f"System Memory: {free_memory:.2f}GB free ({memory_percent}% used)")
                    print(f"Internet: {'Available' if internet_available else 'Not Available'}")
                    print(f"DistilBERT: {'Available' if distilbert_available else 'Not Available'} {'(Initialized)' if distilbert_initialized else ''}")
            except Exception as e:
                if RICH_AVAILABLE:
                    self.console.print(Panel(f"[bold red]Error checking Ollama status: {str(e)}[/bold red]", title="Ollama", border_style="red"))
                else:
                    print(f"Error checking Ollama status: {str(e)}")

        # Display summary
        memory_status = "green" if system_status['memory']['percent'] < 70 else "yellow" if system_status['memory']['percent'] < 90 else "red"
        disk_status = "green" if system_status['disk']['percent'] < 70 else "yellow" if system_status['disk']['percent'] < 90 else "red"
        cpu_status = "green" if system_status['cpu']['percent'] < 70 else "yellow" if system_status['cpu']['percent'] < 90 else "red"

        overall_status = "green"
        if memory_status == "red" or disk_status == "red" or cpu_status == "red":
            overall_status = "red"
        elif memory_status == "yellow" or disk_status == "yellow" or cpu_status == "yellow":
            overall_status = "yellow"

        # Check Ollama status
        ollama_status = "Not Available"
        if self.agent and hasattr(self.agent, 'model_interface'):
            try:
                # Force parameter to False to respect offline mode setting
                status = await self.agent.model_interface.check_status(force=False)
                ollama_status = status.get("ollama", {})
                if ollama_status.get("running", False):
                    ollama_status = "Running"
                else:
                    ollama_status = "Not Running"
            except Exception:
                ollama_status = "Error"

        # Determine status color and text
        status_text = "Good" if overall_status == "green" else "Warning" if overall_status == "yellow" else "Critical"

        # Create the panel with the appropriate color
        if overall_status == "green":
            status_message = f"[bold green]System Status: {status_text}[/bold green]\n\n"
        elif overall_status == "yellow":
            status_message = f"[bold yellow]System Status: {status_text}[/bold yellow]\n\n"
        else:  # red
            status_message = f"[bold red]System Status: {status_text}[/bold red]\n\n"

        self.console.print(Panel(
            status_message +
            f"Memory: {'Good' if memory_status == 'green' else 'Warning' if memory_status == 'yellow' else 'Critical'}\n" +
            f"Disk: {'Good' if disk_status == 'green' else 'Warning' if disk_status == 'yellow' else 'Critical'}\n" +
            f"CPU: {'Good' if cpu_status == 'green' else 'Warning' if cpu_status == 'yellow' else 'Critical'}\n" +
            f"Cloud Models: {'Available' if self.agent.model_orchestrator and self.agent.model_orchestrator.openrouter else 'Limited'}\n" +
            f"Local Models (Ollama): {ollama_status}",
            title="System Check Summary",
            border_style="green" if overall_status == "green" else "yellow" if overall_status == "yellow" else "red"
        ))

    async def test_intent(self, query: str):
        """
        Test intent classification

        Args:
            query: Query to classify
        """
        if not self.agent or not hasattr(self.agent, 'intent_handler'):
            print("Cannot test intent: No intent handler available")
            return

        try:
            # Classify the intent
            intent = await self.agent.intent_handler.classify(query)

            # Parse the command
            command = await self.agent.intent_handler.parse_command(query)

            if not RICH_AVAILABLE:
                print(f"\n=== INTENT TEST: {query} ===")
                print(f"Intent: {intent}")
                print(f"Command: {command}")
                return

            # Display the result
            self.console.print(Panel(
                f"[bold cyan]Query:[/bold cyan] {query}\n\n"
                f"[bold green]Intent:[/bold green] {intent}\n\n"
                f"[bold yellow]Command:[/bold yellow] {str(command)}",
                title="Intent Test",
                border_style="cyan"
            ))

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error testing intent: {str(e)}[/bold red]")
            else:
                print(f"Error testing intent: {str(e)}")

    async def test_all_models(self):
        """
        Test all available models
        """
        if not self.agent or not self.agent.model_orchestrator:
            print("Cannot test models: No model orchestrator available")
            return

        # Define test query
        test_query = "What is machine learning? Keep it brief."

        # Track results for summary
        successful_models = []
        failed_models = []

        # Define models to test with their correct names
        # These names must match the model names in the configuration
        models_to_test = [
            # OpenRouter models
            "deepseek",  # deepseek/deepseek-r1-zero:free
            "deepcoder",  # agentica-org/deepcoder-14b-preview:free
            "llama-doc",  # meta-llama/llama-4-scout:free
            "mistral-small",  # mistralai/mistral-small-3.1-24b-instruct:free
            "maverick",  # meta-llama/llama-4-maverick:free (Llama-Content)
            "llama-technical",  # meta-llama/llama-3.3-70b-instruct:free
            "hermes",  # nousresearch/deephermes-3-llama-3-8b-preview:free
            "molmo",  # allenai/molmo-7b-d:free (Olmo)
            "mistralai",  # mistralai/mistral-7b-instruct:free
            "kimi",  # moonshotai/moonlight-16b-a3b-instruct:free
            "nemotron",  # nvidia/llama-3.1-nemotron-ultra-253b-v1:free
            "gemma",  # google/gemma-3-27b-it:free
            "dolphin",  # cognitivecomputations/dolphin3.0-mistral-24b:free
            "phi"  # microsoft/phi-2:free via Ollama
        ]

        # Display header first
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold cyan]Testing all available models[/bold cyan]\n\n"
                f"Test query: [yellow]{test_query}[/yellow]",
                border_style="cyan"
            ))
        else:
            print("\n=== TESTING ALL MODELS ===")
            print(f"Test query: {test_query}")

        # First test OpenRouter models
        for model in models_to_test:
            try:
                if RICH_AVAILABLE:
                    self.console.print(f"\n[bold blue]Testing model: {model}[/bold blue]")
                else:
                    print(f"\nTesting model: {model}")

                # Set a timeout for each model test to prevent hanging
                try:
                    # Use asyncio.wait_for to set a timeout
                    result = await asyncio.wait_for(
                        self.test_model(model, test_query),
                        timeout=30  # 30 second timeout per model
                    )

                    if result and result.get("success", False):
                        successful_models.append(model)
                    else:
                        failed_models.append(model)
                except asyncio.TimeoutError:
                    # Handle timeout gracefully
                    if RICH_AVAILABLE:
                        self.console.print(f"\n[bold yellow]Timeout testing {model} - taking too long[/bold yellow]")
                    else:
                        print(f"Timeout testing {model} - taking too long")
                    failed_models.append(model)
            except Exception as e:
                if RICH_AVAILABLE:
                    self.console.print(f"\n[bold red]Error testing {model}: {str(e)}[/bold red]")
                else:
                    print(f"Error testing {model}: {str(e)}")
                failed_models.append(model)
                # Continue with the next model regardless of errors

        # Now test main_brain separately since it's our primary model
        # This is CRITICAL - main_brain must be tested separately to ensure it's working
        if RICH_AVAILABLE:
            self.console.print("\n[bold blue]Testing main_brain model (Mistral Small via OpenRouter)...[/bold blue]")
        else:
            print("\nTesting main_brain model (Mistral Small via OpenRouter)...")

        try:
            # Set a timeout for main_brain test to prevent hanging
            try:
                # Use a direct approach to test main_brain
                if self.agent and hasattr(self.agent, 'model_orchestrator') and self.agent.model_orchestrator:
                    # Call main_brain directly with timeout
                    main_brain_result = await asyncio.wait_for(
                        self.agent.model_orchestrator.test_main_brain(test_query),
                        timeout=30  # 30 second timeout
                    )

                    if main_brain_result and main_brain_result.get("success", False):
                        successful_models.append("main_brain")
                        if RICH_AVAILABLE:
                            self.console.print(Panel(
                                f"[bold green]Test successful![/bold green]\n\n[cyan]Query:[/cyan] {test_query}\n\n[yellow]Response:[/yellow] {main_brain_result.get('content', 'No content')}",
                                title="Model Test: main_brain (Mistral Small via OpenRouter)",
                                border_style="green"
                            ))
                        else:
                            print("Model: main_brain (Mistral Small via OpenRouter)")
                            print(f"Response: {main_brain_result.get('content', 'No content')}")
                    else:
                        failed_models.append("main_brain")
                        if RICH_AVAILABLE:
                            self.console.print(Panel(
                                f"[bold red]Test failed![/bold red]\n\n[cyan]Query:[/cyan] {test_query}\n\n[red]Error:[/red] {main_brain_result.get('error', 'Unknown error')}",
                                title="Model Test: main_brain (Mistral Small via OpenRouter)",
                                border_style="red"
                            ))
                        else:
                            print("Error: main_brain test failed")
                            print(f"Details: {main_brain_result.get('error', 'Unknown error')}")
                else:
                    failed_models.append("main_brain")
                    if RICH_AVAILABLE:
                        self.console.print(Panel(
                            f"[bold yellow]Model orchestrator not available for main_brain test[/bold yellow]",
                            title="Model Test: main_brain (Mistral Small via OpenRouter)",
                            border_style="yellow"
                        ))
                    else:
                        print("Model orchestrator not available for main_brain test")
            except asyncio.TimeoutError:
                # Handle timeout gracefully
                failed_models.append("main_brain")
                if RICH_AVAILABLE:
                    self.console.print(Panel(
                        f"[bold yellow]Timeout testing main_brain - taking too long[/bold yellow]",
                        title="Model Test: main_brain (Mistral Small via OpenRouter)",
                        border_style="yellow"
                    ))
                else:
                    print("Timeout testing main_brain - taking too long")
        except Exception as e:
            # Catch any outer exceptions but continue with the test summary
            failed_models.append("main_brain")
            if RICH_AVAILABLE:
                self.console.print(Panel(
                    f"[bold red]Unexpected error during main_brain test: {str(e)}[/bold red]",
                    title="Model Test: main_brain (Mistral Small via OpenRouter)",
                    border_style="red"
                ))
            else:
                print(f"Unexpected error during main_brain test: {str(e)}")

        # Calculate total models (OpenRouter + main_brain)
        total_models = len(models_to_test) + 1  # +1 for main_brain

        # Display summary
        if RICH_AVAILABLE:
            self.console.print(Panel(
                f"[bold cyan]Test Summary[/bold cyan]\n\n"
                f"Successful models: [green]{len(successful_models)}/{total_models}[/green]\n\n"
                + (f"Working models: [green]{', '.join(successful_models)}[/green]\n\n" if successful_models else "")
                + (f"Failed models: [red]{', '.join(failed_models)}[/red]" if failed_models else ""),
                border_style="cyan"
            ))
        else:
            print("\n=== TEST SUMMARY ===")
            print(f"Successful models: {len(successful_models)}/{total_models}")
            if successful_models:
                print(f"Working models: {', '.join(successful_models)}")
            if failed_models:
                print(f"Failed models: {', '.join(failed_models)}")

    def display_help(self):
        """
        Display help information
        """
        if not RICH_AVAILABLE:
            print("\n=== CLI UI HELP ===")
            print("Available commands:")
            print("  vitals - Display system vitals")
            print("  models - Display model status")
            print("  test [model] - Test a specific model")
            print("  test all - Test all models")
            print("  test main_brain - Test the main brain API key (OpenRouter)")
            print("  test gemini - Test the OpenRouter API key for Mistral Small (renamed from Gemini for compatibility)")
            print("  test intent [query] - Test intent classification")
            print("  check - Run a comprehensive system check")
            print("  ollama status - Check Ollama status")
            print("  ollama on - Start Ollama service")
            print("  ollama off - Stop Ollama service")
            print("  ollama pull [model] - Pull a model from Ollama")
            print("  help - Display this help message")
            print("  exit - Exit the CLI UI")
            print("\nYou can also just chat naturally! Any text that's not a command will be treated as a conversation with the AI.")
            return

        # Create a table for commands
        table = Table(title="CLI UI Commands")

        # Add columns
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")

        # Add rows
        table.add_row("vitals", "Display system vitals")
        table.add_row("models", "Display model status")
        table.add_row("test [model]", "Test a specific model")
        table.add_row("test all", "Test all models")
        table.add_row("test main_brain", "Test the main brain API key (OpenRouter)")
        table.add_row("test gemini", "Test the OpenRouter API key for Mistral Small (renamed from Gemini for compatibility)")
        table.add_row("test intent [query]", "Test intent classification")
        table.add_row("check", "Run a comprehensive system check")
        table.add_row("ollama status", "Check Ollama status")
        table.add_row("ollama on", "Start Ollama service")
        table.add_row("ollama off", "Stop Ollama service")
        table.add_row("ollama pull [model]", "Pull a model from Ollama")
        table.add_row("help", "Display this help message")
        table.add_row("exit", "Exit the CLI UI")

        # Print the table
        self.console.print(Panel(
            "[bold cyan]P.U.L.S.E. CLI UI[/bold cyan]\n\n"
            "This interface allows you to monitor system status and test models.\n"
            "Use the commands below to navigate the interface.\n\n"
            "[bold green]You can also just chat naturally![/bold green] Any text that's not a command will be treated as a conversation with the AI.",
            title="Help",
            border_style="cyan"
        ))
        self.console.print(table)

    async def run(self):
        """
        Run the CLI UI
        """
        if not RICH_AVAILABLE:
            print("\n=== P.U.L.S.E. CLI UI ===")
            print("Warning: Rich library not available. Using plain text interface.")
            print("Install rich for a better experience: pip install rich")
        else:
            # Get system status for header
            try:
                from utils.system_utils import get_system_status
                system_status = get_system_status()
                memory = system_status['memory']
                cpu = system_status['cpu']

                # Format memory values
                try:
                    memory_used = float(memory['used'].split('GB')[0])
                    memory_total = float(memory['total'].split('GB')[0])
                    memory_str = f"{memory_used:.1f}/{memory_total:.1f}GB"
                except:
                    memory_str = f"{memory['used']}/{memory['total']}"

                # Create the P.U.L.S.E. header
                header = f"""
╭──────────────────────────────────────────╮
│ Prime Uminda's Learning System Engine    │
│ ver 2.1 | Memory: {memory_str} | CPU: {cpu['percent']}%     │
╰──────────────────────────────────────────╯
                """
                self.console.print(header)
            except Exception as e:
                # Fallback if we can't get system status
                self.console.print("""
╭──────────────────────────────────────────╮
│ Prime Uminda's Learning System Engine    │
│ ver 2.1 | Memory: 6.1/8GB | CPU: 55%     │
╰──────────────────────────────────────────╯
                """)

            self.console.print(Panel(
                "[bold cyan]Welcome to P.U.L.S.E. CLI UI[/bold cyan]\n\n"
                "This interface allows you to monitor system status and test models.\n"
                "Type [bold]help[/bold] to see available commands.",
                border_style="cyan"
            ))

        # Display initial system check
        await self.run_system_check()

        # Main loop
        while True:
            try:
                # Get input using prompt_toolkit if available, otherwise use standard input
                try:
                    if PROMPT_TOOLKIT_AVAILABLE:
                        # Use prompt_toolkit for better input handling
                        prompt_text = "[bold cyan]pulse-cli>[/bold cyan] " if RICH_AVAILABLE else "pulse-cli> "
                        command = await self.prompt_session.prompt_async(prompt_text)
                        command = command.strip().lower()
                    else:
                        # Use a more reliable approach for standard input
                        if RICH_AVAILABLE:
                            self.console.print("[bold cyan]pulse-cli>[/bold cyan] ", end="", flush=True)
                        else:
                            print("\npulse-cli> ", end="", flush=True)

                        # Read directly from stdin to avoid buffering issues
                        command = ""
                        while True:
                            char = sys.stdin.read(1)
                            if char == '\n':
                                break
                            command += char

                        command = command.strip().lower()
                except EOFError:
                    # Handle EOF (Ctrl+D)
                    command = "exit"
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    if RICH_AVAILABLE:
                        self.console.print("\n[bold yellow]Operation cancelled.[/bold yellow]")
                    else:
                        print("\nOperation cancelled.")
                    command = ""

                if command == "exit":
                    break
                elif command == "help":
                    self.display_help()
                elif command == "vitals":
                    from utils.system_utils import get_system_status
                    self.display_system_vitals(get_system_status())
                elif command == "models":
                    if self.agent and self.agent.model_orchestrator:
                        model_stats = self.agent.model_orchestrator.get_usage_stats()
                        available_models = self.agent.model_orchestrator.get_available_models()
                        self.display_model_status(model_stats, available_models)
                        self.display_openrouter_models(self.agent.model_orchestrator)
                    else:
                        print("No model orchestrator available")
                elif command.startswith("test "):
                    model_name = command[5:].strip()
                    if model_name == "all":
                        await self.test_all_models()
                    elif model_name == "gemini":
                        # Redirect Gemini to Mistral Small via OpenRouter
                        if RICH_AVAILABLE:
                            self.console.print("\n[bold yellow]Note: 'gemini' is deprecated. Redirecting to Mistral Small via OpenRouter.[/bold yellow]")
                        else:
                            print("\nNote: 'gemini' is deprecated. Redirecting to Mistral Small via OpenRouter.")
                        await self.test_model("mistral-small")
                    elif model_name == "mistral":
                        # Test Mistral separately as the main brain via OpenRouter
                        if RICH_AVAILABLE:
                            self.console.print("\n[bold blue]Testing Mistral-Small model via OpenRouter...[/bold blue]")
                        else:
                            print("\nTesting Mistral-Small model via OpenRouter...")
                        # Use the test_main_brain method to test Mistral
                        await self.test_main_brain_api_key()
                    else:
                        # Extract the actual model name if there are additional words
                        # This handles cases like "test mistral what's the latest in AI"
                        if " " in model_name:
                            actual_model = model_name.split(" ")[0]
                            if RICH_AVAILABLE:
                                self.console.print(f"\n[bold yellow]Note: Testing only model '{actual_model}', ignoring additional text.[/bold yellow]")
                            else:
                                print(f"\nNote: Testing only model '{actual_model}', ignoring additional text.")
                            await self.test_model(actual_model)
                        else:
                            await self.test_model(model_name)
                elif command == "check":
                    await self.run_system_check()
                elif command.startswith("ollama "):
                    await self.handle_ollama_command(command[7:].strip())
                elif command in ["enable offline mode", "disable offline mode", "toggle offline mode"]:
                    enable = "enable" in command or "toggle" in command
                    await self.handle_offline_mode(enable)
                elif command.startswith("test intent "):
                    query = command[12:].strip()  # Remove "test intent " prefix
                    await self.test_intent(query)
                elif command == "test main_brain":
                    await self.test_main_brain_api_key()
                elif command == "test gemini":
                    # For backward compatibility, redirect to main_brain test
                    if RICH_AVAILABLE:
                        self.console.print("\n[bold yellow]Note: 'test gemini' is deprecated. Using 'test main_brain' instead.[/bold yellow]")
                    else:
                        print("\nNote: 'test gemini' is deprecated. Using 'test main_brain' instead.")
                    await self.test_main_brain_api_key()
                else:
                    # Handle as natural language query
                    await self.handle_natural_language(command)
            except Exception as e:
                if RICH_AVAILABLE:
                    self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
                else:
                    print(f"Error: {str(e)}")

        # Exit message
        if RICH_AVAILABLE:
            self.console.print("[bold cyan]Exiting CLI UI. Goodbye![/bold cyan]")
        else:
            print("\nExiting CLI UI. Goodbye!")

    async def handle_ollama_command(self, command: str) -> None:
        """
        Handle Ollama commands

        Args:
            command: Ollama command to execute
        """
        if not self.agent or not hasattr(self.agent, 'model_interface'):
            if RICH_AVAILABLE:
                self.console.print("[bold red]Cannot execute Ollama command: No model interface available[/bold red]")
            else:
                print("Cannot execute Ollama command: No model interface available")
            return

        try:
            if command == "status":
                status = await self.agent.model_interface.check_status()
                ollama_status = status.get("ollama", {})
                offline_mode = status.get("offline_mode", False)
                distilbert_available = status.get("distilbert_available", False)
                distilbert_initialized = status.get("distilbert_initialized", False)
                internet_available = status.get("internet_available", False)

                if RICH_AVAILABLE:
                    if ollama_status.get("running", False):
                        models_str = ", ".join(ollama_status.get("models", [])) if ollama_status.get("models", []) else "None"
                        memory_usage = f"{ollama_status.get('memory_usage', 0):.2f}GB" if ollama_status.get('memory_usage', 0) > 0 else "Unknown"
                        system_memory = ollama_status.get("system_memory", {})
                        free_memory = system_memory.get("free_gb", 0)
                        memory_percent = system_memory.get("percent_used", 0)

                        status_color = "green"
                        status_text = "Running"
                        if offline_mode:
                            status_text += " (Offline Mode)"

                        self.console.print(Panel(
                            f"[bold green]🚀 Ollama Status: {status_text}[/bold green]\n\n"
                            f"Models Loaded: {models_str}\n"
                            f"Memory Usage: {memory_usage}\n"
                            f"System Memory: {free_memory:.2f}GB free ({memory_percent}% used)\n"
                            f"Internet: {'✅ Available' if internet_available else '❌ Not Available'}\n"
                            f"DistilBERT: {'✅ Available' if distilbert_available else '❌ Not Available'} {'(Initialized)' if distilbert_initialized else ''}",
                            title="Ollama",
                            border_style=status_color
                        ))
                    else:
                        # Always use yellow for not running status
                        status_color = "yellow"
                        message = "[bold yellow]🛑 Ollama Status: Not Running"
                        if offline_mode:
                            message += " (Offline Mode)"
                        message += "[/bold yellow]"

                        system_memory = ollama_status.get("system_memory", {})
                        free_memory = system_memory.get("free_gb", 0)
                        memory_percent = system_memory.get("percent_used", 0)

                        if not ollama_status.get("executable_found", True):
                            message += "\n\nOllama executable not found. Please install Ollama from https://ollama.com"

                        if ollama_status.get("error"):
                            message += f"\n\nError: {ollama_status['error']}"

                        message += f"\n\nSystem Memory: {free_memory:.2f}GB free ({memory_percent}% used)\n"
                        message += f"Internet: {'✅ Available' if internet_available else '❌ Not Available'}\n"
                        message += f"DistilBERT: {'✅ Available' if distilbert_available else '❌ Not Available'} {'(Initialized)' if distilbert_initialized else ''}"

                        self.console.print(Panel(message, title="Ollama", border_style=status_color))
                else:
                    status_text = "Running" if ollama_status.get("running", False) else "Not Running"
                    if offline_mode:
                        status_text += " (Offline Mode)"

                    print(f"🚀 Ollama Status: {status_text}")

                    if ollama_status.get("running", False):
                        models_str = ", ".join(ollama_status.get("models", [])) if ollama_status.get("models", []) else "None"
                        memory_usage = f"{ollama_status.get('memory_usage', 0):.2f}GB" if ollama_status.get('memory_usage', 0) > 0 else "Unknown"
                        print(f"Models Loaded: {models_str}")
                        print(f"Memory Usage: {memory_usage}")
                    else:
                        if not ollama_status.get("executable_found", True):
                            print("Ollama executable not found. Please install Ollama from https://ollama.com")
                        if ollama_status.get("error"):
                            print(f"Error: {ollama_status['error']}")

                    system_memory = ollama_status.get("system_memory", {})
                    free_memory = system_memory.get("free_gb", 0)
                    memory_percent = system_memory.get("percent_used", 0)
                    print(f"System Memory: {free_memory:.2f}GB free ({memory_percent}% used)")
                    print(f"Internet: {'Available' if internet_available else 'Not Available'}")
                    print(f"DistilBERT: {'Available' if distilbert_available else 'Not Available'} {'(Initialized)' if distilbert_initialized else ''}")

            elif command == "on":
                result = await self.agent.model_interface.start_ollama()
                if RICH_AVAILABLE:
                    if result["success"]:
                        self.console.print(f"[bold green]🚀 {result['message']}[/bold green]")
                    else:
                        self.console.print(f"[bold red]❌ {result['message']}[/bold red]")
                else:
                    if result["success"]:
                        print(f"🚀 {result['message']}")
                    else:
                        print(f"❌ {result['message']}")

                # Also enable offline mode
                await self.agent.model_interface.toggle_offline_mode(True)

            elif command == "off":
                # First disable offline mode
                await self.agent.model_interface.toggle_offline_mode(False)

                # Then stop the service
                result = await self.agent.model_interface.stop_ollama()
                if RICH_AVAILABLE:
                    if result["success"]:
                        self.console.print(f"[bold yellow]🛑 {result['message']}[/bold yellow]")
                    else:
                        self.console.print(f"[bold red]❌ {result['message']}[/bold red]")
                else:
                    if result["success"]:
                        print(f"🛑 {result['message']}")
                    else:
                        print(f"❌ {result['message']}")

            elif command.startswith("pull "):
                model_name = command[5:].strip()
                if RICH_AVAILABLE:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"[bold blue]Pulling model {model_name}...[/bold blue]"),
                        console=self.console
                    ) as progress:
                        progress.add_task("Pulling...", total=None)
                        result = await self.agent.model_interface.pull_ollama_model(model_name)
                else:
                    print(f"Pulling model {model_name}...")
                    result = await self.agent.model_interface.pull_ollama_model(model_name)

                if RICH_AVAILABLE:
                    if result["success"]:
                        self.console.print(f"[bold green]✅ {result['message']}[/bold green]")
                    else:
                        self.console.print(f"[bold red]❌ {result['message']}[/bold red]")
                else:
                    if result["success"]:
                        print(f"✅ {result['message']}")
                    else:
                        print(f"❌ {result['message']}")
            else:
                if RICH_AVAILABLE:
                    self.console.print("[bold red]Unknown Ollama command. Available commands: status, on, off, pull [model][/bold red]")
                else:
                    print("Unknown Ollama command. Available commands: status, on, off, pull [model]")

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error executing Ollama command: {str(e)}[/bold red]")
            else:
                print(f"Error executing Ollama command: {str(e)}")

        # End of handle_ollama_command

    async def handle_natural_language(self, query: str) -> None:
        """
        Handle natural language queries by passing them to the Pulse Agent

        Args:
            query: The natural language query
        """
        if not self.agent:
            if RICH_AVAILABLE:
                self.console.print("[bold red]Cannot process query: No agent available[/bold red]")
            else:
                print("Cannot process query: No agent available")
            return

        try:
            # Show a spinner while processing
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Processing...[/bold blue]"),
                    console=self.console
                ) as progress:
                    progress.add_task("Processing...", total=None)

                    # Process the query with the agent
                    response = await self.agent.process_input(query)
            else:
                print("Processing...")
                # Process the query with the agent
                response = await self.agent.process_input(query)

            # Display the response
            if RICH_AVAILABLE:
                self.console.print(Panel(
                    f"{response}",
                    title="Response",
                    border_style="green"
                ))
            else:
                print(f"\n{response}")

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error processing query: {str(e)}[/bold red]")
            else:
                print(f"Error processing query: {str(e)}")

    async def test_intent(self, query: str) -> None:
        """
        Test intent classification for a query

        Args:
            query: The query to classify
        """
        if not self.agent or not hasattr(self.agent, 'intent_handler'):
            if RICH_AVAILABLE:
                self.console.print("[bold red]Cannot test intent: No intent handler available[/bold red]")
            else:
                print("Cannot test intent: No intent handler available")
            return

        try:
            # Show a spinner while processing
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Classifying intent...[/bold blue]"),
                    console=self.console
                ) as progress:
                    progress.add_task("Classifying...", total=None)

                    # Classify the intent
                    intent = await self.agent.intent_handler.classify(query)
            else:
                print("Classifying intent...")
                # Classify the intent
                intent = await self.agent.intent_handler.classify(query)

            # Display the result
            if RICH_AVAILABLE:
                self.console.print(Panel(
                    f"[bold cyan]Query:[/bold cyan] {query}\n\n[bold green]Intent:[/bold green] {intent}",
                    title="Intent Classification",
                    border_style="green"
                ))
            else:
                print(f"\nQuery: {query}")
                print(f"Intent: {intent}")

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error classifying intent: {str(e)}[/bold red]")
            else:
                print(f"Error classifying intent: {str(e)}")

    async def test_main_brain_api_key(self) -> None:
        """
        Test the OpenRouter API key for the main brain (Mistral Small) and run a test query
        """
        if not self.agent or not hasattr(self.agent, 'model_orchestrator'):
            if RICH_AVAILABLE:
                self.console.print("[bold red]Cannot test OpenRouter API key for main brain: No model orchestrator available[/bold red]")
            else:
                print("Cannot test OpenRouter API key for main brain: No model orchestrator available")
            return

        try:
            # Show a spinner while testing
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Testing OpenRouter API key for main brain (Mistral Small)...[/bold blue]"),
                    console=self.console
                ) as progress:
                    progress.add_task("Testing...", total=None)

                    # Test the API key
                    result = await self.agent.model_orchestrator.check_openrouter_api_key()
            else:
                print("Testing OpenRouter API key for main brain (Mistral Small)...")
                # Test the API key
                result = await self.agent.model_orchestrator.check_openrouter_api_key()

            # Display the result
            if result["success"]:
                if RICH_AVAILABLE:
                    self.console.print(Panel(
                        f"[bold green]✅ OpenRouter API key for main brain (Mistral Small) is valid![/bold green]\n\n"
                        f"[bold cyan]Test response:[/bold cyan] {result.get('response', 'No response')}",
                        title="OpenRouter API Key Test for Main Brain",
                        border_style="green"
                    ))
                else:
                    print("\n✅ OpenRouter API key for main brain (Mistral Small) is valid!")
                    print(f"Test response: {result.get('response', 'No response')}")

                # Now test Mistral-Small model with a query
                if RICH_AVAILABLE:
                    self.console.print("\n[bold blue]Testing Mistral-Small model via OpenRouter with query: What is machine learning? Keep it brief.[/bold blue]")
                else:
                    print("\nTesting Mistral-Small model via OpenRouter with query: What is machine learning? Keep it brief.")

                # Call Mistral-Small directly through the model orchestrator
                test_query = "What is machine learning? Keep it brief."
                mistral_result = await asyncio.wait_for(
                    self.agent.model_orchestrator.test_main_brain(test_query),
                    timeout=30  # 30 second timeout
                )

                if mistral_result and mistral_result.get("success", False):
                    if RICH_AVAILABLE:
                        self.console.print(Panel(
                            f"[bold green]Test successful![/bold green]\n\n[cyan]Query:[/cyan] {test_query}\n\n[yellow]Response:[/yellow] {mistral_result.get('content', '')}\n\n[dim]Model: {mistral_result.get('model_id', 'mistralai/mistral-small-3.1-24b-instruct:free')}[/dim]",
                            title="Mistral-Small via OpenRouter Test",
                            border_style="green"
                        ))
                    else:
                        print("\nTest successful!")
                        print(f"Query: {test_query}")
                        print(f"Response: {mistral_result.get('content', '')}")
                        print(f"Model: {mistral_result.get('model_id', 'mistralai/mistral-small-3.1-24b-instruct:free')}")
                else:
                    if RICH_AVAILABLE:
                        self.console.print(Panel(
                            f"[bold red]Test failed![/bold red]\n\n[cyan]Query:[/cyan] {test_query}\n\n[red]Error:[/red] {mistral_result.get('error', 'Unknown error')}",
                            title="Mistral-Small via OpenRouter Test",
                            border_style="red"
                        ))
                    else:
                        print("\nTest failed!")
                        print(f"Query: {test_query}")
                        print(f"Error: {mistral_result.get('error', 'Unknown error')}")
            else:
                if RICH_AVAILABLE:
                    self.console.print(Panel(
                        f"[bold red]❌ OpenRouter API key test for main brain (Mistral Small) failed![/bold red]\n\n"
                        f"[bold cyan]Error:[/bold cyan] {result.get('error', 'Unknown error')}\n"
                        f"[bold cyan]Message:[/bold cyan] {result.get('message', 'No message')}",
                        title="OpenRouter API Key Test for Main Brain",
                        border_style="red"
                    ))
                else:
                    print("\n❌ OpenRouter API key test for main brain (Mistral Small) failed!")
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    print(f"Message: {result.get('message', 'No message')}")

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error testing OpenRouter API key for main brain: {str(e)}[/bold red]")
            else:
                print(f"Error testing OpenRouter API key for main brain: {str(e)}")

    async def test_gemini_api_key(self) -> None:
        """
        Test the OpenRouter API key for Mistral Small (renamed from Gemini for backward compatibility)
        """
        if not self.agent or not hasattr(self.agent, 'model_orchestrator'):
            if RICH_AVAILABLE:
                self.console.print("[bold red]Cannot test OpenRouter API key for Mistral Small: No model orchestrator available[/bold red]")
            else:
                print("Cannot test OpenRouter API key for Mistral Small: No model orchestrator available")
            return

        try:
            # Show a spinner while testing
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Testing OpenRouter API key for Mistral Small...[/bold blue]"),
                    console=self.console
                ) as progress:
                    progress.add_task("Testing...", total=None)

                    # Test the API key
                    result = await self.agent.model_orchestrator.check_gemini_api_key()
            else:
                print("Testing OpenRouter API key for Mistral Small...")
                # Test the API key
                result = await self.agent.model_orchestrator.check_gemini_api_key()

            # Display the result
            if result["success"]:
                if RICH_AVAILABLE:
                    self.console.print(Panel(
                        f"[bold green]✅ OpenRouter API key for Mistral Small is valid![/bold green]\n\n"
                        f"[bold cyan]Test response:[/bold cyan] {result.get('response', 'No response')}",
                        title="OpenRouter API Key Test for Mistral Small",
                        border_style="green"
                    ))
                else:
                    print("\n✅ OpenRouter API key for Mistral Small is valid!")
                    print(f"Test response: {result.get('response', 'No response')}")
            else:
                if RICH_AVAILABLE:
                    self.console.print(Panel(
                        f"[bold red]❌ OpenRouter API key test for Mistral Small failed![/bold red]\n\n"
                        f"[bold cyan]Error:[/bold cyan] {result.get('error', 'Unknown error')}\n"
                        f"[bold cyan]Message:[/bold cyan] {result.get('message', 'No message')}",
                        title="OpenRouter API Key Test for Mistral Small",
                        border_style="red"
                    ))
                else:
                    print("\n❌ OpenRouter API key test for Mistral Small failed!")
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    print(f"Message: {result.get('message', 'No message')}")

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[bold red]Error testing OpenRouter API key for Mistral Small: {str(e)}[/bold red]")
            else:
                print(f"Error testing OpenRouter API key for Mistral Small: {str(e)}")