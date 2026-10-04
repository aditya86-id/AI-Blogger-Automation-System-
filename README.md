# 🤖 AI Blogger Automation System

An intelligent AI-powered blog automation system that generates, refines, and publishes high-quality blog posts directly to Blogger. Built with LangGraph, FastAPI, and React, this system features an AI agent that can manage your entire blogging workflow with human-in-the-loop approval.

## ✨ Key Features

### 📝 Content Generation
- AI-powered blog post generation using Groq LLMs
- Intelligent topic expansion and content structuring
- Markdown-to-HTML conversion with proper formatting
- Automatic image generation using Pollinations AI

### 🔄 Iterative Refinement
- Human feedback loop for content improvement
- Real-time draft preview
- Multiple refinement iterations
- Context-aware content updates

### 🚀 Automated Publishing
- Direct integration with Blogger API via MCP Server
- One-click publish to Blogger platform
- Automatic title optimization
- Featured image embedding

### 🤖 AI Agent Capabilities
- Natural language blog management commands
- List, create, update, and delete posts via conversation
- Smart post identification (newest, by ID, by title)
- Human approval for critical actions (delete, update, publish)
- Context-aware decision making

## 🏛️ Architecture

### Tech Stack

**Backend:**
- **Framework:** FastAPI (Python)
- **AI/LLM:** LangGraph + ChatGroq (GPT-oss-20b)
- **MCP Integration:** Blogger MCP Server (Node.js)
- **State Management:** LangGraph StateGraph
- **Image Generation:** Pollinations AI

**Frontend:**
- **Framework:** React 19 + Vite
- **Styling:** Tailwind CSS v4
- **Icons:** Lucide React
- **Build Tool:** Vite 7

### System Flow

```
User Input (Topic)
    ↓
AI Content Generator (LLM)
    ↓
Draft Preview (Markdown)
    ↓
User Review & Feedback
    ↓
Refinement Loop (Optional)
    ↓
Approval & Publish
    ↓
AI Agent (Human-in-loop)
    ↓
Blogger API (MCP Server)
    ↓
Published Blog Post
```

## 📸 Application Screenshots

### Blog Draft Generation
![Blog Draft Interface]<img width="978" height="738" alt="Screenshot 2025-12-07 214913" src="https://github.com/user-attachments/assets/5aae9e9e-163a-4f76-a575-31d378cb45e8" />

*Generate AI-powered blog drafts on any topic with automatic structuring and formatting*

### Review & Refinement Workflow
![Review Interface]
*Review drafts, provide feedback, and refine content iteratively before publishing*

### Published Blog Management
![Published Blogs]<img width="716" height="718" alt="Screenshot 2025-12-07 221747" src="https://github.com/user-attachments/assets/14312ecd-f92f-4859-8a70-67c1a97d173f" />

*View and manage all published posts with AI agent commands*

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- Google Blogger Account
- Google Cloud Project with Blogger API enabled
- Groq API Key

### 1. Clone Repository

```bash
git clone https://github.com/alk231/AI-Blogger-Automation-System-.git
cd AI-Blogger-Automation-System-/blogAgent
```

### 2. Backend Setup

#### Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

Create a `requirements.txt` with:
```txt
fastapi
uvicorn[standard]
python-dotenv
langchain-groq
langgraph
langchain-mcp-adapters
markdown
```

#### Configure Environment Variables

Create `.env` file in `Backend/` directory:

```env
# Blogger Configuration
BLOG_ID=your_blogger_blog_id

# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Groq API Key
GROQ_API_KEY=your_groq_api_key
```

#### Setup Blogger MCP Server

1. Install the Blogger MCP Server:
```bash
npm install -g @your-org/blogger-mcp-server
```

2. Update the MCP server path in `app.py` (line 99):
```python
"command": "node",
"args": ["path/to/blogger-mcp-server/dist/index.js"],
```

#### Run Backend

```bash
python app.py
# or
uvicorn app:app --reload
```

Backend runs on `http://localhost:8000`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd ../Frontend
npm install
```

#### Configure API Endpoint

Create `.env` file in `Frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

#### Run Frontend

```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

## 📚 API Documentation

### Content Generation Endpoints

#### Generate Blog Draft
```http
POST /generate
Content-Type: application/json

{
  "topic": "Your blog topic",
  "include_image": false
}
```

**Response:**
```json
{
  "draft": "Markdown content...",
  "evaluation": "Draft generated successfully."
}
```

#### Refine Blog Draft
```http
POST /refine
Content-Type: application/json

{
  "original_topic": "Original topic",
  "feedback": "Your improvement suggestions",
  "previous_draft": "Previous markdown content",
  "include_image": false
}
```

#### Publish Blog Post
```http
POST /publish
Content-Type: application/json

{
  "title": "Blog title",
  "content": "Markdown content",
  "include_image": true
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "title": "Optimized Title",
    "postId": "AUTO_GENERATED",
    "url": "https://yourblog.blogspot.com/..."
  }
}
```

### AI Agent Endpoint

#### Natural Language Blog Management
```http
POST /agent
Content-Type: application/json

