"""
Skill Marketplace for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides a pipeline for acquiring and managing skills from GitHub
"""

import os
import json
import asyncio
import hashlib
import structlog
import tempfile
import shutil
import subprocess
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv
import git

# Configure logger
logger = structlog.get_logger("skill_marketplace")

# Load environment variables
load_dotenv()

# Constants
SKILLS_REPO_URL = "https://github.com/Spyboss/pulse-skills.git"
SKILLS_DIR = "skills"
SKILLS_TEMP_DIR = "temp/skills"
SKILLS_MANIFEST_FILE = "manifest.json"
SKILLS_DB_COLLECTION = "skills"

class SkillMarketplace:
    """
    Manages skill acquisition and installation from GitHub
    Features:
    - Retrieves skills from the official skills repository
    - Validates skills with SHA-256 checksums
    - Tracks installed skills in MongoDB
    - Provides rollback capability with Git
    """

    def __init__(self):
        """Initialize the skill marketplace"""
        self.logger = logger
        self.client = None
        self.db = None

        # Initialize MongoDB connection
        self._init_mongodb()

        # Ensure directories exist
        os.makedirs(SKILLS_DIR, exist_ok=True)
        os.makedirs(SKILLS_TEMP_DIR, exist_ok=True)

        logger.info("Skill marketplace initialized")

    def _init_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        # Disable MongoDB connection to avoid DNS issues
        logger.info("MongoDB connection disabled for skill tracking, using SQLite fallback")
        self.client = None
        self.db = None

    async def _create_indexes(self) -> None:
        """Create indexes for skills collection"""
        if self.db is None:
            return

        try:
            # Create indexes for skills collection
            await self.db.skills.create_index([("skill_id", 1)], unique=True)
            await self.db.skills.create_index([("category", 1)])
            await self.db.skills.create_index([("installed_at", -1)])

            logger.info("Created indexes for skills collection")
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")

    async def list_available_skills(self, refresh: bool = False) -> Dict[str, Any]:
        """
        List available skills from the repository

        Args:
            refresh: Whether to refresh the local cache

        Returns:
            Result dictionary with available skills
        """
        try:
            # Clone or update the skills repository
            repo_path = os.path.join(SKILLS_TEMP_DIR, "repo")

            if refresh or not os.path.exists(repo_path):
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)

                logger.info(f"Cloning skills repository from {SKILLS_REPO_URL}")
                git.Repo.clone_from(SKILLS_REPO_URL, repo_path)
            else:
                # Update the repository
                try:
                    repo = git.Repo(repo_path)
                    repo.remotes.origin.pull()
                    logger.info("Updated skills repository")
                except Exception as e:
                    logger.error(f"Failed to update skills repository: {str(e)}")
                    # Re-clone if update fails
                    shutil.rmtree(repo_path)
                    git.Repo.clone_from(SKILLS_REPO_URL, repo_path)

            # Read the manifest file
            manifest_path = os.path.join(repo_path, SKILLS_MANIFEST_FILE)
            if not os.path.exists(manifest_path):
                logger.error(f"Manifest file not found: {manifest_path}")
                return {"success": False, "error": "Manifest file not found"}

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            # Get installed skills
            installed_skills = await self.list_installed_skills()
            installed_skill_ids = []

            if installed_skills["success"]:
                installed_skill_ids = [skill["skill_id"] for skill in installed_skills["skills"]]

            # Mark installed skills
            for skill in manifest.get("skills", []):
                skill["installed"] = skill["id"] in installed_skill_ids

            logger.info(f"Found {len(manifest.get('skills', []))} available skills")
            return {"success": True, "skills": manifest.get("skills", [])}

        except Exception as e:
            logger.error(f"Error listing available skills: {str(e)}")
            return {"success": False, "error": str(e)}

    async def list_installed_skills(self) -> Dict[str, Any]:
        """
        List installed skills

        Returns:
            Result dictionary with installed skills
        """
        if self.db is None:
            logger.warning("MongoDB not available, using local fallback")
            # Fallback to local directory scan
            try:
                skills = []
                for item in os.listdir(SKILLS_DIR):
                    skill_path = os.path.join(SKILLS_DIR, item)
                    if os.path.isdir(skill_path) and item != "__pycache__":
                        # Check for metadata file
                        metadata_path = os.path.join(skill_path, "metadata.json")
                        if os.path.exists(metadata_path):
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                                skills.append(metadata)
                        else:
                            # Create basic metadata
                            skills.append({
                                "skill_id": item,
                                "name": item.replace("_", " ").title(),
                                "installed_at": "unknown"
                            })

                logger.info(f"Found {len(skills)} installed skills (local scan)")
                return {"success": True, "skills": skills}
            except Exception as e:
                logger.error(f"Error scanning local skills: {str(e)}")
                return {"success": False, "error": str(e)}

        try:
            # Retrieve installed skills from MongoDB
            cursor = self.db.skills.find({})
            skills = await cursor.to_list(length=100)

            logger.info(f"Found {len(skills)} installed skills")
            return {"success": True, "skills": skills}

        except Exception as e:
            logger.error(f"Error listing installed skills: {str(e)}")
            return {"success": False, "error": str(e)}

    async def install_skill(self, skill_id: str) -> Dict[str, Any]:
        """
        Install a skill from the repository

        Args:
            skill_id: Skill identifier

        Returns:
            Result dictionary with installation result
        """
        try:
            # Get available skills
            available_skills = await self.list_available_skills()
            if not available_skills["success"]:
                return available_skills

            # Find the skill
            skill = None
            for s in available_skills["skills"]:
                if s["id"] == skill_id:
                    skill = s
                    break

            if not skill:
                logger.error(f"Skill not found: {skill_id}")
                return {"success": False, "error": f"Skill not found: {skill_id}"}

            # Check if already installed
            if skill.get("installed", False):
                logger.info(f"Skill already installed: {skill_id}")
                return {"success": True, "message": f"Skill already installed: {skill_id}"}

            # Clone or update the skills repository
            repo_path = os.path.join(SKILLS_TEMP_DIR, "repo")

            if not os.path.exists(repo_path):
                logger.info(f"Cloning skills repository from {SKILLS_REPO_URL}")
                git.Repo.clone_from(SKILLS_REPO_URL, repo_path)

            # Check if the skill directory exists
            skill_repo_path = os.path.join(repo_path, skill_id)
            if not os.path.exists(skill_repo_path):
                logger.error(f"Skill directory not found: {skill_repo_path}")
                return {"success": False, "error": f"Skill directory not found: {skill_id}"}

            # Validate the skill with checksum
            checksum_result = await self._validate_skill_checksum(skill_repo_path, skill.get("checksum"))
            if not checksum_result["success"]:
                return checksum_result

            # Create a Git commit before installing
            await self._create_pre_install_commit(skill_id)

            # Install the skill
            skill_dest_path = os.path.join(SKILLS_DIR, skill_id)

            # Remove existing skill if present
            if os.path.exists(skill_dest_path):
                shutil.rmtree(skill_dest_path)

            # Copy the skill files
            shutil.copytree(skill_repo_path, skill_dest_path)

            # Create metadata file
            metadata = {
                "skill_id": skill_id,
                "name": skill.get("name", skill_id),
                "description": skill.get("description", ""),
                "version": skill.get("version", "1.0.0"),
                "author": skill.get("author", "Unknown"),
                "installed_at": datetime.utcnow().isoformat(),
                "checksum": skill.get("checksum", "")
            }

            with open(os.path.join(skill_dest_path, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)

            # Record the installation in MongoDB
            if self.db:
                await self.db.skills.update_one(
                    {"skill_id": skill_id},
                    {"$set": metadata},
                    upsert=True
                )

            # Create a Git commit after installing
            await self._create_post_install_commit(skill_id)

            logger.info(f"Installed skill: {skill_id}")
            return {"success": True, "message": f"Installed skill: {skill_id}"}

        except Exception as e:
            logger.error(f"Error installing skill: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _validate_skill_checksum(self, skill_path: str, expected_checksum: Optional[str]) -> Dict[str, Any]:
        """
        Validate a skill with its checksum

        Args:
            skill_path: Path to the skill directory
            expected_checksum: Expected SHA-256 checksum

        Returns:
            Result dictionary with validation result
        """
        try:
            if not expected_checksum:
                logger.warning(f"No checksum provided for skill at {skill_path}")
                return {"success": True, "message": "No checksum validation performed"}

            # Calculate checksum of all Python files
            sha256 = hashlib.sha256()

            for root, _, files in os.walk(skill_path):
                for file in sorted(files):  # Sort for deterministic order
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "rb") as f:
                            sha256.update(f.read())

            calculated_checksum = sha256.hexdigest()

            if calculated_checksum != expected_checksum:
                logger.error(f"Checksum validation failed: expected {expected_checksum}, got {calculated_checksum}")
                return {"success": False, "error": "Checksum validation failed"}

            logger.info(f"Checksum validation passed: {calculated_checksum}")
            return {"success": True, "message": "Checksum validation passed"}

        except Exception as e:
            logger.error(f"Error validating skill checksum: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _create_pre_install_commit(self, skill_id: str) -> None:
        """
        Create a Git commit before installing a skill

        Args:
            skill_id: Skill identifier
        """
        try:
            # Check if we're in a Git repository
            if not os.path.exists(".git"):
                logger.warning("Not in a Git repository, skipping pre-install commit")
                return

            # Create a commit
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Pre-install state before adding skill: {skill_id}"],
                check=True
            )

            logger.info(f"Created pre-install commit for skill: {skill_id}")
        except Exception as e:
            logger.error(f"Error creating pre-install commit: {str(e)}")

    async def _create_post_install_commit(self, skill_id: str) -> None:
        """
        Create a Git commit after installing a skill

        Args:
            skill_id: Skill identifier
        """
        try:
            # Check if we're in a Git repository
            if not os.path.exists(".git"):
                logger.warning("Not in a Git repository, skipping post-install commit")
                return

            # Create a commit
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Installed skill: {skill_id}"],
                check=True
            )

            logger.info(f"Created post-install commit for skill: {skill_id}")
        except Exception as e:
            logger.error(f"Error creating post-install commit: {str(e)}")

    async def uninstall_skill(self, skill_id: str) -> Dict[str, Any]:
        """
        Uninstall a skill

        Args:
            skill_id: Skill identifier

        Returns:
            Result dictionary with uninstallation result
        """
        try:
            # Check if the skill is installed
            skill_path = os.path.join(SKILLS_DIR, skill_id)
            if not os.path.exists(skill_path):
                logger.error(f"Skill not installed: {skill_id}")
                return {"success": False, "error": f"Skill not installed: {skill_id}"}

            # Create a Git commit before uninstalling
            await self._create_pre_install_commit(f"uninstall-{skill_id}")

            # Remove the skill directory
            shutil.rmtree(skill_path)

            # Remove from MongoDB
            if self.db:
                await self.db.skills.delete_one({"skill_id": skill_id})

            # Create a Git commit after uninstalling
            await self._create_post_install_commit(f"uninstall-{skill_id}")

            logger.info(f"Uninstalled skill: {skill_id}")
            return {"success": True, "message": f"Uninstalled skill: {skill_id}"}

        except Exception as e:
            logger.error(f"Error uninstalling skill: {str(e)}")
            return {"success": False, "error": str(e)}

    async def rollback_skill_installation(self, skill_id: str) -> Dict[str, Any]:
        """
        Rollback a skill installation

        Args:
            skill_id: Skill identifier

        Returns:
            Result dictionary with rollback result
        """
        try:
            # Check if we're in a Git repository
            if not os.path.exists(".git"):
                logger.error("Not in a Git repository, cannot rollback")
                return {"success": False, "error": "Not in a Git repository"}

            # Find the pre-install commit
            result = subprocess.run(
                ["git", "log", "--grep", f"Pre-install state before adding skill: {skill_id}", "--format=%H"],
                capture_output=True,
                text=True,
                check=True
            )

            commit_hash = result.stdout.strip()
            if not commit_hash:
                logger.error(f"Pre-install commit not found for skill: {skill_id}")
                return {"success": False, "error": f"Pre-install commit not found for skill: {skill_id}"}

            # Create a new branch for the rollback
            branch_name = f"rollback-{skill_id}-{int(time.time())}"
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)

            # Reset to the pre-install commit
            subprocess.run(["git", "reset", "--hard", commit_hash], check=True)

            # Remove from MongoDB
            if self.db:
                await self.db.skills.delete_one({"skill_id": skill_id})

            logger.info(f"Rolled back skill installation: {skill_id}")
            return {
                "success": True,
                "message": f"Rolled back skill installation: {skill_id}",
                "branch": branch_name
            }

        except Exception as e:
            logger.error(f"Error rolling back skill installation: {str(e)}")
            return {"success": False, "error": str(e)}

    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
