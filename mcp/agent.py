"""
Open Notebook Agent - Customer Onboarding & Assistance Agent

A LangGraph-based agent that helps customers:
1. Onboard to the platform
2. Learn to use features effectively
3. Get maximum value from Open Notebook

Built using LangGraph specification pattern.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
import os


# =============================================================================
# State Definitions
# =============================================================================


class AgentState(BaseModel):
    """Main agent state."""

    # User context
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_goal: Optional[str] = None
    
    # Conversation context
    messages: list = Field(default_factory=list)
    current_notebook_id: Optional[str] = None
    current_notebook_name: Optional[str] = None
    
    # Onboarding progress
    onboarding_step: Literal[
        "greeting",
        "goal_discovery",
        "feature_intro",
        "hands_on",
        "value_optimization",
        "complete"
    ] = "greeting"
    features_shown: list[str] = Field(default_factory=list)
    
    # Task tracking
    tasks_completed: list[str] = Field(default_factory=list)
    pending_tasks: list[str] = Field(default_factory=list)
    
    # Context
    last_action: Optional[str] = None
    last_result: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Node Functions
# =============================================================================


def greeting_node(state: AgentState) -> AgentState:
    """Initial greeting and user identification."""
    state.onboarding_step = "greeting"
    
    welcome_msg = """Welcome to Open Notebook! 👋

I'm your AI assistant, here to help you:
- Get started with Open Notebook
- Learn all the features
- Get the most out of your research

What would you like to do today?

A) Start a new research project
B) Learn about features
C) Get help with something specific
D) Just explore
"""
    state.messages.append(AIMessage(content=welcome_msg))
    return state


def goal_discovery_node(state: AgentState) -> AgentState:
    """Discover user's goals and use case."""
    state.onboarding_step = "goal_discovery"
    
    goal_msg = """That's great! To help you best, I'd like to understand your goals.

What are you trying to accomplish with Open Notebook?

Examples:
- Research for a project
- Summarize documents/papers
- Create audio podcasts from content
- Build a personal knowledge base
- Analyze and extract insights from sources
"""
    state.messages.append(AIMessage(content=goal_msg))
    return state


def feature_intro_node(state: AgentState) -> AgentState:
    """Introduce relevant features based on user goals."""
    state.onboarding_step = "feature_intro"
    
    # Map goals to features
    feature_map = {
        "research": ["notebooks", "sources", "chat", "search"],
        "summarize": ["notebooks", "sources", "podcasts"],
        "podcast": ["podcasts", "sources", "audio"],
        "knowledge": ["notebooks", "sources", "embeddings", "search"],
        "analyze": ["insights", "sources", "chat", "search"],
    }
    
    user_goal_lower = (state.user_goal or "").lower()
    relevant_features = []
    for key, features in feature_map.items():
        if key in user_goal_lower:
            relevant_features.extend(features)
    
    state.features_shown = list(set(relevant_features))
    
    intro_msg = f"""Perfect! Based on your goal: "{state.user_goal}"

Here are the features that'll help you most:

"""
    
    feature_descriptions = {
        "notebooks": "📓 **Notebooks** - Organize your research into separate containers",
        "sources": "📄 **Sources** - Add URLs, PDFs, text, or audio content",
        "chat": "💬 **Chat** - Ask questions and have conversations with your sources",
        "search": "🔍 **Search** - Find relevant content using semantic search",
        "podcasts": "🎙️ **Podcasts** - Generate audio summaries of your content",
        "embeddings": "🧠 **Embeddings** - AI-powered understanding of your content",
        "insights": "💡 **Insights** - Extract key findings automatically",
        "audio": "🎵 **Audio** - Work with audio files and recordings",
    }
    
    for feature in state.features_shown:
        if feature in feature_descriptions:
            intro_msg += feature_descriptions[feature] + "\n"
    
    intro_msg += """

Would you like to:
1. Create your first notebook and add some sources?
2. See a demo of how a feature works?
3. Learn more about a specific feature?
"""
    
    state.messages.append(AIMessage(content=intro_msg))
    return state


def hands_on_node(state: AgentState) -> AgentState:
    """Guide user through hands-on experience."""
    state.onboarding_step = "hands_on"
    
    hands_on_msg = """Let's get hands-on! 🎯

I'll guide you through creating your first notebook and adding sources.

**Step 1: Create a Notebook**
Tell me what you'd like to name your first notebook (e.g., "My Research Project")

Or I can create a sample one for you to explore.
"""
    
    state.messages.append(AIMessage(content=hands_on_msg))
    return state


def value_optimization_node(state: AgentState) -> AgentState:
    """Help user get maximum value from the platform."""
    state.onboarding_step = "value_optimization"
    
    optimization_msg = """Now that you've got the basics, let's optimize your experience! 🚀

**Pro Tips for Maximum Value:**

1. **Organize by Project** - Create separate notebooks for different research projects

2. **Quality Sources** - Add diverse, high-quality sources for better answers

3. **Rebuild Embeddings** - Re-index after adding new sources for accurate search

4. **Try Podcasts** - Great for consuming research on the go

5. **Chat Sessions** - Use continuous chats for deep dives into topics

6. **API Keys** - Set up your own API keys for more control

What would you like to explore next?
"""
    
    state.messages.append(AIMessage(content=optimization_msg))
    return state


