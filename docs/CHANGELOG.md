# General Pulse Changelog

## [Unreleased]

### Added
- Enhanced memory management system with proactive monitoring and critical threshold handling
- Added global helper functions for checking integration status
- Improved task routing with better fallback mechanisms
- Added dynamic token adjustment for expensive models to prevent credit limit errors

### Fixed
- Fixed circular dependency issues between execution_flow.py and model_interface.py
- Fixed integration configuration checking for GitHub and Notion
- Improved error handling in the agent's processing pipeline with helpful messages
- Addressed memory leaks with enhanced memory guard implementation

### Changed
- Reduced default token limits for Claude models to conserve OpenRouter credits
- Improved task handling with better error messages for misconfigured integrations
- Enhanced agent feedback when encountering API errors or service issues

## 2023-01-15

### Added
- Enhanced system status command to display memory usage, integration status, and model availability
- Added system metadata cache for faster startup and reduced API calls
- Added new helper functions for common operations

### Fixed
- Fixed issue with Notion API pagination
- Fixed memory leak in the cache manager
- Implemented proper model availability checking for status display

### Changed
- Improved error handling for API calls
- Enhanced logging for better debugging
- Updated documentation with new features and error codes

## 2023-01-01

### Added
- Initial release of General Pulse
- Task tracking system with memory
- Intent classification
- Basic utilities
- GitHub and Notion integration
- Configuration system with YAML
- Utility functions for common operations 