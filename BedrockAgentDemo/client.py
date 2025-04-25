"""
Core client implementation for interacting with the Model Context Protocol server.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack
from jsonschema import validate, ValidationError

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import boto3

from config import Config
from models import Message, Tool, Conversation


class MCPClient:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("mcp_client.client")
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=config.aws_region
        )
        self.available_tools: List[Tool] = []
        # Add conversation context to maintain throughout the session
        self.conversation = Conversation(messages=[])

    async def connect(self):
        server_script_path = self.config.server_script_path
        
        if not server_script_path.endswith(('.py', '.js')):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if server_script_path.endswith('.py') else "node"
        server_params = StdioServerParameters(
            command=command, 
            args=[server_script_path], 
            env=None
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()
            await self._refresh_tools()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MCP server: {str(e)}") from e

    async def _refresh_tools(self):
        if not self.session:
            raise RuntimeError("Session not initialized")
        response = await self.session.list_tools()
        self.available_tools = [
            Tool(
                name=tool.name,
                description=tool.description,
                input_schema=tool.inputSchema
            ) for tool in response.tools
        ]
        self.logger.info(f"Available tools: {[tool.name for tool in self.available_tools]}")

    async def shutdown(self):
        self.logger.info("Closing connection and cleaning up resources")
        await self.exit_stack.aclose()

    async def run_interactive_chat(self):
        self.logger.info("Starting interactive chat")
        print("\nMCP Client Started!\nType your queries or 'quit' to exit.")
        
        # Initialize conversation at the start of the session
        self.conversation = Conversation(messages=[])
        
        # Display greeting when user first connects
        greeting = await self._get_welcome_message()
        print(f"\n{greeting}")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() in ('quit', 'exit'):
                    break
                if query.lower() == 'clear context':
                    self.conversation = Conversation(messages=[])
                    print("\nConversation context has been cleared.")
                    # Display greeting again after clearing context
                    greeting = await self._get_welcome_message()
                    print(f"\n{greeting}")
                    continue
                response = await self.process_query(query)
                print("\n" + response)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt detected")
                break
            except Exception as e:
                self.logger.exception(f"Error processing query: {str(e)}")
                print(f"\nError: {str(e)}")

    async def _get_welcome_message(self) -> str:
        """Generate a welcome message for the user when they first connect."""
        try:
            welcome_query = "system: User has connected. Greet user as a power corporation call centre representative in India."
            self.conversation.add_user(welcome_query)
            bedrock_tools = Message.to_bedrock_format(self.available_tools)
            response = await self._call_bedrock_model(self.conversation.to_list(), bedrock_tools)
            
            if 'output' in response and 'message' in response['output']:
                assistant_message = response['output']['message']
                self.conversation.add_assistant_response(assistant_message['content'])
                welcome_text = self._extract_text(assistant_message['content'])
                return welcome_text
        except Exception as e:
            self.logger.warning(f"Failed to generate welcome message: {str(e)}")
            # Fall back to a default greeting if model call fails
            return "Welcome! I'm your customer service representative from the power corporation. How may I assist you today with your power outage or billing inquiries?"
    
    async def process_query(self, query: str) -> str:
        # Use the existing conversation context instead of creating a new one
        self.conversation.add_user(query)
        bedrock_tools = Message.to_bedrock_format(self.available_tools)
        self.logger.debug(f"Sending query to model with conversation context: {len(self.conversation.messages)} messages")
        response = await self._call_bedrock_model(self.conversation.to_list(), bedrock_tools)

        if response.get('stopReason') == 'tool_use':
            return await self._handle_tool_use(response, bedrock_tools)

        if 'output' in response and 'message' in response['output']:
            assistant_message = response['output']['message']
            # Add assistant's response to the conversation context
            self.conversation.add_assistant_response(assistant_message['content'])
            return self._extract_text(assistant_message['content'])

        return "No response generated."

    async def _handle_tool_use(self, initial_response: Dict, bedrock_tools: List[Dict]) -> str:
        self.logger.info("Model requested tool use")

        tool_uses = [item['toolUse'] for item in initial_response['output']['message']['content'] if 'toolUse' in item]
        self.logger.info(f"Number of tools requested: {len(tool_uses)}")

        # Add tool use to conversation context
        self.conversation.add_tool_use(tool_uses)

        tool_results = await self._execute_tools(tool_uses)
        
        # Add tool results to conversation context
        self.conversation.add_tool_results(tool_results)

        self.logger.debug(f"Sending tool results to model: {json.dumps(tool_results)}")
        final_response = await self._call_bedrock_model(self.conversation.to_list(), bedrock_tools)

        if final_response.get('stopReason') == 'tool_use':
            self.logger.info("Model requested additional tools after first round")
            return await self._handle_tool_use(final_response, bedrock_tools)

        if 'output' in final_response and 'message' in final_response['output']:
            assistant_message = final_response['output']['message']
            # Add final assistant response to conversation context
            self.conversation.add_assistant_response(assistant_message['content'])
            text = self._extract_text(assistant_message['content'])
            if text:
                return text

        combined_results = ""
        for result in tool_results:
            if 'toolResult' in result and 'content' in result['toolResult']:
                for item in result['toolResult']['content']:
                    if 'text' in item:
                        combined_results += item['text'] + "\n\n"
        return combined_results.strip() if combined_results else "No response generated after tool use."

    async def _execute_tools(self, tool_uses: List[Dict]) -> List[Dict]:
        tool_results = []

        for tool_use in tool_uses:
            tool_name = tool_use['name']
            tool_args = tool_use['input']
            tool_use_id = tool_use['toolUseId']

            tool = next((t for t in self.available_tools if t.name == tool_name), None)
            if not tool:
                error_msg = f"Tool '{tool_name}' is not available."
                self.logger.warning(error_msg)
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": error_msg}]
                    }
                })
                continue

            validation_error = self._validate_tool_input(tool.input_schema, tool_args)
            if validation_error:
                self.logger.warning(f"Invalid input for tool '{tool_name}': {validation_error}")
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": f"⚠️ Invalid input: {validation_error}"}]
                    }
                })
                continue

            try:
                self.logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                result = await self.session.call_tool(tool_name, tool_args)
                result_text = self._extract_text_from_tool_result(result)
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": result_text}]
                    }
                })
            except Exception as e:
                self.logger.warning(f"Tool '{tool_name}' failed: {str(e)}", exc_info=True)
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": f"⚠️ Tool '{tool_name}' failed: {str(e)}"}]
                    }
                })

        return tool_results

    def _validate_tool_input(self, schema: Dict[str, Any], input_data: Dict[str, Any]) -> Optional[str]:
        try:
            validate(instance=input_data, schema={
                "type": "object",
                "properties": schema["properties"],
                "required": schema["required"]
            })
            return None
        except ValidationError as e:
            return str(e)

    def _extract_text_from_tool_result(self, result) -> str:
        result_text = ""
        for content_item in result.content:
            if isinstance(content_item, dict):
                result_text += content_item.get("text", "") + " "
            elif hasattr(content_item, "text"):
                result_text += content_item.text + " "
        return result_text.strip()

    def _extract_text(self, content_list: List[Dict[str, Any]]) -> str:
        result = ""
        for item in content_list:
            if isinstance(item, dict) and "text" in item:
                result += item["text"] + " "
        return result.strip()

    async def _call_bedrock_model(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        return await asyncio.to_thread(
            self.bedrock.converse,
            modelId=self.config.model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": self.config.max_tokens, 
                "temperature": self.config.temperature
            },
            toolConfig={"toolChoice": {"auto": {}}, "tools": tools},
            system=[{"text": self.config.system_prompt}],
        )