# MediaForge GitHub Copilot Prompts

This directory contains meticulously crafted prompts for GitHub Copilot Agent to autonomously implement MediaForge features.

## 📝 Prompt Execution Order

### Phase 1: Foundation (Week 1-2)
1. `01_database_schema.md` - Complete database architecture
2. `02_media_scanner.md` - File system scanning engine
3. `03_metadata_extraction.md` - Metadata extraction framework
4. `04_cli_interface.md` - Command-line interface
5. `05_testing_framework.md` - Comprehensive test suite

### Phase 2: Core Features (Week 3-4)
6. `06_search_engine.md` - Full-text search implementation
7. `07_web_api.md` - FastAPI REST interface
8. `08_media_organization.md` - Organization and categorization

### Phase 3: Advanced Features (Week 5-8)
9. `09_compression_pipeline.md` - Intelligent compression
10. `10_torrent_integration.md` - Torrent client integration
11. `11_device_discovery.md` - USB/Network device scanning

## 🚀 How to Use These Prompts

1. **Open VS Code** with GitHub Copilot enabled
2. **Open the prompt file** you want to execute
3. **Copy the entire prompt** (everything after the metadata section)
4. **Open Copilot Chat** (Ctrl+Shift+I or Cmd+Shift+I)
5. **Paste the prompt** and let Copilot work
6. **Review the generated code** before committing
7. **Run tests** to validate implementation
8. **Move to next prompt** once tests pass

## ✅ Validation Checklist

After each prompt execution:
- [ ] Code follows Python best practices
- [ ] Type hints are present and correct
- [ ] Docstrings are comprehensive
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Code is formatted with Black
- [ ] No linting errors from Flake8
- [ ] Mypy type checking passes

## 📊 Progress Tracking

Mark prompts as complete in this README as you finish them.

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

## 📄 Prompt Template

Each prompt follows this structure:

```markdown
# [Feature Name]

## Context
[Background and purpose]

## Technical Requirements
[Detailed specifications]

## Implementation Details
[Step-by-step guidance]

## Code Structure
[Expected file organization]

## Testing Requirements
[Test specifications]

## Success Criteria
[Validation checklist]
```

## 🔧 Troubleshooting

If Copilot generates unexpected results:
1. Review the prompt for clarity
2. Check that previous prompts were completed successfully
3. Ensure all dependencies are installed
4. Verify Docker containers are running
5. Check logs for errors

## 💬 Support

For issues with prompt execution, review the generated code and tests. Copilot may require iterative refinement for complex features.