# Scenarios Guide

Everything you need to know about AgentProbe scenarios - what they are, how to use them, and how to create your own.

## What Are Scenarios?

Scenarios are **simple text prompts** that describe tasks for AI agents to perform using CLI tools. They're stored as plain `.txt` files with no special formatting - just the instructions.

**Example scenario** (`git/status.txt`):
```
Check the current status of the git repository and report:
1. The current branch name
2. Whether there are any uncommitted changes  
3. Whether the branch is up to date with the remote

Use the git status command and provide a clear summary of the repository state.
```

## Scenario Types

### Simple Scenarios
Single-step tasks that test basic tool usage:

- **git/status** - Check repository status
- **docker/run-nginx** - Run nginx container
- **vercel/deploy** - Deploy application

### Complex Scenarios  
Multi-step workflows that test advanced usage:

- **netlify/full-lifecycle** - Create site, deploy, cleanup
- **vercel/domain-setup** - Configure custom domain
- **wrangler/kv-setup** - Set up key-value storage

## Available Scenarios

### Git (git/)
| Scenario | Description | Difficulty |
|----------|-------------|------------|
| `status` | Check repository status | ⭐ Easy |
| `show-log` | Display commit history | ⭐ Easy |
| `commit-changes` | Stage and commit files | ⭐⭐ Medium |

### Docker (docker/)  
| Scenario | Description | Difficulty |
|----------|-------------|------------|
| `run-nginx` | Run nginx web server | ⭐ Easy |

### GitHub CLI (gh/)
| Scenario | Description | Difficulty |
|----------|-------------|------------|
| `create-pr` | Create pull request | ⭐⭐ Medium |

### Vercel (vercel/)
| Scenario | Description | Difficulty |
|----------|-------------|------------|
| `deploy` | Deploy to production | ⭐⭐ Medium |
| `init-project` | Initialize new project | ⭐ Easy |
| `build-local` | Build project locally | ⭐ Easy |
| `list-deployments` | List recent deployments | ⭐ Easy |
| `preview-deploy` | Deploy to preview | ⭐⭐ Medium |
| `rollback` | Rollback deployment | ⭐⭐⭐ Hard |
| `domain-setup` | Configure custom domain | ⭐⭐⭐ Hard |
| `env-setup` | Manage environment variables | ⭐⭐ Medium |

### Netlify (netlify/)
| Scenario | Description | Difficulty |
|----------|-------------|------------|
| `full-lifecycle` | Complete site lifecycle | ⭐⭐⭐ Hard |
| `function-lifecycle` | Deploy serverless functions | ⭐⭐⭐ Hard |
| `draft-and-promote` | Draft deploy workflow | ⭐⭐ Medium |
| `advanced-env-management` | Environment variable management | ⭐⭐ Medium |
| `monorepo-deploy` | Deploy from monorepo | ⭐⭐⭐ Hard |

### Cloudflare Workers (wrangler/)
| Scenario | Description | Difficulty |
|----------|-------------|------------|
| `init` | Initialize new Worker | ⭐ Easy |
| `dev` | Start local development | ⭐ Easy |
| `deploy` | Deploy to production | ⭐⭐ Medium |
| `kv-setup` | Set up KV storage | ⭐⭐ Medium |
| `pages-deploy` | Deploy Pages site | ⭐⭐ Medium |
| `secret-manage` | Manage secrets | ⭐⭐ Medium |
| `tail-logs` | View live logs | ⭐ Easy |

## Running Scenarios

### Single Scenario
```bash
# Run specific scenario
agentprobe test git --scenario status

# Run with verbose output to see AI conversation
agentprobe test git --scenario status --verbose

# Run multiple times to test consistency
agentprobe test vercel --scenario deploy --runs 3
```

### Multiple Scenarios
```bash
# Run all scenarios for a tool
agentprobe benchmark git

# Run all scenarios for all tools (long!)
agentprobe benchmark --all
```

## Scenario Structure

### File Organization
```
src/agentprobe/scenarios/
├── git/
│   ├── status.txt
│   ├── show-log.txt
│   └── commit-changes.txt
├── vercel/
│   ├── deploy.txt
│   ├── init-project.txt
│   └── ...
└── docker/
    └── run-nginx.txt
```

### Naming Convention
- **Directory**: Tool name (e.g., `git`, `vercel`, `docker`)
- **File**: Scenario name with `.txt` extension (e.g., `status.txt`, `deploy.txt`)
- **Use hyphens**: For multi-word scenarios (e.g., `commit-changes.txt`)

## Creating Custom Scenarios

### 1. Choose Your Tool
First, decide which CLI tool you want to test:

```bash
# Check if tool directory exists
ls src/agentprobe/scenarios/
```

### 2. Create Scenario File
Create a new `.txt` file in the appropriate tool directory:

```bash
# Example: Create new git scenario
touch src/agentprobe/scenarios/git/my-scenario.txt
```

### 3. Write the Prompt
Write clear, specific instructions in plain English:

