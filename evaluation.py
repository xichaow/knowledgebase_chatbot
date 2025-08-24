import os
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import json

# Load environment variables
load_dotenv()

# Judge LLM (separate from chat LLM for evaluation)
judge_llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.1,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

class SimpleAPRAEvaluator:
    """Simple APRA-specific evaluation system using only LLM-as-Judge"""
    
    def __init__(self):
        self.judge_llm = judge_llm
    
    async def evaluate_conversation(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        trace_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single conversation using LLM-as-Judge
        """
        
        print(f"🔍 Evaluating conversation: {trace_id}")
        
        # Run LLM judge evaluation
        judge_results = await self._run_llm_judge_evaluation(question, answer, contexts)
        
        # Print results for visibility
        print(f"📊 Evaluation Results for {trace_id}:")
        for metric, result in judge_results.items():
            if isinstance(result, dict) and 'score' in result:
                print(f"  {metric.replace('judge_', '').title()}: {result['score']}/10")
                print(f"    Reasoning: {result['reasoning'][:100]}...")
        
        return judge_results
    
    async def _run_llm_judge_evaluation(
        self, question: str, answer: str, contexts: List[str]
    ) -> Dict[str, Any]:
        """Run LLM-as-Judge evaluation"""
        
        # Prepare context for judge
        context_text = "\n\n".join(contexts[:3])  # Use top 3 contexts
        
        # Run all judge evaluations concurrently
        correctness_task = self._judge_correctness(question, answer, context_text)
        compliance_task = self._judge_apra_compliance(question, answer, context_text)
        helpfulness_task = self._judge_helpfulness(question, answer, context_text)
        context_relevance_task = self._judge_context_relevance(question, answer, context_text)
        
        results = await asyncio.gather(
            correctness_task,
            compliance_task,
            helpfulness_task,
            context_relevance_task
        )
        
        return {
            "judge_correctness": results[0],
            "judge_apra_compliance": results[1], 
            "judge_helpfulness": results[2],
            "judge_context_relevance": results[3]
        }
    
    async def _judge_correctness(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """Judge factual correctness"""
        
        prompt = f"""Rate the factual correctness of this APRA response on a scale of 0-10.

Question: {question}
Answer: {answer}
Retrieved Context: {context}

Evaluation Criteria:
- Are APRA facts and regulations stated accurately?
- Are regulatory requirements correctly described?
- Are there any factual errors or misstatements?
- Does the answer align with official APRA guidance?

Respond with a JSON object containing:
- "score": integer from 0-10
- "reasoning": brief explanation of the score

JSON Response:"""

        try:
            response = await self.judge_llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('{') and content.endswith('}'):
                result = json.loads(content)
            else:
                # If not JSON, try to find JSON in the response
                import re
                json_match = re.search(r'\{[^}]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: parse score manually
                    score_match = re.search(r'score["\']?\s*:\s*(\d+)', content)
                    score = int(score_match.group(1)) if score_match else 5
                    return {"score": score, "reasoning": "Could not parse full response"}
            
            return {"score": result["score"], "reasoning": result["reasoning"]}
        except Exception as e:
            return {"score": 5, "reasoning": f"Evaluation error: {str(e)}"}
    
    async def _judge_apra_compliance(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """Judge APRA regulatory compliance"""
        
        prompt = f"""Rate how well this response aligns with APRA regulatory guidance on a scale of 0-10.

Question: {question}
Answer: {answer}
Retrieved Context: {context}

Evaluation Criteria:
- Does the response reflect current APRA standards and practices?
- Are regulatory nuances and requirements properly conveyed?
- Is the tone appropriate for professional regulatory guidance?
- Would this response help with APRA compliance understanding?

Respond with a JSON object containing:
- "score": integer from 0-10  
- "reasoning": brief explanation of the score

JSON Response:"""

        try:
            response = await self.judge_llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('{') and content.endswith('}'):
                result = json.loads(content)
            else:
                # If not JSON, try to find JSON in the response
                import re
                json_match = re.search(r'\{[^}]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: parse score manually
                    score_match = re.search(r'score["\']?\s*:\s*(\d+)', content)
                    score = int(score_match.group(1)) if score_match else 5
                    return {"score": score, "reasoning": "Could not parse full response"}
            
            return {"score": result["score"], "reasoning": result["reasoning"]}
        except Exception as e:
            return {"score": 5, "reasoning": f"Evaluation error: {str(e)}"}
    
    async def _judge_helpfulness(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """Judge helpfulness for financial services professionals"""
        
        prompt = f"""Rate how helpful this response is for financial services professionals on a scale of 0-10.

Question: {question}
Answer: {answer}

Evaluation Criteria:
- Does it directly and clearly answer the user's question?
- Is the information actionable and practical?
- Would this help someone understand and implement APRA requirements?
- Is the response clear and well-structured?

Respond with a JSON object containing:
- "score": integer from 0-10
- "reasoning": brief explanation of the score

JSON Response:"""

        try:
            response = await self.judge_llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('{') and content.endswith('}'):
                result = json.loads(content)
            else:
                # If not JSON, try to find JSON in the response
                import re
                json_match = re.search(r'\{[^}]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: parse score manually
                    score_match = re.search(r'score["\']?\s*:\s*(\d+)', content)
                    score = int(score_match.group(1)) if score_match else 5
                    return {"score": score, "reasoning": "Could not parse full response"}
            
            return {"score": result["score"], "reasoning": result["reasoning"]}
        except Exception as e:
            return {"score": 5, "reasoning": f"Evaluation error: {str(e)}"}
    
    async def _judge_context_relevance(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """Judge relevance of retrieved context"""
        
        prompt = f"""Rate how well the retrieved context supports answering the question on a scale of 0-10.

Question: {question}
Answer: {answer}
Retrieved Context: {context}

Evaluation Criteria:
- Is the retrieved context directly relevant to the question?
- Does the answer properly utilize the provided context?
- Are there important context pieces that seem to be missing?
- Is the context sufficient to generate a good answer?

Respond with a JSON object containing:
- "score": integer from 0-10
- "reasoning": brief explanation of the score

JSON Response:"""

        try:
            response = await self.judge_llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('{') and content.endswith('}'):
                result = json.loads(content)
            else:
                # If not JSON, try to find JSON in the response
                import re
                json_match = re.search(r'\{[^}]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: parse score manually
                    score_match = re.search(r'score["\']?\s*:\s*(\d+)', content)
                    score = int(score_match.group(1)) if score_match else 5
                    return {"score": score, "reasoning": "Could not parse full response"}
            
            return {"score": result["score"], "reasoning": result["reasoning"]}
        except Exception as e:
            return {"score": 5, "reasoning": f"Evaluation error: {str(e)}"}

# Global evaluator instance
evaluator = SimpleAPRAEvaluator()

async def evaluate_conversation_async(
    question: str,
    answer: str,
    contexts: List[str],
    trace_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async function to evaluate a conversation
    """
    return await evaluator.evaluate_conversation(
        question=question,
        answer=answer,
        contexts=contexts,
        trace_id=trace_id,
        user_id=user_id
    )

def evaluate_conversation_background(
    question: str,
    answer: str,
    contexts: List[str],
    trace_id: str,
    user_id: Optional[str] = None
):
    """
    Run evaluation in background without blocking main thread
    """
    asyncio.create_task(
        evaluate_conversation_async(question, answer, contexts, trace_id, user_id)
    )