{
  "message": "Delete my 3 most recent posts"
}
```

**Supported Commands:**
- "List all my blog posts"
- "Delete the most recent post"
- "Update the latest post with more examples"
- "Show posts from last week"

## 🧠 AI Agent Intelligence

### Decision-Making Logic

The AI agent follows intelligent rules:

1. **Content vs Management**: Distinguishes between content writing requests and blog management commands
2. **Safety First**: Always lists posts before deletion to avoid mistakes
3. **Smart Identification**: Finds posts by newest, ID, or title match
4. **Human Approval**: Requires confirmation for critical actions
5. **Context Preservation**: Maintains formatting when updating posts

### Agent Workflow

```python
User Command → Agent Analysis → Action Detection
                                      ↓
                              Critical Action?
                                      ↓
                        Yes → Human Approval → Execute
                         No → Direct Execute
```

## 📑 Project Structure

```
AI-Blogger-Automation-System-/
├── blogAgent/
│   ├── Backend/
│   │   ├── app.py              # FastAPI main application
│   │   └── .env                # Environment variables
│   │
│   └── Frontend/
│       ├── src/
│       │   ├── App.jsx         # Main React component
│       │   └── components/     # UI components
│       ├── public/
│       ├── package.json
│       └── vite.config.js
│
├── docs/
│   └── images/             # Screenshot documentation
└── README.md
```

## 🔒 Google API Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Blogger API v3

### Step 2: Configure OAuth Consent

1. Navigate to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type
3. Add required scopes:
   - `https://www.googleapis.com/auth/blogger`
   - `https://www.googleapis.com/auth/blogger.readonly`

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Create **OAuth 2.0 Client ID**
3. Application type: **Web application**
4. Authorized redirect URIs:
   - `http://localhost:3000/oauth/callback`
5. Copy Client ID and Client Secret to `.env`

### Step 4: Get Blog ID

1. Visit your Blogger dashboard
2. Go to **Settings** > **Basic**
3. Find **Blog ID** in the URL or settings
4. Add to `.env` file

## 🎓 Usage Guide

### Generating a Blog Post

1. Enter your topic in the input field
2. Click **Generate Draft**
3. Review the AI-generated content
4. Optionally add feedback and click **Refine**
5. When satisfied, click **Approve & Publish**

### Using AI Agent Commands

In the agent interface, try:

```
"List my recent blog posts"
"Delete the last 2 posts"
"Update the newest post with better examples"
"Show me posts about AI"
```

## 🔧 Configuration Options

### LLM Model Selection

Change the model in `app.py`:

```python
llm = ChatGroq(
    model="openai/gpt-oss-20b",  # or "mixtral-8x7b-32768"
    temperature=0.7
)
```

### Image Generation

Customize image parameters:

```python
return f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux"
```

### Approval Requirements

Modify critical actions list:

```python
CRITICAL_ACTIONS = ["delete_post", "create_post", "update_post"]
```

## 🚀 Advanced Features

### Custom Markdown Extensions

The system uses Python Markdown with extensions:
- **extra**: Adds tables, footnotes, abbreviations
- **sane_lists**: Better list handling

### Image Prompt Engineering

Generate better images by modifying the prompt:

```python
img_prompt = f"Professional blog header image about {title}, high quality, modern design"
```

### Multi-Blog Support

Manage multiple blogs by switching `BLOG_ID` in environment variables or extending the agent logic.

## 📊 Performance & Limits

- **Generation Time:** 5-15 seconds per draft
- **Refinement:** 3-10 seconds per iteration
- **Publishing:** 2-5 seconds to Blogger
- **Rate Limits:** Depends on Groq API tier and Blogger API quotas

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Multi-language support
- SEO optimization suggestions
- Plagiarism detection
- Scheduled publishing
- Analytics integration
- WordPress/Medium support

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 🐛 Troubleshooting

### Common Issues

**Issue:** "MCP Server not found"
- Solution: Update MCP server path in `app.py` line 99

**Issue:** "Blogger API quota exceeded"
- Solution: Check Google Cloud Console quotas and enable billing

**Issue:** "Authentication failed"
- Solution: Regenerate OAuth credentials and update `.env`

**Issue:** "Image not loading"
- Solution: Check Pollinations API status or use alternative image service

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Alok Kumar**

- GitHub: [@alk231](https://github.com/alk231)
- Project Link: [AI-Blogger-Automation-System](https://github.com/alk231/AI-Blogger-Automation-System-)

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [Groq](https://groq.com/) for fast LLM inference
- [Pollinations AI](https://pollinations.ai/) for image generation
- [Blogger API](https://developers.google.com/blogger) for content publishing
- [FastAPI](https://fastapi.tiangolo.com/) for backend framework

## 💡 Future Enhancements

- [ ] Multi-platform publishing (WordPress, Medium, Dev.to)
- [ ] Scheduled post publishing
- [ ] SEO score analysis
- [ ] Content plagiarism checker
- [ ] Analytics dashboard
- [ ] Voice-to-blog conversion
- [ ] Multi-language content generation
- [ ] A/B testing for titles
- [ ] Social media auto-posting
- [ ] Draft versioning system

---

⭐ **Star this repository if you find it useful!**

🐛 **Found a bug? Open an issue!**

💡 **Have suggestions? Start a discussion!**
