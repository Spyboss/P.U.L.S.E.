# General Pulse - Development Roadmap

## Current Development Focus
**Last Updated:** April 14, 2025

## Date & Time Capabilities Enhancement

### Implemented
- [x] Basic date/time information (current date, time, timezone)

### In Progress
- [ ] Timezone conversion functionality
- [ ] Date calculation (days between dates, add/subtract time)
- [ ] Date formatting options (different format standards)

### Planned
- [ ] Calendar integration (view upcoming events)
- [ ] Reminders and scheduling
- [ ] Countdowns and timers
- [ ] Recurring date calculations (next Monday, third Thursday of month, etc.)
- [ ] Holiday detection and information
- [ ] Meeting time suggestions across timezones

## AI Integration Status

### Implemented
- [x] Claude API integration for content generation
- [x] DeepSeek API integration for code generation 
- [x] Gemini API integration as agent brain
- [x] Fallback mechanism between AI models
- [x] OpenRouter integration for unified AI model access
- [x] AI-powered commit message generation for GitHub
- [x] Credit limit handling for free tier OpenRouter models
- [x] Async error handling for model interfaces
- [x] Proper detection of OpenRouter error responses

### In Progress
- [ ] Enhanced context handling for AI requests
- [ ] Improved intent classification with Gemini

### Planned
- [ ] Better response formatting for different AI models
- [ ] Rate limiting and cost management for API usage
- [ ] Fine-tuning prompts for each model type
- [ ] AI model performance benchmarking
- [ ] AI-powered code review for pull requests
- [ ] Notion-to-code generation pipeline

## GitHub Integration Status

### Implemented
- [x] Repository information retrieval
- [x] Issue listing and creation
- [x] Issue detail view
- [x] Local caching for offline access
- [x] AI-driven commit message generation
- [x] Repository URL parsing and validation

### In Progress
- [x] GitHub Skills module for high-level functionality

### Planned
- [ ] Pull request management
- [ ] Commit history browsing
- [ ] Code search in repositories
- [ ] Workflow status checking
- [ ] Automated PR review system

## Notion Integration Status

### Implemented
- [x] Basic Notion page access and content retrieval
- [x] URL parsing to extract page and database IDs

### In Progress
- [ ] Content creation and updating
- [ ] Database query capabilities

### Planned
- [ ] Bi-directional sync with tasks
- [ ] Template system for Notion pages
- [ ] AI-enhanced content organization

## Technical Debt & Improvements

### In Progress
- [ ] Code documentation improvements
- [ ] Error handling enhancements
- [ ] Unit test coverage
- [ ] Logging improvements

## Future Directions
- Web interface for the agent
- Mobile notification support
- Integration with more productivity tools
- Advanced natural language task delegation 
- Slack bot for code generation
- CLI-driven bug detection and fixing 