"""
Supplement Guidance Agent for non-medical supplement information and guidance.

This module provides the SupplementGuideAgent that handles supplement-related queries
with strong disclaimers about non-medical guidance and healthcare professional consultation.
"""

import json
import logging
from datetime import datetime
from typing import AsyncIterator, List

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse

logger = logging.getLogger(__name__)


class SupplementGuideAgent(BaseAgent):
    """
    Specialized agent for supplement information and guidance.
    
    This agent handles:
    - Providing general supplement information
    - Checking potential supplement interactions
    - Emphasizing non-medical guidance
    - Recommending healthcare professional consultation
    
    CRITICAL: This agent provides NON-MEDICAL guidance only and always
    includes disclaimers about consulting healthcare professionals.
    """
    
    async def process_text(self, query: str) -> AgentResponse:
        """
        Process a text query and return a detailed response with tool calling.
        
        Builds messages with full conversation history, creates a tool-calling
        agent, and returns a structured AgentResponse with markdown formatting
        and prominent disclaimers.
        
        Args:
            query: User's text query
            
        Returns:
            AgentResponse with content, agent type, tools used, and metadata
        """
        # Build messages with full history for text mode
        messages = self._build_messages(query, voice_mode=False)
        
        # Get tools for this agent
        tools = self.get_tools()
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)
        
        # Call LLM with tools
        response = await llm_with_tools.ainvoke(messages)
        
        # Track which tools were called
        tools_used = []
        
        # If LLM wants to call tools, execute them
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tools_used.append(tool_call['name'])
                
                # Find and execute the tool
                for t in tools:
                    if t.name == tool_call['name']:
                        try:
                            tool_result = await t.ainvoke(tool_call['args'])
                            # Add tool result to messages and get final response
                            messages.append(response)
                            messages.append(HumanMessage(content=f"Tool result: {tool_result}"))
                            response = await self.llm.ainvoke(messages)
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            response.content = f"I encountered an error while processing your request. Please try again."
        
        # Return structured response
        return AgentResponse(
            content=response.content,
            agent_type="supplement",
            tools_used=tools_used,
            metadata={
                "mode": "text",
                "user_id": self.context.user_id,
                "fitness_level": self.context.fitness_level,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def process_voice(self, query: str) -> str:
        """
        Process a voice query and return a concise response with disclaimers.
        
        Builds messages with limited conversation history for low-latency,
        calls the LLM without tools, and returns a plain string suitable
        for text-to-speech (under 75 words) with disclaimer included.
        
        Args:
            query: User's voice query (transcribed to text)
            
        Returns:
            str: Concise response text suitable for text-to-speech with disclaimer
        """
        # Build messages with limited history for voice mode
        messages = self._build_messages(query, voice_mode=True)
        
        # Call LLM without tools for faster response
        response = await self.llm.ainvoke(messages)
        
        # Return plain string for voice
        return response.content
    
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """
        Stream response chunks for real-time display.
        
        Builds messages and uses the LLM's streaming capability to yield
        response chunks as they are generated.
        
        Args:
            query: User's query
            
        Yields:
            str: Response chunks as they are generated
        """
        # Build messages
        messages = self._build_messages(query, voice_mode=False)
        
        # Stream response chunks
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    
    def get_tools(self) -> List:
        """
        Get the list of tools available to the supplement guidance agent.
        
        Returns:
            List: List of LangChain tools for supplement information operations
        """
        # Create closures to pass context to tools
        context = self.context
        
        @tool
        async def get_supplement_info(supplement_name: str) -> str:
            """Get general information about a supplement.
            
            Args:
                supplement_name: Name of the supplement to get information about
                
            Returns:
                JSON string with general supplement information and disclaimer
            """
            try:
                # Disclaimer text
                disclaimer = (
                    "IMPORTANT DISCLAIMER: This information is for educational purposes only "
                    "and is NOT medical advice. Always consult with a qualified healthcare "
                    "professional before starting any supplement regimen."
                )
                
                # Common supplement information database
                # In a production system, this would query a comprehensive supplement database
                supplement_info_db = {
                    "protein powder": {
                        "description": "Dietary supplement derived from whey, casein, soy, or plant sources",
                        "common_uses": ["Muscle building", "Post-workout recovery", "Meeting daily protein needs"],
                        "typical_dosage": "20-30g per serving, 1-2 times daily",
                        "timing": "Post-workout or between meals",
                        "considerations": ["Check for allergens (dairy, soy)", "Quality varies by brand", "Not necessary if protein needs met through diet"],
                        "evidence_level": "Strong scientific support for muscle building and recovery"
                    },
                    "creatine": {
                        "description": "Naturally occurring compound that helps produce energy during high-intensity exercise",
                        "common_uses": ["Increased strength", "Improved high-intensity performance", "Muscle mass gains"],
                        "typical_dosage": "3-5g daily (maintenance), 20g daily for 5-7 days (loading phase)",
                        "timing": "Any time of day, consistency is key",
                        "considerations": ["Well-researched and safe", "May cause water retention", "Drink adequate water"],
                        "evidence_level": "Extensive scientific support, one of the most researched supplements"
                    },
                    "bcaa": {
                        "description": "Branched-Chain Amino Acids (leucine, isoleucine, valine)",
                        "common_uses": ["Muscle recovery", "Reducing exercise fatigue", "Preventing muscle breakdown"],
                        "typical_dosage": "5-10g before or during workout",
                        "timing": "Pre-workout or intra-workout",
                        "considerations": ["May be unnecessary if consuming adequate protein", "Benefits debated in research"],
                        "evidence_level": "Mixed evidence, may be redundant with adequate protein intake"
                    },
                    "multivitamin": {
                        "description": "Combination of essential vitamins and minerals",
                        "common_uses": ["Filling nutritional gaps", "General health support", "Immune function"],
                        "typical_dosage": "One tablet daily with food",
                        "timing": "With a meal for better absorption",
                        "considerations": ["Not a replacement for healthy diet", "Quality varies significantly", "Some nutrients better from food"],
                        "evidence_level": "Moderate support for filling dietary gaps, limited evidence for disease prevention"
                    },
                    "omega-3": {
                        "description": "Essential fatty acids (EPA and DHA) typically from fish oil",
                        "common_uses": ["Heart health", "Brain function", "Reducing inflammation"],
                        "typical_dosage": "1-3g combined EPA/DHA daily",
                        "timing": "With meals to improve absorption",
                        "considerations": ["Check for mercury and purity", "May interact with blood thinners", "Vegetarian alternatives available (algae-based)"],
                        "evidence_level": "Strong evidence for cardiovascular and cognitive benefits"
                    },
                    "vitamin d": {
                        "description": "Fat-soluble vitamin important for bone health and immune function",
                        "common_uses": ["Bone health", "Immune support", "Mood regulation"],
                        "typical_dosage": "1000-4000 IU daily (varies by individual needs)",
                        "timing": "With a meal containing fat",
                        "considerations": ["Many people are deficient", "Blood test recommended", "Toxicity possible at very high doses"],
                        "evidence_level": "Strong evidence for bone health and immune function"
                    },
                    "caffeine": {
                        "description": "Stimulant that increases alertness and can enhance exercise performance",
                        "common_uses": ["Increased energy", "Improved focus", "Enhanced endurance"],
                        "typical_dosage": "100-400mg daily (varies by tolerance)",
                        "timing": "30-60 minutes before workout or when alertness needed",
                        "considerations": ["Can cause jitters and anxiety", "May disrupt sleep", "Tolerance develops", "Avoid late in day"],
                        "evidence_level": "Strong evidence for performance enhancement and alertness"
                    },
                    "pre-workout": {
                        "description": "Blend of ingredients designed to enhance workout performance",
                        "common_uses": ["Increased energy", "Better focus", "Enhanced endurance"],
                        "typical_dosage": "One serving 20-30 minutes before workout",
                        "timing": "Pre-workout",
                        "considerations": ["Ingredients vary widely", "Often contains caffeine", "May cause tingling (beta-alanine)", "Check ingredient list carefully"],
                        "evidence_level": "Varies by ingredients; caffeine and creatine have strong support"
                    }
                }
                
                # Normalize supplement name for lookup
                supplement_key = supplement_name.lower().strip()
                
                # Check if we have information for this supplement
                if supplement_key in supplement_info_db:
                    info = supplement_info_db[supplement_key]
                    
                    return json.dumps({
                        "success": True,
                        "data": {
                            "supplement_name": supplement_name,
                            "description": info["description"],
                            "common_uses": info["common_uses"],
                            "typical_dosage": info["typical_dosage"],
                            "timing": info["timing"],
                            "considerations": info["considerations"],
                            "evidence_level": info["evidence_level"],
                            "disclaimer": disclaimer
                        },
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "supplement_guide_agent"
                        }
                    })
                else:
                    # Generic response for supplements not in database
                    return json.dumps({
                        "success": True,
                        "data": {
                            "supplement_name": supplement_name,
                            "message": f"I don't have detailed information about {supplement_name} in my database. "
                                      f"For accurate information about this supplement, please consult with a "
                                      f"qualified healthcare professional, registered dietitian, or pharmacist.",
                            "disclaimer": disclaimer,
                            "recommendation": "Always research supplements from reputable sources and consult healthcare professionals"
                        },
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "supplement_guide_agent"
                        }
                    })
                
            except Exception as e:
                logger.error(f"Error in get_supplement_info: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve supplement information. Please try again.",
                    "disclaimer": "This is not medical advice. Consult a healthcare professional."
                })
        
        @tool
        async def check_supplement_interactions(supplements: List[str]) -> str:
            """Check for potential interactions between supplements.
            
            Args:
                supplements: List of supplement names to check for interactions
                
            Returns:
                JSON string with potential interaction information and disclaimer
            """
            try:
                # Disclaimer text
                disclaimer = (
                    "CRITICAL DISCLAIMER: This information is for educational purposes only. "
                    "Supplement interactions can be serious. ALWAYS consult with a qualified "
                    "healthcare professional, pharmacist, or registered dietitian before "
                    "combining supplements or if you are taking any medications."
                )
                
                if not supplements or len(supplements) < 2:
                    return json.dumps({
                        "success": False,
                        "error": "Please provide at least 2 supplements to check for interactions",
                        "disclaimer": disclaimer
                    })
                
                # Known interaction database
                # In production, this would be a comprehensive medical database
                known_interactions = {
                    ("caffeine", "pre-workout"): {
                        "severity": "Moderate",
                        "description": "Pre-workout supplements often contain caffeine. Combining may lead to excessive caffeine intake.",
                        "effects": ["Jitters", "Anxiety", "Rapid heartbeat", "Sleep disruption"],
                        "recommendation": "Check caffeine content in pre-workout. Total daily caffeine should not exceed 400mg."
                    },
                    ("omega-3", "vitamin e"): {
                        "severity": "Low to Moderate",
                        "description": "Both have blood-thinning properties. High doses may increase bleeding risk.",
                        "effects": ["Increased bleeding risk", "Bruising"],
                        "recommendation": "Use moderate doses. Inform doctor before surgery. Avoid if on blood thinners."
                    },
                    ("calcium", "iron"): {
                        "severity": "Moderate",
                        "description": "Calcium can interfere with iron absorption.",
                        "effects": ["Reduced iron absorption"],
                        "recommendation": "Take at different times of day (separate by 2+ hours)."
                    },
                    ("vitamin d", "calcium"): {
                        "severity": "Positive Interaction",
                        "description": "Vitamin D enhances calcium absorption. This is a beneficial combination.",
                        "effects": ["Improved calcium absorption", "Better bone health"],
                        "recommendation": "This is a recommended combination for bone health."
                    },
                    ("caffeine", "creatine"): {
                        "severity": "Low",
                        "description": "Some older research suggested caffeine might reduce creatine effectiveness, but recent studies show minimal impact.",
                        "effects": ["Possibly reduced creatine benefits (debated)"],
                        "recommendation": "Generally safe to combine. Stay well hydrated."
                    }
                }
                
                # Normalize supplement names
                normalized_supplements = [s.lower().strip() for s in supplements]
                
                # Check for interactions
                found_interactions = []
                general_warnings = []
                
                # Check all pairs
                for i in range(len(normalized_supplements)):
                    for j in range(i + 1, len(normalized_supplements)):
                        pair = tuple(sorted([normalized_supplements[i], normalized_supplements[j]]))
                        
                        if pair in known_interactions:
                            interaction = known_interactions[pair]
                            found_interactions.append({
                                "supplements": [normalized_supplements[i], normalized_supplements[j]],
                                "severity": interaction["severity"],
                                "description": interaction["description"],
                                "effects": interaction["effects"],
                                "recommendation": interaction["recommendation"]
                            })
                
                # Add general warnings
                if "caffeine" in normalized_supplements or "pre-workout" in normalized_supplements:
                    general_warnings.append("Monitor total caffeine intake from all sources (coffee, tea, supplements)")
                
                if len(normalized_supplements) > 5:
                    general_warnings.append("Taking many supplements increases risk of interactions. Consult healthcare professional.")
                
                # Build response
                if found_interactions:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "supplements_checked": supplements,
                            "interactions_found": len(found_interactions),
                            "interactions": found_interactions,
                            "general_warnings": general_warnings,
                            "disclaimer": disclaimer,
                            "important_note": "This is not a comprehensive interaction check. Many interactions exist that are not listed here."
                        },
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "supplement_guide_agent"
                        }
                    })
                else:
                    return json.dumps({
                        "success": True,
                        "data": {
                            "supplements_checked": supplements,
                            "interactions_found": 0,
                            "message": "No known interactions found in our database for this combination.",
                            "general_warnings": general_warnings,
                            "disclaimer": disclaimer,
                            "important_note": "Absence of known interactions does not guarantee safety. Always consult healthcare professionals."
                        },
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "supplement_guide_agent"
                        }
                    })
                
            except Exception as e:
                logger.error(f"Error in check_supplement_interactions: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to check supplement interactions. Please try again.",
                    "disclaimer": "This is not medical advice. Consult a healthcare professional."
                })
        
        return [get_supplement_info, check_supplement_interactions]
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the supplement guidance agent.
        
        Creates a specialized system prompt with strong non-medical disclaimers,
        user context, and behavioral guidelines. The prompt varies based on
        whether the interaction is voice or text.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM with prominent disclaimers
        """
        base_prompt = f"""You are a supplement information assistant for the Shuren fitness coaching system providing NON-MEDICAL guidance.

