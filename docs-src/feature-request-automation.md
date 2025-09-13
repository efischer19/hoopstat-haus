# Feature Request Automation Documentation

This document provides guidance on using the AI-driven feature request creation system to automatically extract and create GitHub issues from planning documents.

## Overview

The system consists of three main components:

1. **Analysis Document** (`meta/plans/ai-driven-feature-request-creation.md`) - Comprehensive analysis of the approach and implementation strategy
2. **Feature Database** (`meta/plans/extracted-feature-requests.json`) - Structured JSON containing all extracted feature requests
3. **Creation Script** (`scripts/create-feature-issues.sh`) - Bash script using GitHub CLI to create issues

## Quick Start

### Prerequisites

Before running the feature request creation script, ensure you have:

- **GitHub CLI (gh)** installed and authenticated
- **jq** installed for JSON processing
- Valid access to the GitHub repository
- Proper permissions to create issues

### Authentication Setup

```bash
# Authenticate with GitHub CLI
gh auth login

# Verify authentication
gh auth status
```

### Running the Script

#### Preview Issues (Recommended First Step)

```bash
# Preview all feature requests
./scripts/create-feature-issues.sh --dry-run --verbose

# Preview specific category
./scripts/create-feature-issues.sh --dry-run --category frontend

# Preview high-priority items only
./scripts/create-feature-issues.sh --dry-run --priority high
```

#### Create Issues

```bash
# Create all feature requests
./scripts/create-feature-issues.sh

# Create only frontend issues
./scripts/create-feature-issues.sh --category frontend

# Create only high-priority ETL pipeline issues
./scripts/create-feature-issues.sh --category etl-pipeline --priority high
```

## Available Categories

The extracted feature requests are organized into the following categories:

- `frontend` - UI/UX and client-side features
- `etl-pipeline` - Data processing and transformation features
- `aws-integration` - AWS infrastructure and integration features

## Available Priorities

Features are classified by priority:

- `high` - Critical path features requiring immediate attention
- `medium` - Important features for planned development
- `low` - Future enhancements and optimizations

## Script Options

| Option | Description | Example |
|--------|-------------|---------|
| `--dry-run` | Preview issues without creating them | `--dry-run` |
| `--category CATEGORY` | Filter by feature category | `--category frontend` |
| `--priority PRIORITY` | Filter by priority level | `--priority high` |
| `--verbose` | Enable detailed output | `--verbose` |
| `--help` | Show usage information | `--help` |

## Issue Format

Created issues follow a standardized format:

```markdown
## Description
[Feature description from planning document]

## Acceptance Criteria
- [ ] Specific requirement 1
- [ ] Specific requirement 2

## Technical Requirements
- Implementation detail 1
- Implementation detail 2

## Definition of Done
- Success criteria 1
- Success criteria 2

## Source Information
- **Epic:** [Epic name]
- **Category:** [frontend/etl-pipeline/etc.]
- **Priority:** [high/medium/low]
- **Complexity:** [high/medium/low]
- **Estimated Effort:** [time estimate]
- **Source Document:** [original planning document]
- **Source Section:** [specific section reference]

## Metadata
- **Feature ID:** [unique identifier]
- **Generated from planning documents on:** [timestamp]
```

## Labels Applied

Issues are automatically labeled based on their characteristics:

- `feature` - All feature requests
- `high-priority` - High-priority features
- Category-specific labels (`frontend`, `etl`, `aws-integration`, etc.)
- Feature-type labels (`setup`, `authentication`, `monitoring`, etc.)

## Error Handling

The script includes comprehensive error handling:

- **Duplicate Detection**: Checks for existing issues with the same title
- **Rate Limiting**: Respects GitHub API limits with delays between requests
- **Validation**: Validates JSON format and GitHub authentication
- **Logging**: Creates detailed logs in `logs/issue-creation-[timestamp].log`

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   gh auth login
   gh auth status
   ```

2. **Permission Errors**
   - Ensure you have write access to the repository
   - Check that your GitHub token has appropriate scopes

3. **JSON Parsing Errors**
   ```bash
   jq empty meta/plans/extracted-feature-requests.json
   ```

4. **Missing Dependencies**
   ```bash
   # Install GitHub CLI
   # See: https://cli.github.com/

   # Install jq
   # Ubuntu/Debian: apt-get install jq
   # macOS: brew install jq
   ```

### Log Analysis

Check the log file for detailed error information:

```bash
tail -f logs/issue-creation-[timestamp].log
```

## Customization

### Adding New Features

To add new features to the system:

1. Extract feature requests from new planning documents
2. Add them to `extracted-feature-requests.json` following the established schema
3. Update the `total_features` count in metadata
4. Run the script to create the new issues

### Modifying Issue Format

The issue format is controlled by the `format_issue_body()` function in the script. Modify this function to change how issues are formatted.

### Custom Labels

Labels are defined in the JSON file under `github_labels` for each feature. Modify these arrays to change the labels applied to issues.

## Best Practices

1. **Always use --dry-run first** to preview what will be created
2. **Start with high-priority items** to focus on critical features
3. **Process one category at a time** for better organization
4. **Review created issues** for quality and completeness
5. **Keep logs** for audit trails and troubleshooting

## Maintenance

### Updating Feature Requests

When planning documents are updated:

1. Re-run the extraction process (future automation)
2. Update the JSON file with new or modified features
3. Use the script to create only new issues (duplicate detection prevents re-creation)

### Monitoring Usage

Track the success of created issues:

- Monitor issue completion rates
- Gather feedback on issue quality
- Adjust extraction patterns based on developer feedback

## Integration with Development Workflow

The generated issues are designed to integrate seamlessly with existing development workflows:

- Issues follow repository conventions
- Labels align with project categorization
- Acceptance criteria provide clear implementation guidance
- Source traceability maintains connection to planning documents

## Future Enhancements

Potential improvements to the system:

- Automated extraction from updated planning documents
- Integration with GitHub Projects for automatic project board management
- Batch operations for issue updates when plans change
- Integration with issue templates and automation
- Metrics and analytics on feature completion

---

For questions or issues with the feature request automation system, refer to the comprehensive analysis in `meta/plans/ai-driven-feature-request-creation.md` or create an issue in the repository.