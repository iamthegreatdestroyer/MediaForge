# MediaForge GitHub Copilot Prompts

This directory contains meticulously crafted prompts for GitHub Copilot Agent to autonomously implement MediaForge features.

## 🚀 Prompt Execution Order

### Phase 0: Environment Setup (30 minutes)
0. `00_docker_setup.md` - Docker environment setup and verification

### Phase 1: Foundation (Week 1-2)
1. `01_database_schema.md` - Complete database architecture
2. `02_media_scanner.md` - File system scanning engine
3. `03_metadata_extraction.md` - Metadata extraction framework
4. `04_cli_interface.md` - Command-line interface
5. `05_testing_framework.md` - Comprehensive test suite

### Phase 2: Core Features (Week 3-4)
6. `06_search_engine.md` - Full-text search implementation (Coming Soon)
7. `07_web_api.md` - FastAPI REST interface (Coming Soon)
8. `08_media_organization.md` - Organization and categorization (Coming Soon)

### Phase 3: Advanced Features (Week 5-8)
9. `09_compression_pipeline.md` - Intelligent compression (Coming Soon)
10. `10_torrent_integration.md` - Torrent client integration (Coming Soon)
11. `11_device_discovery.md` - USB/Network device scanning (Coming Soon)

## 📋 How to Use These Prompts

### Method 1: Using GitHub Copilot Chat in VS Code (Recommended)

1. **Open VS Code** with your MediaForge repository
2. **Ensure GitHub Copilot is enabled** (check status bar)
3. **Open the prompt file** you want to execute
4. **Copy the entire prompt** (everything after the metadata section)
5. **Open Copilot Chat** (Ctrl+Shift+I or Cmd+Shift+I)
6. **Paste the prompt** into the chat
7. **Let Copilot generate the code** - it will create files, implement features
8. **Review the generated code** - check for completeness and correctness
9. **Run tests** to validate implementation
10. **Commit your changes** and move to the next prompt

### Method 2: Using GitHub Copilot Inline (For Smaller Sections)

1. **Create the file** that the prompt says to create
2. **Copy relevant sections** of the prompt as comments
3. **Let Copilot autocomplete** based on the comments
4. **Review and refine** the generated code

### Method 3: Terminal Commands (For Docker Setup)

**Prompt 00** includes bash commands that can be:
- Copy-pasted directly into your terminal
- Used with the helper script (dev.sh)
- Executed through VS Code terminal

## ✅ Validation Checklist

After each prompt execution:

- [ ] Code follows Python best practices
- [ ] Type hints are present and correct
- [ ] Docstrings are comprehensive (Google style)
- [ ] Unit tests pass
- [ ] Integration tests pass (when applicable)
- [ ] Code is formatted with Black: `./dev.sh format`
- [ ] No linting errors from Flake8: `./dev.sh lint`
- [ ] Mypy type checking passes: `./dev.sh types`
- [ ] Code coverage >90%

## 📊 Progress Tracking

Mark prompts as complete as you finish them:

### Phase 0: Environment Setup
- [ ] Docker Setup & Verification

### Phase 1: Foundation
- [ ] Database Schema
- [ ] Media Scanner
- [ ] Metadata Extraction
- [ ] CLI Interface
- [ ] Testing Framework

### Phase 2: Core Features
- [ ] Search Engine
- [ ] Web API
- [ ] Media Organization

### Phase 3: Advanced Features
- [ ] Compression Pipeline
- [ ] Torrent Integration
- [ ] Device Discovery

## 🎯 Prompt Template Structure

Each prompt follows this structure:

```markdown
# [Feature Name]

## Metadata
- Phase, Priority, Time estimate, Dependencies, Files to create

---

# GITHUB COPILOT PROMPT: [FEATURE NAME]

## Context
[Background and purpose]

## Technical Requirements
[Detailed specifications]

## Implementation Instructions
[Step-by-step guidance with code examples]

## Testing Requirements
[Test specifications]

## Success Criteria
[Validation checklist]

## Code Quality Standards
[Quality expectations]

## Example Usage
[How the feature should work]
```

## 🛠️ Development Workflow

### For Each Prompt:

1. **Read the Entire Prompt**
   - Understand what you're building
   - Note dependencies
   - Review success criteria

