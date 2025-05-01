"""
Test script for P.U.L.S.E. (Prime Uminda's Learning System Engine) core components
"""

import os
import sys
import json
import datetime
import logging
import anyio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - P.U.L.S.E. - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("test_run.log"),
        logging.StreamHandler()
    ]
)

# Import core components
from skills.task_memory_manager import TaskMemoryManager
from skills.prompt_generator import PromptGenerator
from utils.logger import default_logger as logger

def test_portfolio_workflow():
    """Test a complete portfolio creation workflow."""

    logger.info("=== Starting Portfolio Creation Workflow Test ===")

    # Initialize components
    task_manager = TaskMemoryManager()
    prompt_generator = PromptGenerator()

    # Step 1: Create a task
    logger.info("Step 1: Creating main task")
    task_id = task_manager.create_task(
        name="Portfolio Website for Alex",
        description="Create a modern personal portfolio site for Alex that showcases 2025 design trends",
        task_type="code",
        priority=2,
        tags=["portfolio", "website", "frontend", "nextjs"]
    )

    # Step 2: Create subtasks
    logger.info("Step 2: Creating subtasks")
    design_subtask_id = task_manager.create_subtask(
        task_id=task_id,
        name="Research design trends",
        description="Research latest design trends for 2025 portfolio sites",
        priority=1
    )

    tech_subtask_id = task_manager.create_subtask(
        task_id=task_id,
        name="Choose tech stack",
        description="Select the optimal tech stack for a modern portfolio",
        priority=1
    )

    content_subtask_id = task_manager.create_subtask(
        task_id=task_id,
        name="Generate content",
        description="Create bio and project descriptions",
        priority=2
    )

    # Step 3: Agent dispatch - store responses
    logger.info("Step 3: Dispatching to agents and storing their responses")

    # DeepSeek response for tech stack
    deepseek_response = {
        "framework": "Next.js",
        "technologies": ["React", "Tailwind CSS", "Framer Motion", "Supabase"],
        "styling": "Tailwind CSS with custom theme",
        "animation": "Framer Motion for page transitions",
        "reasoning": "Next.js App Router provides the best balance of performance, SEO, and developer experience for a portfolio site. Supabase offers auth, storage, and a lightweight database without vendor lock-in."
    }

    task_manager.add_agent_response(
        agent="deepseek",
        response=json.dumps(deepseek_response),
        task_id=task_id,
        subtask_id=tech_subtask_id,
        response_type="json"
    )

    # Grok response for design trends
    grok_response = {
        "trends": [
            {"name": "Neobrutalism", "description": "Bold typography, bright colors, raw edges, and playful imperfections", "vibe_score": 9},
            {"name": "Glassmorphism", "description": "Frosted glass effect with depth and translucency", "vibe_score": 8},
            {"name": "Kinetic Typography", "description": "Text that moves and responds to user interaction", "vibe_score": 10},
            {"name": "3D Elements", "description": "Subtle 3D objects that enhance rather than overwhelm", "vibe_score": 9},
            {"name": "Soft Gradients", "description": "Subtle color transitions in backgrounds and UI elements", "vibe_score": 7}
        ],
        "analysis": "Portfolios in 2025 need to balance tech flex with personality. Neobrutalism with subtle 3D elements is trending hard on Dribbble. Every designer has dark mode now - so think about unique toggles or transitions between modes. Voice-activated theme switching would set it apart.",
        "vibe_score": 9
    }

    task_manager.add_agent_response(
        agent="grok",
        response=json.dumps(grok_response),
        task_id=task_id,
        subtask_id=design_subtask_id,
        response_type="json"
    )

    # Claude response for content
    claude_response = {
        "bio": "Alex is a creative developer who blends code and design to build unique digital experiences. With expertise in frontend architecture and interactive animations, Alex transforms concepts into engaging web applications that prioritize both aesthetics and performance.",
        "projects": [
            {
                "title": "Neurosync",
                "description": "An interactive data visualization platform that transforms neural network activity into immersive visual experiences."
            },
            {
                "title": "Ambient",
                "description": "A minimalist productivity suite featuring context-aware notifications and ambient computing principles."
            }
        ],
        "tone": "Professional with personality - technical credibility balanced with creative energy."
    }

    task_manager.add_agent_response(
        agent="claude",
        response=json.dumps(claude_response),
        task_id=task_id,
        subtask_id=content_subtask_id,
        response_type="json"
    )

    # Step 4: Update vibe score based on Grok's analysis
    logger.info("Step 4: Updating task vibe score")
    task_manager.update_task_vibe_score(task_id, grok_response["vibe_score"], "grok")

    # Step 5: Generate combined prompt for Cursor
    logger.info("Step 5: Generating combined Cursor prompt")

    # Prepare data for prompt
    task_data = task_manager.get_task(task_id)

    # Parse agent responses
    agent_responses = task_manager.get_agent_responses(task_id=task_id)
    model_outputs = {}

    for response in agent_responses:
        model_outputs[response["agent"]] = json.loads(response["response"])

    # Create a prompt for Cursor
    try:
        # First ensure we have the combined_portfolio template
        if "combined_portfolio" not in prompt_generator.list_templates():
            logger.warning("combined_portfolio template not found - would create here in production")

        # Generate combined prompt
        cursor_prompt = prompt_generator.combine_model_outputs(model_outputs, "portfolio")
        logger.info(f"Generated Cursor prompt: {cursor_prompt[:100]}...")
    except Exception as e:
        logger.error(f"Error generating Cursor prompt: {str(e)}")
        cursor_prompt = "Error generating prompt"

    # Step 6: Update task status
    logger.info("Step 6: Updating task status")
    task_manager.update_subtask_status(design_subtask_id, "completed")
    task_manager.update_subtask_status(tech_subtask_id, "completed")
    task_manager.update_subtask_status(content_subtask_id, "completed")

    # Step 7: Get task summary and next actions
    logger.info("Step 7: Generating task summary and next actions")
    summary = task_manager.get_task_summary(task_id)
    next_actions = task_manager.predict_next_actions(task_id)

    # Print summary information
    print("\n=== Task Summary ===")
    print(f"Task: {summary['task']['name']}")
    print(f"Description: {summary['task']['description']}")
    print(f"Vibe Score: {summary['stats']['vibe_score']}/10")
    print(f"Completion: {summary['stats']['completion_percentage']}%")

    print("\n=== Subtasks ===")
    for subtask in summary['subtasks']:
        print(f"- {subtask['name']} ({subtask['status']})")

    print("\n=== Cursor Prompt ===")
    print(cursor_prompt)

    print("\n=== Next Actions ===")
    for action in next_actions:
        if action['type'] == 'complete_subtask':
            print(f"- Complete subtask: {action['name']}")
        elif action['type'] == 'get_agent_response':
            print(f"- Get input from {action['agent']}: {action['reason']}")

    logger.info("=== Portfolio Creation Workflow Test Completed ===")

    # Close connection
    task_manager.close()

    return {
        "task_id": task_id,
        "cursor_prompt": cursor_prompt,
        "summary": summary,
        "next_actions": next_actions
    }

