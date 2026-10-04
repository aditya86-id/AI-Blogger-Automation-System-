from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import urllib.parse
from dotenv import load_dotenv
import markdown  # NEW: proper markdown → HTML conversion

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# -------------------------------------------------------
# Request Models
# -------------------------------------------------------
class GenerateRequest(BaseModel):
    topic: str
    include_image: bool = False


class RefineRequest(BaseModel):
    original_topic: str
    feedback: str
    previous_draft: str
    include_image: bool = False


class PublishRequest(BaseModel):
    title: str  # this is your "topic" from frontend
    content: str  # markdown draft
    include_image: bool = False


class AgentRequest(BaseModel):
    message: str


# -------------------------------------------------------
# Agent State
# -------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    pending_action: dict
    human_feedback: str


BLOG_ID =os.getenv("BLOG_ID")
CRITICAL_ACTIONS = ["delete_post", "create_post", "update_post"]

workflow = None


# -------------------------------------------------------
# FastAPI Lifecycle
# -------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_workflow()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------
# Image Generation
# -------------------------------------------------------
async def generate_image(prompt: str):
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux"


# -------------------------------------------------------
# Initialize Workflow
# -------------------------------------------------------
async def init_workflow():
    global workflow

    servers = {
        "blogger": {
            "transport": "stdio",
            "command": "node",
            "args": ["E:/Langgraph/blogger-mcp-server/dist/index.js"],
            "env": {
                "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
                "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
                "GOOGLE_REDIRECT_URI": "http://localhost:3000/oauth/callback",
            },
        }
    }

    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()
    tool_node = ToolNode(tools)

    agent_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    agent_llm = agent_llm.bind_tools(tools)

    # -------------------------------------------------------
    # Agent Node
    # -------------------------------------------------------
    async def agent_node(state: AgentState):
        system_prompt = SystemMessage(
            content=f"""
You are a Blogger management agent.

BLOG_ID={BLOG_ID}

GENERAL RULES:
- NEVER assume the user wants to update or delete anything unless they clearly say so.
- If the user is asking for content writing (generate, refine, improve wording, etc.), DO NOT call any Blogger tools.
- Only call Blogger tools when the user gives a clear blog management command (delete, list, update, create, edit title, etc.).

DELETE RULE:
- ALWAYS call list_posts first.
- Sort posts by newest.
- Delete EXACTLY the number of posts the user specifies.
- If the user does not specify a number, delete only 1 post.
- NEVER invent postIds.

CONTENT UPDATE PROCEDURE:

When the user requests updating an existing post:

1. ALWAYS perform list_posts first.
2. Sort posts by newest.
3. Identify the correct post:
   - If the user said "update the most recent post", select the newest.
   - If the user gave an ID, select that ID.
4. Retrieve the full HTML content of that post using get_post (if available), otherwise use stored content from list_posts.
5. Generate the updated content according to the user's instructions:
   - Rewrite paragraphs if needed.
   - Add or reposition images.
   - Add justification, explanation, examples, corrections, etc.
6. KEEP all existing formatting safe.
7. Produce a final updated HTML block.
8. Call update_post with:
   - postId = selected post ID
   - title = unchanged unless the user specifies a new title
   - content = updated HTML



CREATE RULE:
- Only call create_post when the user clearly wants to publish or create a new post.
- Do not call create_post during simple draft writing unless it is a final publish action.

IMAGE RULE:
- Only embed a generated image when the user explicitly requests an image.

ALLOWED TOOL CALLS:
- create_post
- update_post
- delete_post
- list_posts
"""
        )

        msgs = state["messages"]

        if len(msgs) == 1:
            response = await agent_llm.ainvoke([system_prompt, msgs[0]])
        else:
            response = await agent_llm.ainvoke([system_prompt] + msgs)

        return {"messages": [response]}

    # -------------------------------------------------------
    # Approval
    # -------------------------------------------------------
    def needs_approval(state: AgentState) -> str:
        last = state["messages"][-1]

        if hasattr(last, "tool_calls") and last.tool_calls:
            name = last.tool_calls[0]["name"]
            if name in CRITICAL_ACTIONS:
                return "ask_human"
            return "execute_tools"

        return "end"

    async def ask_human(state: AgentState):
        # Right now you auto-approve; you could later plug in real UI feedback.
        last = state["messages"][-1]
        tc = last.tool_calls[0]

        return {
            "pending_action": {"tool_call": tc, "approved": True},
            "human_feedback": "yes",
        }

    async def check_approval(state: AgentState):
        if not state["pending_action"]["approved"]:
            return "cancelled"

        tc = state["pending_action"]["tool_call"]

        # Only add image automatically for create_post + explicit "image" in prompt
        if tc["name"] == "create_post":
            user_prompt = state["messages"][0].content.lower()
            if "image" in user_prompt:
                return "add_image"

        return "execute_tools"

    # -------------------------------------------------------
    # Add Image
    # -------------------------------------------------------
    async def add_image_to_post(state: AgentState):
        for m in reversed(state["messages"]):
            if hasattr(m, "tool_calls") and m.tool_calls:
                tc = m.tool_calls[0]
                if tc["name"] == "create_post":
                    title = tc["args"]["title"]
                    content = tc["args"]["content"]
                    img_url = await generate_image(title)
                    # prepend image HTML to content
                    tc["args"]["content"] = f'<img src="{img_url}" alt="Featured image"/><br>{content}'
                    break
        return {"messages": []}

    # -------------------------------------------------------
    # Cancelled
    # -------------------------------------------------------
    async def cancelled(state: AgentState):
        return {"messages": [AIMessage(content="Action cancelled.")]}

    # -------------------------------------------------------
    # Build Graph
    # -------------------------------------------------------
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("ask_human", ask_human)
    graph.add_node("add_image", add_image_to_post)
    graph.add_node("tools", tool_node)
    graph.add_node("cancelled", cancelled)

    graph.add_edge(START, "agent")

    graph.add_conditional_edges(
        "agent",
        needs_approval,
        {"ask_human": "ask_human", "execute_tools": "tools", "end": END},
    )

    graph.add_conditional_edges(
        "ask_human",
        check_approval,
        {"add_image": "add_image", "execute_tools": "tools", "cancelled": "cancelled"},
    )

    graph.add_edge("add_image", "tools")
    # IMPORTANT: stop after tools / cancelled, no looping back to agent
    graph.add_edge("tools", "agent")

    graph.add_edge("cancelled", END)

    workflow = graph.compile()


