An automated deployment system that receives app briefs via API, generates code using OpenAI GPT-4, creates GitHub repositories, and deploys applications to GitHub Pages with support for iterative revisions.

## ⚙️Tech Stack
- Backend: Python 3.13, Flask 3.0
- LLM: OpenAI GPT-4
- Version Control: PyGithub 2.8
- Deployment: Render
- Environment: python-dotenv

## ✔️ Core Features
- RESTful endpoint accepts JSON requests with app specifications.
- Creates repositories, manages commits, and enables GitHub Pages.
- Handles multiple rounds of modifications to existing applications.
- Automatically includes MIT license and comprehensive README for each generated app.
- Notifies evaluation URL with retry logic.
- Returns appropriate HTTP status codes.

## Workflow
> Request → Verify Secret → Generate Code (OpenAI) → Create/Update GitHub Repo → Enable Pages → Notify Evaluation URL → Response

## The goal of the mini project

This project demonstrates the practical application of LLM-powered automation in software development workflows. The key learning objectives are:

- **API Development**: Building robust REST APIs that handle complex workflows.
- **LLM Integration**: Leveraging large language models for code generation and automation.
- **CI/CD Automation**: Implementing automated deployment pipelines using GitHub APIs.
- **Error Handling**: Managing asynchronous operations, retries, and failure recovery.
- **End-to-End Workflow**: Orchestrating multiple services (LLM, GitHub, deployment platforms) into a cohesive system.

## Security Measures

- Secrets managed via environment variables.
- GitHub token has minimal required permissions.
- `.env` file excluded from github repo.
- Secret verification on all requests.
