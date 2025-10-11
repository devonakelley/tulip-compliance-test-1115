"""
LLM Service for Enterprise QSP System
Handles multi-model AI integration using Emergent LLM Key
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import json
from dataclasses import dataclass
import time

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """LLM response wrapper"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    
class LLMService:
    """Multi-model LLM service using Emergent integration"""
    
    def __init__(self):
        self.client = None
        self.available_models = []
        self._initialized = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize LLM client with Emergent integration"""
        try:
            # Import emergentintegrations for LLM support
            from emergentintegrations import LLMClient
            
            config = settings.get_llm_config()
            
            if config.get("provider") == "emergent" and config.get("api_key"):
                self.client = LLMClient(
                    api_key=config["api_key"],
                    default_model=config.get("model", "gpt-4o")
                )
                
                # Set available models for emergent integration
                self.available_models = [
                    "gpt-4o", "gpt-4o-mini", 
                    "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
                    "gemini-1.5-pro", "gemini-1.5-flash"
                ]
                
                self._initialized = True
                logger.info(f"LLM service initialized with Emergent integration. Models: {self.available_models}")
                
            else:
                logger.warning("Emergent LLM key not configured. AI features will be limited.")
                
        except ImportError:
            logger.error("emergentintegrations package not found. Please install: pip install emergentintegrations")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self._initialized and self.client is not None
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using LLM
        
        Args:
            prompt: User prompt
            model: Model name (optional, uses default)
            max_tokens: Maximum tokens (optional, uses config default)
            temperature: Temperature (optional, uses config default)
            system_prompt: System prompt (optional)
            
        Returns:
            Generated text
        """
        if not self.is_available():
            raise ValueError("LLM service not available")
        
        try:
            start_time = time.time()
            
            # Prepare parameters
            params = {
                "messages": [],
                "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
                "temperature": temperature or settings.LLM_TEMPERATURE
            }
            
            # Add system prompt if provided
            if system_prompt:
                params["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add user prompt
            params["messages"].append({
                "role": "user", 
                "content": prompt
            })
            
            # Use specified model or default
            if model and model in self.available_models:
                params["model"] = model
            
            # Make API call
            response = await self._make_api_call(params)
            
            response_time = time.time() - start_time
            
            # Extract content
            content = self._extract_content(response)
            
            logger.info(f"LLM generation completed in {response_time:.2f}s")
            return content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def analyze_document(
        self,
        document_content: str,
        analysis_type: str = "compliance",
        framework: str = "ISO_13485"
    ) -> Dict[str, Any]:
        """
        Analyze document content for compliance
        
        Args:
            document_content: Document text
            analysis_type: Type of analysis
            framework: Regulatory framework
            
        Returns:
            Analysis results
        """
        if not self.is_available():
            return {"error": "LLM service not available"}
        
        try:
            system_prompt = f"""
            You are an expert regulatory compliance analyst specializing in {framework} for medical devices.
            Analyze the provided document content and provide detailed compliance assessment.
            
            Focus on:
            1. Clause identification and mapping
            2. Compliance gaps
            3. Risk assessment
            4. Recommendations for improvement
            
            Provide structured output in JSON format.
            """
            
            user_prompt = f"""
            Analyze this document content for {framework} compliance:
            
            Document Content:
            {document_content[:4000]}...
            
            Provide analysis in the following JSON structure:
            {{
                "compliance_score": 0.0-100.0,
                "mapped_clauses": [
                    {{
                        "clause_id": "4.1",
                        "clause_title": "General requirements",
                        "confidence": 0.0-1.0,
                        "evidence": "relevant text from document"
                    }}
                ],
                "gaps": [
                    {{
                        "clause_id": "7.3",
                        "description": "Missing requirement description",
                        "severity": "high|medium|low",
                        "recommendation": "Specific action needed"
                    }}
                ],
                "overall_assessment": "Summary of compliance status",
                "priority_actions": ["Action 1", "Action 2"]
            }}
            """
            
            response = await self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                analysis = json.loads(response.strip())
                return analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM analysis response as JSON")
                return {
                    "error": "Failed to parse analysis",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return {"error": str(e)}
    
    async def batch_analyze(
        self,
        documents: List[Dict[str, Any]],
        analysis_type: str = "compliance"
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple documents in batch
        
        Args:
            documents: List of document data
            analysis_type: Type of analysis
            
        Returns:
            List of analysis results
        """
        if not self.is_available():
            return [{"error": "LLM service not available"} for _ in documents]
        
        results = []
        
        # Process documents with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
        async def analyze_single(doc):
            async with semaphore:
                return await self.analyze_document(
                    doc.get("content", ""),
                    analysis_type,
                    doc.get("framework", "ISO_13485")
                )
        
        tasks = [analyze_single(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "document_id": documents[i].get("id", "unknown")
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def compare_documents(
        self,
        doc1_content: str,
        doc2_content: str,
        comparison_type: str = "regulatory_alignment"
    ) -> Dict[str, Any]:
        """
        Compare two documents for regulatory alignment
        
        Args:
            doc1_content: First document content
            doc2_content: Second document content  
            comparison_type: Type of comparison
            
        Returns:
            Comparison results
        """
        if not self.is_available():
            return {"error": "LLM service not available"}
        
        try:
            system_prompt = """
            You are an expert at comparing regulatory documents for alignment and consistency.
            Compare the provided documents and identify differences, gaps, and alignment issues.
            """
            
            user_prompt = f"""
            Compare these two regulatory documents:
            
            Document 1:
            {doc1_content[:2000]}...
            
            Document 2:
            {doc2_content[:2000]}...
            
            Provide comparison in JSON format:
            {{
                "alignment_score": 0.0-100.0,
                "differences": [
                    {{
                        "section": "section identifier",
                        "type": "missing|different|conflicting",
                        "description": "description of difference",
                        "impact": "high|medium|low"
                    }}
                ],
                "recommendations": ["recommendation 1", "recommendation 2"],
                "summary": "Overall comparison summary"
            }}
            """
            
            response = await self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.1
            )
            
            try:
                comparison = json.loads(response.strip())
                return comparison
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse comparison",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            return {"error": str(e)}
    
    async def _make_api_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call to LLM service"""
        try:
            # Use emergentintegrations client
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                **params
            )
            return response
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _extract_content(self, response: Any) -> str:
        """Extract content from LLM response"""
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return choice.message.content
                elif hasattr(choice, 'text'):
                    return choice.text
            
            # Fallback for different response formats
            if isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    return response['choices'][0].get('message', {}).get('content', '')
                elif 'content' in response:
                    return response['content']
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Failed to extract content from response: {e}")
            return ""
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        # This would track usage statistics
        # For now, return basic info
        return {
            "service_available": self.is_available(),
            "models_available": self.available_models,
            "initialized": self._initialized
        }