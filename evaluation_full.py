import os
import asyncio
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Evaluation imports with error handling
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
    print("✅ RAGAS library loaded successfully")
except ImportError as e:
    print(f"⚠️ RAGAS not available: {e}")
    RAGAS_AVAILABLE = False

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
    print("✅ Langfuse library loaded successfully")
except ImportError as e:
    print(f"⚠️ Langfuse not available: {e}")
    LANGFUSE_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain.schema import Document
import json

# Initialize Langfuse client if available
if LANGFUSE_AVAILABLE:
    try:
        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        print("✅ Langfuse client initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize Langfuse: {e}")
        langfuse = None
        LANGFUSE_AVAILABLE = False
else:
    langfuse = None

# Judge LLM (separate from chat LLM for evaluation)
judge_llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.1,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

class ComprehensiveAPRAEvaluator:
    """Comprehensive APRA-specific evaluation system using both RAGAS and LLM-as-Judge"""
    
    def __init__(self):
        self.judge_llm = judge_llm
        self.langfuse = langfuse
    
    async def evaluate_conversation(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        trace_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single conversation using both RAGAS and LLM-as-Judge
        """
        
        print(f"🔍 Evaluating conversation: {trace_id}")
        
        # Create Langfuse trace if available
        trace = None
        if LANGFUSE_AVAILABLE and langfuse:
            try:
                # Use the correct Langfuse API
                trace = langfuse.start_span(
                    name="apra_conversation_evaluation",
                    input={"question": question},
                    output={"answer": answer},
                    metadata={
                        "contexts_count": len(contexts),
                        "original_trace_id": trace_id,
                        "user_id": user_id
                    }
                )
                print(f"📊 Langfuse span created: {trace.trace_id}")
            except Exception as e:
                print(f"⚠️ Could not create Langfuse trace: {e}")
                trace = None
        
        # Run evaluations concurrently
        ragas_results, judge_results = await asyncio.gather(
            self._run_ragas_evaluation(question, answer, contexts),
            self._run_llm_judge_evaluation(question, answer, contexts)
        )
        
        # Combine results
        all_results = {**ragas_results, **judge_results}
        
        # Print results for visibility
        print(f"📈 Evaluation Results for {trace_id}:")
        for metric, result in all_results.items():
            if metric.startswith("ragas_"):
                print(f"  🤖 {metric.replace('ragas_', '').title()}: {result:.3f}")
            elif isinstance(result, dict) and 'score' in result:
                print(f"  ⚖️ {metric.replace('judge_', '').title()}: {result['score']}/10")
                print(f"    💭 {result['reasoning'][:100]}...")
        
        # Send scores to Langfuse
        await self._send_scores_to_langfuse(trace, all_results)
        
        return all_results
    
    async def _run_ragas_evaluation(
        self, question: str, answer: str, contexts: List[str]
    ) -> Dict[str, float]:
        """Run RAGAS evaluation metrics"""
        
        if not RAGAS_AVAILABLE:
            print("⚠️ RAGAS not available, skipping RAGAS evaluation")
            return {
                "ragas_faithfulness": 0.0,
                "ragas_answer_relevancy": 0.0,
                "ragas_context_precision": 0.0,
                "ragas_context_recall": 0.0
            }
        
        print("🤖 Running RAGAS evaluation...")
        
        # Create dataset for RAGAS
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
            "ground_truth": [answer]  # Using answer as ground truth for reference-free eval
        }
        
        dataset = Dataset.from_dict(data)
        
        try:
            # Run RAGAS evaluation
            result = evaluate(
                dataset=dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall
                ],
                llm=judge_llm,
                embeddings=None  # Let RAGAS use default embeddings
            )
            
            # Extract scores - handle both single values and lists
            ragas_scores = {}
            for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                score_value = result[metric]
                if isinstance(score_value, list):
                    # Take the first item if it's a list
                    score_value = score_value[0] if len(score_value) > 0 else 0.0
                ragas_scores[f"ragas_{metric}"] = float(score_value)
            
            print("✅ RAGAS evaluation completed")
            return ragas_scores
            
        except Exception as e:
            print(f"❌ RAGAS evaluation error: {e}")
            return {
                "ragas_faithfulness": 0.0,
                "ragas_answer_relevancy": 0.0,
                "ragas_context_precision": 0.0,
                "ragas_context_recall": 0.0
            }
    
    async def _run_llm_judge_evaluation(
        self, question: str, answer: str, contexts: List[str]
    ) -> Dict[str, Any]:
        """Run LLM-as-Judge evaluation"""
        
        print("⚖️ Running LLM Judge evaluation...")
        
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
        
        print("✅ LLM Judge evaluation completed")
        
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

        return await self._get_judge_response(prompt)
    
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

        return await self._get_judge_response(prompt)
    
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

        return await self._get_judge_response(prompt)
    
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

        return await self._get_judge_response(prompt)
    
    async def _get_judge_response(self, prompt: str) -> Dict[str, Any]:
        """Get and parse response from judge LLM"""
        
        try:
            response = await self.judge_llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('{') and content.endswith('}'):
                result = json.loads(content)
            else:
                # If not JSON, try to find JSON in the response
                json_match = re.search(r'\{[^}]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: parse score manually
                    score_match = re.search(r'score["\']?\s*:\s*(\d+)', content)
                    score = int(score_match.group(1)) if score_match else 5
                    return {"score": score, "reasoning": "Could not parse full response"}
            
            # Ensure we have required fields
            if not isinstance(result.get("score"), int) or not isinstance(result.get("reasoning"), str):
                return {"score": 5, "reasoning": "Invalid response format"}
            
            return {"score": result["score"], "reasoning": result["reasoning"]}
        except Exception as e:
            return {"score": 5, "reasoning": f"Evaluation error: {str(e)}"}
    
    async def _send_scores_to_langfuse(self, trace, results: Dict[str, Any]):
        """Send all evaluation scores to Langfuse"""
        
        if not LANGFUSE_AVAILABLE or not langfuse or not trace:
            print("⚠️ Langfuse not available, skipping score upload")
            return
        
        try:
            # RAGAS scores
            for metric, score in results.items():
                if metric.startswith("ragas_"):
                    trace.score(
                        name=metric,
                        value=score,
                        comment=f"RAGAS metric: {metric.replace('ragas_', '')}"
                    )
            
            # LLM Judge scores
            for metric, result in results.items():
                if metric.startswith("judge_"):
                    if isinstance(result, dict) and "score" in result:
                        trace.score(
                            name=metric,
                            value=result["score"] / 10.0,  # Normalize to 0-1 for consistency
                            comment=f"Judge reasoning: {result['reasoning'][:200]}..."
                        )
            
            # End the trace to ensure it's uploaded
            trace.end()
            
            print("📊 Scores sent to Langfuse successfully")
        except Exception as e:
            print(f"⚠️ Failed to send scores to Langfuse: {e}")

# Global evaluator instance
evaluator = ComprehensiveAPRAEvaluator()

async def evaluate_conversation_async(
    question: str,
    answer: str,
    contexts: List[str],
    trace_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async function to evaluate a conversation
    This will be called from the main app without blocking the response
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