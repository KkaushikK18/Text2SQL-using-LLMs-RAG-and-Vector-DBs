import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sql_generation.chain import generate_and_validate_sql
from utils.logger import get_logger

logger = get_logger("Evaluator")

def evaluate_pipeline():
    logger.info("Starting pipeline evaluation...")
    
    test_questions = [
        "How many total customers do we have?",
        "What is the total revenue?",
        "List the top 5 most expensive products.",
        "Which supplier has the highest rating?"
    ]
    
    total_latency = 0
    success_count = 0
    
    for q in test_questions:
        start = time.time()
        sql = generate_and_validate_sql(q)
        latency = time.time() - start
        
        logger.info(f"Question: {q}")
        logger.info(f"Generated SQL: {sql}")
        logger.info(f"Latency: {latency:.2f} seconds\n")
        
        if sql:
            success_count += 1
            total_latency += latency
            
    avg_latency = total_latency / success_count if success_count else 0
    logger.info("="*50)
    logger.info("EVALUATION RESULTS")
    logger.info("="*50)
    logger.info(f"Success Rate:  {success_count}/{len(test_questions)} ({(success_count/len(test_questions))*100:.1f}%)")
    logger.info(f"Avg Latency:   {avg_latency:.2f} seconds")
    logger.info("="*50)

if __name__ == "__main__":
    evaluate_pipeline()
