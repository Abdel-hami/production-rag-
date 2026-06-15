from app.security import validate_input, validate_output, validate_json_output


import asyncio
# Assuming validate_input is defined or imported in this file

async def main():
    # Now you can use 'await' safely inside an async function!
    result = await validate_input("fuck you bitch!")
    
    print(f"Status: {result.status}")
    print(f"Data: {result.data}")
    print(f"Warnings: {result.warnings}")
    print(f"Errors: {result.errors}")

if __name__ == "__main__":
    # This initializes the event loop and runs your async main block
    asyncio.run(main())