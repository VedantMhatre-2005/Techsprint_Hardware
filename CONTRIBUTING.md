# Contributing to SafeLabs

Thank you for your interest in contributing to SafeLabs! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Follow the setup instructions in README.md

## Development Workflow

### Branch Naming
- Features: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`

### Commit Messages
Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example: `feat: add temperature threshold alerts`

## Code Standards

### ESP32 Firmware (C++)
- Use meaningful variable names
- Comment complex logic
- Follow Arduino/PlatformIO conventions
- Test with Wokwi simulation before committing

### Node.js Backend
- Use ES6+ features
- Follow Express.js best practices
- Handle errors properly
- Add JSDoc comments for functions

### Python Dashboard
- Follow PEP 8 style guide
- Use type hints where applicable
- Document functions with docstrings
- Test locally with `streamlit run`

## Testing

- Test firmware with Wokwi simulation
- Verify dashboard functionality
- Check API endpoints with tools like Postman
- Ensure no credentials are exposed

## Pull Request Process

1. Update documentation if needed
2. Ensure all tests pass
3. Update CHANGELOG.md
4. Submit PR with clear description
5. Link related issues

## Security

- Never commit credentials
- Use `.env.example` and `config.h.example` as templates
- Report security vulnerabilities privately

## Questions?

Open an issue for discussion or clarification.

Thank you for contributing! 🚀
