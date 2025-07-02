# Copyright (c) Mehmet Bektas <mbektasgh@outlook.com>

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import threading
from typing import Any, Union
import anyio
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.client.stdio import get_default_environment as mcp_get_default_environment
from mcp.types import CallToolResult, TextContent, ImageContent
from notebook_intelligence.api import ChatCommand, ChatRequest, ChatResponse, HTMLFrameData, ImageData, MCPServer, MarkdownData, ProgressData, Tool, ToolPreInvokeResponse
from notebook_intelligence.base_chat_participant import BaseChatParticipant
import logging
from contextlib import AsyncExitStack

log = logging.getLogger(__name__)

MCP_ICON_SRC = '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'
MCP_ICON_URL = f"data:image/png;base64,{MCP_ICON_SRC}"
MCP_TOOL_TIMEOUT = 60


class MCPTool(Tool):
    def __init__(self, server: 'MCPServer', name, description, schema, auto_approve=False):
        super().__init__()
        self._server = server
        self._name = name
        self._description = description
        self._schema = schema
        self._auto_approve = auto_approve

    @property
    def name(self) -> str:
        return self._name

    @property
    def title(self) -> str:
        return self._name
    
    @property
    def tags(self) -> list[str]:
        return ["mcp-tool"]
    
    @property
    def description(self) -> str:
        return self._description

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self._name,
                "description": self._description,
                "strict": False,
                "parameters": self._schema
            },
        }
    
    def pre_invoke(self, request: ChatRequest, tool_args: dict) -> Union[ToolPreInvokeResponse, None]:
        confirmationTitle = None
        confirmationMessage = None
        if not self._auto_approve:
            confirmationTitle = "Approve"
            confirmationMessage = "Are you sure you want to call this MCP tool?"
        return ToolPreInvokeResponse(f"Calling MCP tool '{self.name}'", confirmationTitle, confirmationMessage)

    async def handle_tool_call(self, request: ChatRequest, response: ChatResponse, tool_context: dict, tool_args: dict) -> str:
        call_args = {}

        for key in self._schema['properties']:
            if key in tool_args:
                call_args[key] = tool_args.get(key)

        try:
            result = await self._server.call_tool(self.name, call_args)
            if type(result) is CallToolResult:
                if len(result.content) > 0:
                    text_contents = []
                    for content in result.content:
                        if type(content) is ImageContent:
                            response.stream(ImageData(f"data:{content.mimeType};base64,{content.data}"))
                        elif type(content) is TextContent:
                            text_contents.append(content.text)

                    if len(text_contents) > 0:
                        return "\n".join(text_contents)
                    else:
                        return "success"
            elif type(result) is dict:
                return result
            else:
                return f"Error! Invalid tool result: {result}"
        except Exception as e:
            return f"Error occurred while calling MCP tool: {str(e)}"

@dataclass
class SSEServerParameters:
    url: str
    headers: dict[str, Any] | None = None