2. **Execute with Copilot**
   - Copy full prompt to Copilot Chat
   - Wait for code generation
   - Review all generated files

3. **Validate Implementation**
   ```bash
   # Format code
   ./dev.sh format
   
   # Check linting
   ./dev.sh lint
   
   # Type check
   ./dev.sh types
   
   # Run tests
   ./dev.sh test -v
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Implement [feature] (Prompt XX)"
   git push origin main
   ```

5. **Update Progress**
   - Mark checkbox in this README
   - Note any customizations or issues
   - Document lessons learned

## 💡 Tips for Success

### Working with Copilot

**✅ Best Practices:**
- Copy the **complete prompt** (they're designed as comprehensive units)
- Execute prompts **in order** (they build on each other)
- **Review generated code** before committing
- **Run tests immediately** after generation
- **Format code** before committing
- **Ask Copilot to fix** specific issues if tests fail

**🎯 If Copilot Needs Guidance:**
```
"The generated [component] has [specific issue]. 
Please fix it by [specific solution]."
```

**Example:**
```
"The MediaItem model is missing cascade delete on relationships. 
Please update all relationships to include cascade='all, delete-orphan'."
```

### Code Quality

Before committing:
```bash
# All-in-one validation
./dev.sh format && ./dev.sh lint && ./dev.sh types && ./dev.sh test
```

### Docker Commands

```bash
# Start development environment
./dev.sh start

# Run tests
./dev.sh test

# Open shell in container
./dev.sh shell

# View logs
./dev.sh logs

# Stop everything
./dev.sh stop
```

## 🔧 Troubleshooting

### Copilot Issues

**Copilot not responding:**
- Check Copilot status in VS Code status bar
- Reload VS Code window (Ctrl+R)
- Sign out and back into GitHub account
- Verify Copilot subscription is active

**Generated code has errors:**
- Review the prompt for clarity
- Try breaking complex sections into smaller prompts
- Manually fix obvious issues
- Ask Copilot to regenerate specific sections

**Tests failing:**
- Check that all dependencies are installed
- Verify Docker containers are running
- Review test output for specific failures
- Check for async/await issues
- Ensure fixtures are set up correctly

### Docker Issues

**Containers won't start:**
```bash
./dev.sh clean
./dev.sh build
./dev.sh start
```

**Permission errors:**
```bash
# Fix volume permissions
docker exec -u root mediaforge-app chown -R $(id -u):$(id -g) /app
```

**Import errors:**
```bash
# Reinstall dependencies
docker exec mediaforge-app pip install -r requirements.txt
```

## 📚 Additional Resources

### Documentation
- [EXECUTION_GUIDE.md](../EXECUTION_GUIDE.md) - Complete development guide
- [docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md) - Detailed setup
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - System architecture

### External References
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [GitHub Copilot Docs](https://docs.github.com/en/copilot)

## 🎓 Learning from AI-Generated Code

These prompts are designed to:
- Generate **production-quality code**
- Follow **Python best practices**
- Include **comprehensive documentation**
- Implement **proper error handling**
- Use **modern async/await patterns**

**Review the generated code to learn:**
- How to structure async Python applications
- SQLAlchemy 2.0 patterns
- Proper type hinting techniques
- Testing strategies
- Error handling patterns

## ⚠️ Important Notes

1. **Always review generated code** - Copilot is excellent but not perfect
2. **Run tests before committing** - Catch issues early
3. **Don't skip prompts** - They build on each other
4. **Keep Docker running** - Faster development iteration
5. **Commit frequently** - After each successful prompt
6. **Read the documentation** - It contains important context

## 🚀 Ready to Start?

1. **Start with Prompt 00** - Set up your Docker environment
2. **Verify everything works** - Run the verification script
3. **Move to Prompt 01** - Build the database layer
4. **Follow the sequence** - Complete all Phase 1 prompts
5. **Celebrate success!** 🎉 - You'll have a working media library!

---

**Need help?** Check the troubleshooting section or refer to the main documentation.

**Found an issue?** The prompts can be refined - note improvements for future iterations.

**Ready to build?** Start with Prompt 00 and let's forge your perfect media collection! 🔥