CRITICAL DISCLAIMERS - ALWAYS INCLUDE IN RESPONSES:
- You provide general educational information only
- You are NOT a medical professional, doctor, or pharmacist
- Users MUST consult qualified healthcare providers for medical advice
- You do NOT diagnose conditions or prescribe supplements
- Supplement use should be discussed with healthcare professionals
- Individual needs vary greatly - what works for one person may not work for another

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}

Your Role:
- Provide evidence-based general information about supplements
- Explain common uses and typical dosages (educational only)
- Highlight potential interactions and considerations
- Emphasize the importance of professional consultation
- Be clear about limitations of your knowledge

Guidelines:
- ALWAYS include disclaimers about non-medical guidance
- ALWAYS recommend consulting healthcare professionals
- Provide evidence-based information when available
- Be honest about uncertainty or lack of evidence
- Never diagnose conditions or prescribe specific supplements
- Emphasize that supplements are not substitutes for proper diet
- Highlight potential risks and side effects
- Mention that supplement quality and regulation varies
- Encourage blood tests and professional monitoring when relevant

Available Tools:
- get_supplement_info: Get general information about a supplement (includes disclaimer)
- check_supplement_interactions: Check for potential interactions between supplements (includes disclaimer)

IMPORTANT REMINDERS:
- Supplements can interact with medications
- Individual responses vary greatly
- Quality and purity vary by manufacturer
- More is not always better - dosage matters
- Some supplements may be unnecessary with proper diet
- Professional guidance is essential for safety
"""
        
        if voice_mode:
            base_prompt += "\n\nVOICE MODE: Keep responses concise (under 30 seconds when spoken, approximately 75 words) but ALWAYS include a brief disclaimer about consulting healthcare professionals."
        else:
            base_prompt += "\n\nTEXT MODE: Provide detailed information with markdown formatting. Include prominent disclaimers at the beginning or end of responses. Use headers, lists, and emphasis to improve readability and highlight important safety information."
        
        return base_prompt