def complete_node(state: AgentState) -> AgentState:
    """Mark onboarding as complete."""
    state.onboarding_step = "complete"
    
    complete_msg = """You're all set! 🎉

You're now ready to make the most of Open Notebook.

**Quick Reference:**
- Create notebooks to organize research
- Add sources (URLs, PDFs, text, audio)
- Chat with your sources for insights
- Generate podcasts for audio summaries
- Search semantically across all content

I'm always here to help! Just ask:
- "Help me add a source"
- "Show me how to search"
- "Create a podcast from my notebook"
- Any other questions!

Happy researching! 📚
"""
    
    state.messages.append(AIMessage(content=complete_msg))
    return state


def should_continue_onboarding(state: AgentState) -> Literal["goal_discovery", "feature_intro", "hands_on", "value_optimization", "complete"]:
    """Determine next step in onboarding flow."""
    if state.onboarding_step == "greeting":
        return "goal_discovery"
    elif state.onboarding_step == "goal_discovery":
        return "feature_intro"
    elif state.onboarding_step == "feature_intro":
        return "hands_on"
    elif state.onboarding_step == "hands_on":
        return "value_optimization"
    elif state.onboarding_step == "value_optimization":
        return "complete"
    return END


def route_based_on_intent(state: AgentState) -> Literal["onboarding", "notebook_ops", "source_ops", "chat", "search", "podcast", "help", "general"]:
    """Route to appropriate handler based on user intent."""
    # Simple keyword-based routing
    last_message = state.messages[-1].content if state.messages else ""
    last_message_lower = last_message.lower()
    
    if any(word in last_message_lower for word in ["create", "new", "notebook", "add"]):
        return "notebook_ops"
    elif any(word in last_message_lower for word in ["source", "url", "pdf", "upload", "add"]):
        return "source_ops"
    elif any(word in last_message_lower for word in ["chat", "ask", "question", "talk"]):
        return "chat"
    elif any(word in last_message_lower for word in ["search", "find", "look for"]):
        return "search"
    elif any(word in last_message_lower for word in ["podcast", "audio", "generate"]):
        return "podcast"
    elif any(word in last_message_lower for word in ["help", "how", "what", "explain"]):
        return "help"
    elif state.onboarding_step != "complete":
        return "onboarding"
    
    return "general"


# =============================================================================
# Build the Graph
# =============================================================================


def create_agent_graph() -> StateGraph:
    """Create the LangGraph state machine for the onboarding agent."""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("goal_discovery", goal_discovery_node)
    workflow.add_node("feature_intro", feature_intro_node)
    workflow.add_node("hands_on", hands_on_node)
    workflow.add_node("value_optimization", value_optimization_node)
    workflow.add_node("complete", complete_node)
    
    # Add edges
    workflow.set_entry_point("greeting")
    workflow.add_conditional_edges(
        "greeting",
        should_continue_onboarding,
        {
            "goal_discovery": "goal_discovery",
            "feature_intro": "feature_intro",
            "hands_on": "hands_on",
            "value_optimization": "value_optimization",
            "complete": "complete",
            END: END,
        }
    )
    workflow.add_conditional_edges(
        "goal_discovery",
        should_continue_onboarding,
        {
            "feature_intro": "feature_intro",
            "hands_on": "hands_on",
            "value_optimization": "value_optimization",
            "complete": "complete",
            END: END,
        }
    )
    workflow.add_conditional_edges(
        "feature_intro",
        should_continue_onboarding,
        {
            "hands_on": "hands_on",
            "value_optimization": "value_optimization",
            "complete": "complete",
            END: END,
        }
    )
    workflow.add_conditional_edges(
        "hands_on",
        should_continue_onboarding,
        {
            "value_optimization": "value_optimization",
            "complete": "complete",
            END: END,
        }
    )
    workflow.add_conditional_edges(
        "value_optimization",
        should_continue_onboarding,
        {
            "complete": "complete",
            END: END,
        }
    )
    workflow.add_edge("complete", END)
    
    return workflow


# =============================================================================
# Agent Runner
# =============================================================================


class OnboardingAgent:
    """Customer onboarding and assistance agent."""

    def __init__(self):
        self.graph = create_agent_graph().compile(checkpointer=MemorySaver())
        
        # Initialize LLM (use configured model)
        model_provider = os.getenv("ONBOARDING_MODEL_PROVIDER", "openai")
        model_name = os.getenv("ONBOARDING_MODEL", "gpt-4o-mini")
        
        if model_provider == "anthropic":
            self.llm = ChatAnthropic(model=model_name)
        else:
            self.llm = ChatOpenAI(model=model_name)

    async def run(self, user_input: str, thread_id: str = "default") -> AgentState:
        """Run the agent with user input."""
        
        # Create initial state
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = AgentState(
            messages=[HumanMessage(content=user_input)]
        )
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state, config)
        
        return result

    async def start_onboarding(self, user_name: str, thread_id: str = "default") -> AgentState:
        """Start the onboarding flow."""
        
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = AgentState(
            user_name=user_name,
            messages=[]
        )
        
        result = await self.graph.ainvoke(initial_state, config)
        
        return result

    def get_state(self, thread_id: str = "default") -> Optional[AgentState]:
        """Get current state for a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        
        if state:
            return state.values
        
        return None


# =============================================================================
# MCP Integration
# =============================================================================

# This agent can be exposed via the MCP server for AI-to-AI interaction
# or used directly via the API

__all__ = [
    "AgentState",
    "OnboardingAgent", 
    "create_agent_graph",
]