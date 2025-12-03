"""LangGraph-based multi-agent orchestration for debates."""
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from sqlalchemy.orm import Session
from models import Agent, DebateSession, DebateMessage, UserProfile
from services.llm_clients import LLMClientFactory
from services.prompt_parser import PromptParser


class DebateFormat(Enum):
    """Debate format types."""
    TURN_BASED = "turn_based"  # Agents take turns in order
    MODERATED = "moderated"  # A moderator decides who speaks
    FREE_FORM = "free_form"  # Agents respond when relevant


@dataclass
class AgentState:
    """State for a single agent in the debate."""
    agent_id: int
    name: str
    role: str
    llm_client: Any
    system_prompt: str
    temperature: float
    max_tokens: int


@dataclass
class DebateState:
    """Overall state of the debate."""
    session_id: int
    topic: str
    agents: List[AgentState]
    messages: List[Dict[str, Any]]
    current_turn: int
    max_turns: int
    format: DebateFormat
    user_profile_context: Dict[str, Any]
    is_complete: bool = False


class AgentOrchestrator:
    """Orchestrate multi-agent debates using LangGraph."""
    
    def __init__(self, db_session: Session):
        """
        Initialize the agent orchestrator.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.prompt_parser = PromptParser()
    
    async def start_debate(
        self,
        session_id: int,
        agent_ids: List[int],
        topic: str,
        max_turns: int = 10,
        debate_format: str = "turn_based"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Start a debate session between multiple agents.
        
        Args:
            session_id: Database ID of the debate session
            agent_ids: List of agent IDs to participate
            topic: Topic or decision to discuss
            max_turns: Maximum number of turns
            debate_format: Format of debate
            
        Yields:
            Agent messages as they are generated
        """
        # Load agents from database
        agents = self.db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        
        if len(agents) < 2:
            raise ValueError("At least 2 agents required for a debate")
        
        # Get user profile for context
        user_profile = agents[0].user_profile
        
        # Build user context for variable substitution
        user_context = {
            "user_profile_summary": user_profile.profile_summary or "No profile available",
            "decision_topic": topic,
            "user_expertise_areas": ", ".join(user_profile.expertise_areas or []),
            "user_risk_tolerance": user_profile.risk_tolerance or "moderate"
        }
        
        # Initialize agent states
        agent_states = []
        for agent in agents:
            # Parse and substitute variables in prompt
            parsed_prompt = self.prompt_parser.parse(agent.system_prompt_raw)
            substituted_prompt = self.prompt_parser.substitute_variables(
                parsed_prompt,
                user_context
            )
            formatted_prompt = self.prompt_parser.format_system_prompt(substituted_prompt)
            
            # Create LLM client
            llm_client = LLMClientFactory.create_client(
                agent.model_provider,
                agent.model_name
            )
            
            agent_state = AgentState(
                agent_id=agent.id,
                name=agent.name,
                role=agent.role,
                llm_client=llm_client,
                system_prompt=formatted_prompt,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            agent_states.append(agent_state)
        
        # Initialize debate state
        debate_state = DebateState(
            session_id=session_id,
            topic=topic,
            agents=agent_states,
            messages=[],
            current_turn=0,
            max_turns=max_turns,
            format=DebateFormat(debate_format),
            user_profile_context=user_context
        )
        
        # Update session status
        session = self.db.query(DebateSession).filter(
            DebateSession.id == session_id
        ).first()
        if session:
            session.status = "active"
            session.started_at = datetime.utcnow()
            self.db.commit()
        
        # Run debate based on format
        if debate_state.format == DebateFormat.TURN_BASED:
            async for message in self._run_turn_based_debate(debate_state):
                yield message
        else:
            # For now, default to turn-based; can implement others later
            async for message in self._run_turn_based_debate(debate_state):
                yield message
        
        # Mark session as complete
        if session:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            self.db.commit()
    
    async def _run_turn_based_debate(
        self,
        state: DebateState
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run a turn-based debate where agents take turns speaking.
        
        Args:
            state: Debate state
            
        Yields:
            Agent messages
        """
        # Initial system message to set context
        context_message = f"""You are participating in a collaborative decision-making discussion about:

TOPIC: {state.topic}

Your goal is to provide thoughtful input based on your role and perspective. Listen to other participants and build on their ideas while maintaining your unique viewpoint.

The discussion will proceed in turns. Share your insights, ask questions, and help arrive at a well-reasoned decision."""
        
        for turn in range(state.max_turns):
            state.current_turn = turn
            
            # Each agent speaks in turn
            for agent_idx, agent_state in enumerate(state.agents):
                # Build conversation history for context
                conversation_history = self._build_conversation_history(state.messages)
                
                # Build prompt for this agent
                if turn == 0 and agent_idx == 0:
                    # First agent introduces the topic
                    prompt = f"{context_message}\n\nPlease share your initial thoughts on this topic."
                elif turn == 0:
                    # Other agents respond to first agent
                    prompt = f"{context_message}\n\nThe discussion has begun. Please share your perspective."
                else:
                    # Subsequent turns: respond to the conversation
                    prompt = "Based on the discussion so far, what are your thoughts? Do you have any questions or additional insights?"
                
                # Add conversation history as context
                full_prompt = f"{conversation_history}\n\n{prompt}" if conversation_history else prompt
                
                # Generate response
                start_time = datetime.utcnow()
                
                try:
                    response = await agent_state.llm_client.generate(
                        prompt=full_prompt,
                        system_prompt=agent_state.system_prompt,
                        temperature=agent_state.temperature,
                        max_tokens=agent_state.max_tokens
                    )
                    
                    response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    
                    # Store message
                    message_data = {
                        "agent_id": agent_state.agent_id,
                        "agent_name": agent_state.name,
                        "agent_role": agent_state.role,
                        "content": response,
                        "turn": turn,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    state.messages.append(message_data)
                    
                    # Save to database
                    db_message = DebateMessage(
                        debate_session_id=state.session_id,
                        agent_id=agent_state.agent_id,
                        content=response,
                        turn_number=turn,
                        response_time_ms=response_time
                    )
                    self.db.add(db_message)
                    self.db.commit()
                    
                    # Yield message for streaming
                    yield message_data
                    
                except Exception as e:
                    print(f"Error generating response for agent {agent_state.name}: {str(e)}")
                    # Continue with next agent
                    continue
                
                # Small delay between agents for better UX
                await asyncio.sleep(0.5)
    
    def _build_conversation_history(
        self,
        messages: List[Dict[str, Any]],
        max_messages: int = 10
    ) -> str:
        """
        Build conversation history string from messages.
        
        Args:
            messages: List of message dictionaries
            max_messages: Maximum messages to include
            
        Returns:
            Formatted conversation history
        """
        if not messages:
            return ""
        
        # Get recent messages
        recent_messages = messages[-max_messages:]
        
        history_lines = ["CONVERSATION SO FAR:"]
        for msg in recent_messages:
            history_lines.append(
                f"\n{msg['agent_name']} ({msg['agent_role']}):\n{msg['content']}"
            )
        
        return "\n".join(history_lines)
    
    async def generate_debate_summary(
        self,
        session_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a summary of the debate and key insights.
        
        Args:
            session_id: ID of the debate session
            
        Returns:
            Summary with decision and insights
        """
        try:
            # Get session and messages
            session = self.db.query(DebateSession).filter(
                DebateSession.id == session_id
            ).first()
            
            if not session:
                return None
            
            messages = self.db.query(DebateMessage).filter(
                DebateMessage.debate_session_id == session_id
            ).order_by(DebateMessage.turn_number).all()
            
            if not messages:
                return {"summary": "No discussion took place.", "insights": []}
            
            # Build full conversation
            conversation = []
            for msg in messages:
                agent = self.db.query(Agent).filter(Agent.id == msg.agent_id).first()
                if agent:
                    conversation.append(f"{agent.name}: {msg.content}")
            
            full_conversation = "\n\n".join(conversation)
            
            # Use Gemini to generate summary
            llm_client = LLMClientFactory.create_client("gemini", "gemini-2.5-flash")
            
            summary_prompt = f"""Analyze the following decision-making discussion and provide:
1. A concise summary of the main decision or conclusion (2-3 sentences)
2. 3-5 key insights or important points raised
3. Any areas of agreement or disagreement

Discussion Topic: {session.topic}

Conversation:
{full_conversation}

Provide your analysis:"""
            
            summary_response = await llm_client.generate(
                prompt=summary_prompt,
                temperature=0.3,
                max_tokens=600
            )
            
            # Store summary
            session.decision_summary = summary_response
            self.db.commit()
            
            return {
                "summary": summary_response,
                "message_count": len(messages),
                "agents_participated": len(set(msg.agent_id for msg in messages))
            }
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return None
