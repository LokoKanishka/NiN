import asyncio
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)

async def test_mcp():
    print("Iniciando MCP Client...")
    server_parameters = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
    )
    
    try:
        async with stdio_client(server_parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Obtener herramientas
                tools_response = await session.list_tools()
                print("Herramientas disponibles:")
                for tool in tools_response.tools:
                    print(f" - {tool.name}: {tool.description}")
                    
                # Probar la herramienta de pensamiento
                args = {
                    "thought": "This is a test thought. I am testing the sequence.",
                    "thoughtNumber": 1,
                    "totalThoughts": 2,
                    "nextThoughtNeeded": True
                }
                print(f"Llamando a sequentialthinking con {args}")
                
                result = await session.call_tool("sequentialthinking", arguments=args)
                print("Resultado:")
                if result.content:
                    print(result.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp())