async def test_async_model_interface():
    """Test the async capabilities of the ModelInterface."""
    logger.info("Starting async model interface test")

    # Initialize the ModelInterface and TaskMemoryManager
    from skills.model_interface import ModelInterface
    from skills.task_memory_manager import TaskMemoryManager

    model_interface = ModelInterface(simulate_responses=True)
    task_manager = TaskMemoryManager()

    # Create prompts for different models
    prompts = {
        "claude": "Analyze the following code and suggest performance improvements:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
        "deepseek": "Write a Python function to efficiently calculate the nth Fibonacci number using memoization.",
        "grok": "Compare recursive vs iterative approaches for calculating Fibonacci numbers."
    }

    # Call the models concurrently
    logger.info("Calling multiple models concurrently")
    start_time = datetime.now()

    results = await model_interface.call_models_concurrently(prompts)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Log the results
    logger.info(f"Concurrent model calls completed in {duration:.2f} seconds")
    for model, result in results.items():
        response = result.get("response", "")
        first_line = response.split("\n")[0] if response else ""
        logger.info(f"{model.capitalize()} response (first line): {first_line}")

    # Test individual async calls
    logger.info("Testing individual async calls")
    start_time = datetime.now()

    deepseek_result = await model_interface.call_model_api_async("deepseek", prompts["deepseek"])

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Individual async call completed in {duration:.2f} seconds")

    # Create a new task and subtasks asynchronously
    logger.info("Testing async task management operations")

    # Create a main task asynchronously
    task_id = await task_manager.create_task_async(
        name="Optimize Fibonacci Algorithm",
        description="Create an efficient implementation of the Fibonacci sequence calculation",
        task_type="code",
        priority=1,
        tags=["algorithm", "optimization", "python"]
    )

    # Create subtasks asynchronously
    async with anyio.create_task_group() as tg:
        # Start multiple async operations concurrently
        logger.info("Creating subtasks and adding agent responses concurrently")

        # These will all run concurrently
        subtask1_future = tg.start_soon(
            task_manager.create_subtask_async,
            task_id,
            "Research efficient algorithms",
            "Investigate dynamic programming and memoization approaches"
        )

        subtask2_future = tg.start_soon(
            task_manager.create_subtask_async,
            task_id,
            "Implement solution",
            "Write the optimized Fibonacci function"
        )

        subtask3_future = tg.start_soon(
            task_manager.create_subtask_async,
            task_id,
            "Write tests",
            "Create unit tests to verify correctness and measure performance"
        )

    # Now add agent responses concurrently
    async with anyio.create_task_group() as tg:
        # Add the model responses to the task
        for model, result in results.items():
            tg.start_soon(
                task_manager.add_agent_response_async,
                model,
                result.get("response", "No response"),
                task_id,
                None,  # No subtask ID
                "text"
            )

    # Get the responses asynchronously
    responses = await task_manager.get_agent_responses_async(task_id=task_id)
    logger.info(f"Retrieved {len(responses)} agent responses for task {task_id}")

    # Update task vibe score based on Grok's analysis (simulated score)
    await task_manager.update_task_vibe_score_async(task_id, 8, "grok", "Good optimization approach with clear explanation")

    # Compare with sequential calls if not in simulation mode
    if not model_interface.simulate_responses:
        logger.info("Testing sequential model calls for comparison")
        start_time = datetime.now()

        sequential_results = {}
        for model, prompt in prompts.items():
            sequential_results[model] = await model_interface.call_model_api_async(model, prompt)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Sequential model calls completed in {duration:.2f} seconds")

    logger.info("Async model interface test completed")

    # Clean up
    task_manager.close()

    return {"model_results": results, "task_id": task_id}

if __name__ == "__main__":
    # Run existing tests
    test_portfolio_workflow()

    # Run the async test using anyio
    logger.info("Running async test using anyio")
    anyio.run(test_async_model_interface)

    logger.info("All tests completed")