**Good scenario**:
```
Create a new branch called 'feature/user-auth' from the current branch.
Switch to this new branch and verify you're on it.
Make sure the branch is ready for development work.
```

**Bad scenario**:
```
Do something with git branches.
```

### 4. Test Your Scenario
```bash
# Test your new scenario
agentprobe test git --scenario my-scenario

# Use verbose to see how AI interprets it
agentprobe test git --scenario my-scenario --verbose
```

## Writing Good Scenarios

### ✅ Best Practices

**Be Specific**: Include exact requirements
```
✅ "Deploy to production and return the deployment URL"
❌ "Deploy the app"
```

**Include Context**: Explain the situation
```
✅ "You have a Next.js app in the current directory. Deploy it to Vercel..."
❌ "Deploy this to Vercel"
```

**Define Success**: Be clear about expected outcomes
```
✅ "Verify the deployment was successful by checking the site's status"
❌ "Make sure it works"
```

**Use Action Words**: Start with verbs
```
✅ "Create", "Deploy", "Configure", "Verify"
❌ "Try to...", "Maybe..."
```

**Number Steps**: For complex scenarios
```
✅ "1. Create a new site
     2. Configure the domain
     3. Deploy the application"
❌ "Create a site and configure it and deploy"
```

### ❌ Common Pitfalls

**Too Vague**: Unclear requirements
```
❌ "Set up the project"
```

**Too Specific**: Hardcoded values that might not exist
```
❌ "Deploy to https://my-specific-domain.com"
```

**Assuming State**: Assuming specific files/configuration exist
```
❌ "Deploy the React app in the 'client' directory"
Better: "Deploy the current directory to production"
```

**Multiple Tools**: Scenarios should focus on one tool
```
❌ "Use git to commit changes, then deploy with vercel"
Better: Create separate git and vercel scenarios
```

## Scenario Examples

### Simple Task (Easy)
```
Check the current working directory and list all files and subdirectories.
Show both hidden and visible files.
```

### Workflow Task (Medium)  
```
Initialize a new Git repository in the current directory.
Create an initial commit with all existing files.
Add a remote origin pointing to a GitHub repository (you can use a placeholder URL).
```

### Complex Task (Hard)
```
You need to set up a complete Cloudflare Workers development environment:

1. Initialize a new Worker project called 'api-handler'
2. Configure it to handle HTTP requests
3. Add a KV namespace called 'user-data'  
4. Bind the KV namespace to your worker
5. Deploy to production
6. Test the deployment by making a request
7. View the logs to confirm it's working

Make sure each step completes successfully before proceeding to the next.
```

## Modifying Existing Scenarios

### 1. Find the Scenario
```bash
# Find scenario file
find src/agentprobe/scenarios -name "status.txt"
```

### 2. Edit the File
```bash
# Edit with your preferred editor
code src/agentprobe/scenarios/git/status.txt
```

### 3. Test Changes
```bash
# Test modified scenario
agentprobe test git --scenario status --verbose
```

### 4. Compare Results
Run the scenario multiple times to ensure consistent behavior.

## Contributing Scenarios

### New Tool Support
To add a completely new tool:

1. **Create tool directory**: `src/agentprobe/scenarios/newtool/`
2. **Add basic scenario**: Start with simple functionality
3. **Test thoroughly**: Ensure it works across different environments
4. **Document**: Add to this guide

### New Scenarios for Existing Tools
1. **Check existing scenarios**: Avoid duplication
2. **Follow naming conventions**: Use descriptive names
3. **Test on multiple systems**: Different OS, tool versions
4. **Submit for review**: Get feedback on clarity and usefulness

## Troubleshooting Scenarios

### Scenario Not Found
```bash
Error: Scenario 'my-scenario' not found for tool 'git'
```
**Fix**: Check file exists at `src/agentprobe/scenarios/git/my-scenario.txt`

### AI Misunderstands Scenario
**Symptoms**: Unexpected behavior, wrong commands
**Fix**: Make scenario more specific, add context, test with `--verbose`

### Inconsistent Results
**Symptoms**: Sometimes works, sometimes doesn't
**Fix**: Scenario might be too vague or depend on specific system state

### Tool Not Available
**Symptoms**: "Command not found" errors
**Fix**: Ensure the CLI tool is installed and in PATH

## Advanced Tips

### Environment-Specific Scenarios
Some scenarios work better in specific environments:

- **Development**: Use local development servers
- **CI/CD**: Avoid interactive prompts
- **Docker**: Consider containerized environments

### Parameterized Scenarios
While scenarios are static text, you can include placeholders:

```
Create a new branch called 'feature/[random-string]' to avoid conflicts.
```

The AI will typically generate appropriate values.

### Testing Consistency
Run scenarios multiple times to verify consistency:

```bash
# Test 5 times to check consistency
agentprobe test git --scenario status --runs 5
```

---

**Ready to create your own scenarios?** Start simple with basic tool functionality, then build up to complex workflows. Every scenario you create helps the community understand how AI agents interact with CLI tools! 🚀