An automated deployment system that receives app briefs via API, generates code using OpenAI GPT-4, creates GitHub repositories, and deploys applications to GitHub Pages with support for iterative revisions.

## Tech Stack

## ✔️ Core Features
- RESTful endpoint accepts JSON requests with app specifications.
- Creates repositories, manages commits, and enables GitHub Pages.
- Handles multiple rounds of modifications to existing applications.
- Automatically includes MIT license and comprehensive README for each generated app.

## Workflow
> Request → Verify Secret → Generate Code (OpenAI) → Create/Update GitHub Repo → Enable Pages → Notify Evaluation URL → Response