class MCPServerImpl(MCPServer):
    def __init__(self, name: str, stdio_params: StdioServerParameters = None, sse_params: SSEServerParameters = None, auto_approve_tools: list[str] = []):
        self._name: str = name
        self._stdio_params: StdioServerParameters = stdio_params
        self._sse_params: SSEServerParameters = sse_params
        self._auto_approve_tools: set[str] = set(auto_approve_tools)
        self._tried_to_get_tool_list = False
        self._mcp_tools = []
        self._session = None

    @property
    def name(self) -> str:
        return self._name
    
    async def connect(self):
        try:
            log.info(f"Connecting to MCP server '{self.name}'...")
            if self._session is not None:
                log.info(f"Session already exists for server '{self.name}', skipping connection")
                return

            log.info(f"Creating new session for server '{self.name}'...")
            self.exit_stack = AsyncExitStack()
            
            if self._stdio_params is not None:
                log.info(f"Using STDIO transport for server '{self.name}': {self._stdio_params.command} {self._stdio_params.args}")
                self._transport = await self.exit_stack.enter_async_context(stdio_client(self._stdio_params))
            elif self._sse_params is not None:
                log.info(f"Using SSE transport for server '{self.name}': {self._sse_params.url}")
                self._transport = await self.exit_stack.enter_async_context(sse_client(self._sse_params.url, self._sse_params.headers))
            else:
                raise Exception("No transport parameters provided")

            self._read_stream, self._write_stream = self._transport
            log.info(f"Transport established for server '{self.name}', creating session...")
            self._session = await self.exit_stack.enter_async_context(ClientSession(self._read_stream, self._write_stream, timedelta(seconds=MCP_TOOL_TIMEOUT)))
            
            log.info(f"Initializing session for server '{self.name}'...")
            await self._session.initialize()
            
            if not self._tried_to_get_tool_list:
                log.info(f"Updating tool list for server '{self.name}'...")
                await self._update_tool_list()
                self._tried_to_get_tool_list = True
                log.info(f"Tool list updated for server '{self.name}', found {len(self._mcp_tools)} tools")
            
            log.info(f"Successfully connected to MCP server '{self.name}'")
        except Exception as e:
            log.error(f"Error connecting to MCP server '{self.name}': {e}")
            import traceback
            log.error(f"Connection error traceback: {traceback.format_exc()}")
            self._session = None
            self.exit_stack = None
            raise e

    async def disconnect(self):
        try:
            log.info(f"Disconnecting from MCP server '{self.name}'...")
            if self._session is None:
                log.info(f"Session is None for server '{self.name}', nothing to disconnect")
                return

            log.info(f"Closing exit stack for server '{self.name}'...")
            await self.exit_stack.aclose()
            log.info(f"Exit stack closed for server '{self.name}'")
            
            self.exit_stack = None
            self._session = None
            log.info(f"Successfully disconnected from MCP server '{self.name}'")
        except Exception as e:
            log.error(f"Error disconnecting from MCP server '{self.name}': {e}")
            import traceback
            log.error(f"Disconnect error traceback: {traceback.format_exc()}")
            # Force cleanup even if there's an error
            self.exit_stack = None
            self._session = None

    async def _update_tool_list(self):
        if self._session is None:
            await self.connect()

        response = await self._session.list_tools()
        self._mcp_tools = response.tools

    async def call_tool(self, tool_name: str, tool_args: dict):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                log.info(f"Attempting to call tool '{tool_name}' on server '{self.name}' with args: {tool_args} (attempt {attempt + 1}/{max_retries})")
                if self._session is None:
                    log.info(f"Session is None for server '{self.name}', connecting...")
                    await self.connect()

                log.info(f"Calling tool '{tool_name}' on server '{self.name}'...")
                result = await self._session.call_tool(tool_name, tool_args)
                log.info(f"Tool '{tool_name}' on server '{self.name}' returned: {type(result)} with length {len(str(result)) if result else 0}")
                return result
            except Exception as e:
                error_type = type(e).__name__
                log.error(f"Error calling tool '{tool_name}' on server '{self.name}': {e}")
                log.error(f"Error type: {error_type}")
                log.error(f"Tool args were: {tool_args}")
                
                # Handle ClosedResourceError with automatic reconnection
                if error_type == "ClosedResourceError" and attempt < max_retries - 1:
                    log.warning(f"ClosedResourceError detected for server '{self.name}', attempting reconnection...")
                    try:
                        # Force disconnect and reconnect
                        await self.force_disconnect()
                        await self.connect()
                        log.info(f"Successfully reconnected to server '{self.name}'")
                        continue  # Retry the tool call
                    except Exception as reconnect_error:
                        log.error(f"Failed to reconnect to server '{self.name}': {reconnect_error}")
                
                # Log full traceback on final attempt or non-recoverable errors
                if attempt == max_retries - 1:
                    import traceback
                    log.error(f"Final attempt failed. Full traceback: {traceback.format_exc()}")
                
                # If this was the last attempt, return None
                if attempt == max_retries - 1:
                    return None
        
        return None

    async def force_disconnect(self):
        """Forcefully disconnect without trying to close already-closed resources"""
        log.info(f"Force disconnecting from MCP server '{self.name}' (bypassing close operations)...")
        # Don't try to close the exit_stack since resources are already closed
        # Just reset the state
        self.exit_stack = None
        self._session = None
        log.info(f"Force disconnected from MCP server '{self.name}'")

    # TODO: optimize this
    def get_tools(self) -> list[Tool]:
        return [MCPTool(self, tool.name, tool.description, tool.inputSchema, auto_approve=(tool.name in self._auto_approve_tools)) for tool in self._mcp_tools]

    def get_tool(self, tool_name: str) -> Tool:
        for tool in self.get_tools():
            if tool.name == tool_name:
                return tool
        return None

class MCPChatParticipant(BaseChatParticipant):
    def __init__(self, id: str, name: str, servers: list[MCPServer], nbi_tools: list[str] = []):
        super().__init__()
        self._id = id
        self._name = name
        self._servers = servers
        self._tools_updated = False
        self._nbi_tools = nbi_tools

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._name
    
    @property
    def icon_path(self) -> str:
        return MCP_ICON_URL

    @property
    def commands(self) -> list[ChatCommand]:
        return []

    @property
    def tools(self) -> list[Tool]:
        mcp_tools = []
        for mcp_server in self._servers:
            mcp_tools += mcp_server.get_tools()
        for nbi_tool in self._nbi_tools:
            tool = BaseChatParticipant.get_tool_by_name(nbi_tool)
            if tool is not None:
                mcp_tools.append(tool)
        return mcp_tools
    
    @property
    def servers(self) -> list[MCPServer]:
        return self._servers
    
    async def handle_chat_request(self, request: ChatRequest, response: ChatResponse, options: dict = {}) -> None:
        log.info(f"MCP Chat Participant '{self.name}' handling chat request: {request.command}")
        response.stream(ProgressData("Thinking..."))

        # Force disconnect all servers to ensure fresh connections
        log.info(f"Ensuring fresh connections by disconnecting {len(self._servers)} MCP servers...")
        for server in self._servers:
            try:
                await server.force_disconnect()
                log.info(f"Force disconnected server '{server.name}' for fresh connection")
            except Exception as e:
                log.error(f"Error during force disconnect of server '{server.name}': {e}")

        # Connect to all servers
        log.info(f"Connecting to {len(self._servers)} MCP servers...")
        for server in self._servers:
            try:
                await server.connect()
                log.info(f"Successfully connected to server '{server.name}'")
            except Exception as e:
                log.error(f"Failed to connect to server '{server.name}': {e}")

        if request.command == "info":
            log.info(f"Processing info command for {len(self._servers)} servers")
            for server in self._servers:
                info_lines = []
                info_lines.append(f"- **{server.name}** server tools:")
                for tool in server.get_tools():
                    info_lines.append(f"  - **{tool.name}**: {tool.description}\n")
                response.stream(MarkdownData(f"\n".join(info_lines)))

            response.finish()
        else:
            log.info(f"Processing chat request with tools for command: {request.command}")
            await self.handle_chat_request_with_tools(request, response, options)

        # Disconnect from all servers
        log.info(f"Disconnecting from {len(self._servers)} MCP servers...")
        for server in self._servers:
            try:
                await server.disconnect()
                log.info(f"Successfully disconnected from server '{server.name}'")
            except Exception as e:
                log.error(f"Failed to disconnect from server '{server.name}': {e}")
        
        log.info(f"MCP Chat Participant '{self.name}' finished handling chat request")