# -------------------------------------------------------
# Agent Endpoint (delete / list / update via natural language)
# -------------------------------------------------------
@app.post("/agent")
async def agent_handler(request: AgentRequest):
    try:
        state = {
            "messages": [HumanMessage(content=request.message)],
            "pending_action": {},
            "human_feedback": "",
        }

        final_state = await workflow.ainvoke(state)

        last = final_state["messages"][-1]
        return {"response": getattr(last, "content", str(last))}

    except Exception as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------
# GENERATE DRAFT (NO PUBLISHING)
# -------------------------------------------------------
@app.post("/generate")
async def generate_blog(request: GenerateRequest):
    try:
        prompt = f"Write a blog post about: {request.topic}. Only provide the draft content, do not publish yet."

        llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)

        system_msg = SystemMessage(
            content="""You are a professional blog writer.
Write engaging, well-structured blog posts with clear headings, paragraphs, and conclusions.
Use markdown formatting with # for titles and ## for sections."""
        )

        response = await llm.ainvoke([system_msg, HumanMessage(content=prompt)])
        draft = response.content

        return {
            "draft": draft,
            "evaluation": "Draft generated successfully. Ready for your review.",
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------
# REFINE DRAFT BASED ON FEEDBACK
# -------------------------------------------------------
@app.post("/refine")
async def refine_blog(request: RefineRequest):
    try:
        llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)

        system_msg = SystemMessage(
            content="""You are a professional blog writer.
Refine the blog post based on the user's feedback while maintaining quality and structure.
Use markdown formatting with # for titles and ## for sections."""
        )

        prompt = f"""Original Topic: {request.original_topic}

Previous Draft:
{request.previous_draft}

User Feedback:
{request.feedback}

Please revise the blog post according to the feedback provided."""

        response = await llm.ainvoke([system_msg, HumanMessage(content=prompt)])
        refined_draft = response.content

        return {
            "draft": refined_draft,
            "evaluation": "Draft refined based on your feedback.",
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------
# Clean Title Generator
# -------------------------------------------------------
async def generate_clean_title(topic: str) -> str:
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.2)
    system = SystemMessage(
        content="You generate short, meaningful blog titles. Keep them clear, natural, and not clickbait."
    )
    prompt = HumanMessage(
        content=f"User wrote this topic:\n\n{topic}\n\nGive a clean blog title for publishing:"
    )
    result = await llm.ainvoke([system, prompt])
    return result.content.strip()

import traceback
# -------------------------------------------------------
# PUBLISH APPROVED DRAFT
# -------------------------------------------------------
@app.post("/publish")
async def publish_blog(request: PublishRequest):
    try:
        # Work with markdown draft
        content_md = request.content

        # Add image if requested (HTML at top; markdown lib will pass it through)
        if request.include_image:
            img_url = await generate_image(request.title)
            content_md = f'<img src="{img_url}" alt="Featured image"/>\n\n{content_md}'

        # Convert markdown → HTML (safe and structured)
        html_body = markdown.markdown(
            content_md,
            extensions=["extra", "sane_lists"],
        )

        # Generate clean human-friendly title
        title = await generate_clean_title(request.title)

        # Ask the agent to create a post with this exact HTML
        prompt = (
            f"Create a blog post in Blogger with title '{title}' for BLOG_ID={BLOG_ID}. "
            f"Use the following HTML content exactly as provided, without changing its structure:\n\n{html_body}"
        )

        state = {
            "messages": [HumanMessage(content=prompt)],
            "pending_action": {},
            "human_feedback": "",
        }

        final_state = await workflow.ainvoke(state)

        # Try to detect tool output containing postId / url
        for msg in final_state["messages"]:
            if hasattr(msg, "content") and "postId" in str(msg.content):
                # You can parse it more strictly if your tool returns JSON
                return {
                    "success": True,
                    "result": {
                        "title": title,
                        "postId": "AUTO_GENERATED",
                        "url": "https://alok12blogger.blogspot.com",
                    },
                }

        # Fallback if we can't read tool response cleanly
        return {
            "success": True,
            "result": {
                "title": title,
                "postId": "AUTO_GENERATED",
                "url": "https://alok12blogger.blogspot.com",
            },
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Error: {repr(e)}")


@app.get("/")
async def root():
    return {"status": "running"}


@app.get("/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
