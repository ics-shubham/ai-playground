"""
Data models for the MCP client application.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class Message:
    role: str
    content: List[Dict[str, Any]]

    @staticmethod
    def to_bedrock_format(tools: List['Tool']) -> List[Dict]:
        return [{
            "toolSpec": {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": tool.input_schema["properties"],
                        "required": tool.input_schema["required"]
                    }
                }
            }
        } for tool in tools]


@dataclass
class Conversation:
    messages: List[Message]

    def add_user(self, text: str):
        self.messages.append(Message(role="user", content=[{"text": text}]))

    def add_tool_use(self, tool_uses: List[Dict]):
        self.messages.append(Message(role="assistant", content=[{"toolUse": t} for t in tool_uses]))

    def add_tool_results(self, results: List[Dict]):
        self.messages.append(Message(role="user", content=results))
        
    def add_assistant_response(self, content: List[Dict]):
        """Add a regular assistant response to the conversation history."""
        self.messages.append(Message(role="assistant", content=content))

    def to_list(self) -> List[Dict]:
        return [msg.__dict__ for msg in self.messages]