from app.security import validate_input, validate_output, validate_json_output
from app.cache import test_redis_semantic_cache
from app.agent import ProductionAgent
import asyncio
# Assuming validate_input is defined or imported in this file

# async def main():
    # Now you can use 'await' safely inside an async function!
    # result = await validate_input("fuck you bitch!")
    
    # print(f"Status: {result.status}")
    # print(f"Data: {result.data}")
    # print(f"Warnings: {result.warnings}")
    # print(f"Errors: {result.errors}")


agent  = ProductionAgent()
queries = [
    "what is langGraph?",
    "what is langchain?",
    "what is langsmith?",
]

    
if __name__ == "__main__":
    # This initializes the event loop and runs your async main block
    # asyncio.run(main())
    # test_redis_semantic_cache()
    for q in queries:
        response = agent.invoke(q)
        print(f"Query: {q}\nResponse: {response}\n{'-'*50}")