class MCPManager:
    def __init__(self, mcp_config: dict):
        # TODO: dont reuse servers, recreate with same config
        servers_config = mcp_config.get("mcpServers", {})
        participants_config = mcp_config.get("participants", {})
        self._mcp_participants: list[MCPChatParticipant] = []
        self._mcp_servers: list[MCPServer] = []

        # parse MCP participants
        for participant_id in participants_config:
            participant_config = participants_config[participant_id]
            participant_name = participant_config.get("name", participant_id)
            if participant_name == "mcp":
                continue
            server_names = participant_config.get("servers", [])
            nbi_tools = participant_config.get("nbiTools", [])
            participant_servers = self.create_servers(server_names, servers_config)

            if len(participant_servers) > 0:
                self._mcp_participants.append(MCPChatParticipant(f"mcp-{participant_id}", participant_name, participant_servers, nbi_tools))
                self._mcp_servers += participant_servers

        enabled_server_names = [server_name for server_name in servers_config.keys() if servers_config.get(server_name, {}).get("disabled", False) == False]
        unused_server_names = set(enabled_server_names)

        for participant in self._mcp_participants:
            for server in participant.servers:
                if server.name in unused_server_names:
                    unused_server_names.remove(server.name)

        if len(unused_server_names) > 0:
            unused_servers = self.create_servers(unused_server_names, servers_config)
            mcp_participant_config = participants_config.get("mcp", {})
            nbi_tools = mcp_participant_config.get("nbiTools", [])
            self._mcp_participants.append(MCPChatParticipant("mcp", "MCP", unused_servers, nbi_tools))
            self._mcp_servers += unused_servers

        thread = threading.Thread(target=self.init_tool_lists, args=())
        thread.start()

    def create_servers(self, server_names: list[str], servers_config: dict):
        servers = []
        for server_name in server_names:
            server_config = servers_config.get(server_name, None)
            if server_config is None:
                log.error(f"Server '{server_name}' not found in MCP servers configuration")
                continue

            if server_config.get("disabled", False) == True:
                log.info(f"MCP Server '{server_name}' is disabled in MCP servers configuration. Skipping it.")
                continue

            mcp_server = self.create_mcp_server(server_name, server_config)
            if mcp_server is None:
                log.error(f"Failed to create MCP server '{server_name}'")
                continue

            servers.append(mcp_server)

        return servers
    
    def create_mcp_server(self, server_name: str, server_config: dict):
        auto_approve_tools = server_config.get("autoApprove", [])

        if "command" in server_config:
            command = server_config["command"]
            args = server_config.get("args", [])
            env = server_config.get("env", None)
            server_env = None
            if env is not None:
                server_env = mcp_get_default_environment()
                server_env.update(env)

            return MCPServerImpl(server_name, stdio_params=StdioServerParameters(
                command = command,
                args = args,
                env = server_env
                ), auto_approve_tools = auto_approve_tools)
        elif "url" in server_config:
            server_url = server_config["url"]
            headers = server_config.get("headers", None)

            return MCPServerImpl(server_name, sse_params=SSEServerParameters(url=server_url, headers=headers), auto_approve_tools=auto_approve_tools)

        log.error(f"Invalid MCP server configuration for: {server_name}")
        return None

    def get_mcp_participants(self):
        return self._mcp_participants

    async def init_tool_lists_async(self):
        for server in self._mcp_servers:
            try:
                await server.connect()
                await server.disconnect()
            except Exception as e:
                log.error(f"Error initializing tool list for server {server.name}: {e}")
    
    def init_tool_lists(self):
        asyncio.run(self.init_tool_lists_async())

    def get_mcp_servers(self):
        return self._mcp_servers
    
    def get_mcp_server(self, server_name: str):
        for server in self._mcp_servers:
            if server.name == server_name:
                return server
        return None
