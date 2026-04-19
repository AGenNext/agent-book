"""
Messaging Platform Integrations

Integrate the Open Notebook agent with:
- Slack
- WhatsApp (Twilio)
- Discord

Each platform has its own handler that normalizes messages
and routes them to the onboarding agent.
"""

import os
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

# Load env
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# Message Models
# =============================================================================


class Platform(Enum):
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    WEB = "web"


@dataclass
class InboundMessage:
    """Normalized inbound message."""
    platform: Platform
    user_id: str
    user_name: str
    text: str
    channel_id: str
    raw_data: dict = field(default_factory=dict)
    thread_id: Optional[str] = None


@dataclass
class OutboundMessage:
    """Normalized outbound message."""
    platform: Platform
    channel_id: str
    text: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    embeds: list[dict] = field(default_factory=list)
    components: list[dict] = field(default_factory=list)


# =============================================================================
# Platform Handlers
# =============================================================================


class PlatformHandler(ABC):
    """Base class for platform handlers."""

    @abstractmethod
    async def handle_inbound(self, payload: dict) -> Optional[InboundMessage]:
        """Convert platform-specific payload to normalized message."""
        pass

    @abstractmethod
    async def send_message(self, message: OutboundMessage) -> bool:
        """Send message to platform."""
        pass

    @abstractmethod
    def get_webhook_handler(self):
        """Return FastAPI route handler for platform webhooks."""
        pass


# =============================================================================
# Slack Handler
# =============================================================================


class SlackHandler(PlatformHandler):
    """Slack integration handler."""

    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.app_token = os.getenv("SLACK_APP_TOKEN")  # For socket mode

    async def handle_inbound(self, payload: dict) -> Optional[InboundMessage]:
        """Handle Slack events."""
        # URL verification challenge
        if payload.get("type") == "url_verification":
            return None

        # Handle event callback
        if payload.get("type") == "event_callback":
            event = payload.get("event", {})
            event_type = event.get("type")

            if event_type in ["message", "app_mention"]:
                user_id = event.get("user")
                text = event.get("text", "")
                channel_id = event.get("channel")
                thread_ts = event.get("thread_ts")

                # Skip bot messages
                if event.get("subtype") == "bot_message":
                    return None

                return InboundMessage(
                    platform=Platform.SLACK,
                    user_id=user_id or "unknown",
                    user_name=self._get_user_name(user_id) if user_id else "User",
                    text=self._clean_slack_text(text),
                    channel_id=channel_id,
                    thread_id=thread_ts,
                    raw_data=payload,
                )

        return None

    def _clean_slack_text(self, text: str) -> str:
        """Clean Slack-specific formatting."""
        # Remove user mentions <@U123>
        import re
        text = re.sub(r"<@[A-Z0-9]+>", "", text)
        # Remove channel mentions <#C123>
        text = re.sub(r"<#[A-Z0-9]+\|?[^>]*>", "", text)
        # Remove URLs
        text = re.sub(r"<[^|]+|[^>]+>", "", text)
        return text.strip()

    def _get_user_name(self, user_id: str) -> str:
        """Get user name from Slack."""
        # In production, cache this
        return f"user_{user_id}"

    async def send_message(self, message: OutboundMessage) -> bool:
        """Send message to Slack."""
        if not self.bot_token:
            logger.warning("SLACK_BOT_TOKEN not configured")
            return False

        import httpx

        async with httpx.AsyncClient() as client:
            # Prepare Slack block kit message
            payload = {
                "channel": message.channel_id,
                "text": message.text,
                "blocks": self._create_blocks(message),
            }

            if message.thread_id:
                payload["thread_ts"] = message.thread_id

            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            return resp.status_code == 200

    def _create_blocks(self, message: OutboundMessage) -> list:
        """Create Slack block kit blocks."""
        blocks = []

        # Add text content
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message.text,
            },
        })

        # Add quick actions if applicable
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📓 New Notebook"},
                    "action_id": "new_notebook",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔍 Search"},
                    "action_id": "search",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🎙️ Podcast"},
                    "action_id": "podcast",
                },
            ],
        })

        return blocks

    def get_webhook_handler(self):
        """Return FastAPI route for Slack webhooks."""
        from fastapi import APIRouter, Request, JSONResponse
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        router = APIRouter()

        @router.post("/webhooks/slack")
        async def slack_webhook(request: Request):
            payload = await request.json()
            
            # Handle URL verification
            if payload.get("type") == "url_verification":
                return JSONResponse({"challenge": payload.get("challenge")})

            # Handle events
            message = await self.handle_inbound(payload)
            if message:
                # Process message with agent
                from mcp.agent import OnboardingAgent
                agent = OnboardingAgent()
                result = await agent.run(message.text, thread_id=message.user_id)

                # Send response
                response_text = result.messages[-1].content if result.messages else "Got it!"
                await self.send_message(OutboundMessage(
                    platform=Platform.SLACK,
                    channel_id=message.channel_id,
                    text=response_text,
                    thread_id=message.thread_id,
                ))

            return JSONResponse({"status": "ok"})

        return router


# =============================================================================
# WhatsApp Handler (Twilio)
# =============================================================================


class WhatsAppHandler(PlatformHandler):
    """WhatsApp integration via Twilio."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        self.api_key = os.getenv("TWILIO_API_KEY")
        self.api_secret = os.getenv("TWILIO_API_SECRET")

    async def handle_inbound(self, payload: dict) -> Optional[InboundMessage]:
        """Handle incoming WhatsApp message."""
        # Twilio sends form data
        message_sid = payload.get("MessageSid")
        from_number = payload.get("From")
        body = payload.get("Body", "")
        profile_name = payload.get("ProfileName", "User")

        if not from_number or not body:
            return None

        # Extract WhatsApp number
        wa_id = from_number.replace("whatsapp:", "")

        return InboundMessage(
            platform=Platform.WHATSAPP,
            user_id=wa_id,
            user_name=profile_name,
            text=body.strip(),
            channel_id=wa_id,
            raw_data=payload,
        )

    async def send_message(self, message: OutboundMessage) -> bool:
        """Send WhatsApp message via Twilio."""
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured")
            return False

        import httpx

        async with httpx.AsyncClient() as client:
            # Build TwiML response
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message.text}</Message>
</Response>"""

            # Use Twilio Messages API
            resp = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                auth=(self.account_sid, self.auth_token),
                data={
                    "To": f"whatsapp:{message.channel_id}",
                    "From": f"whatsapp:{self.phone_number}",
                    "Body": message.text,
                },
            )

            return resp.status_code == 201

    def get_webhook_handler(self):
        """Return FastAPI route for WhatsApp webhooks."""
        from fastapi import APIRouter, Form, Request, Response
        from twilio.twiml.messaging_response import MessagingResponse

        router = APIRouter()

        @router.post("/webhooks/whatsapp")
        async def whatsapp_webhook(
            MessageSid: str = Form(None),
            From: str = Form(None),
            Body: str = Form(""),
            ProfileName: str = Form("User"),
        ):
            payload = {
                "MessageSid": MessageSid,
                "From": From,
                "Body": Body,
                "ProfileName": ProfileName,
            }

            message = await self.handle_inbound(payload)

            if message:
                # Process with agent
                from mcp.agent import OnboardingAgent
                agent = OnboardingAgent()
                result = await agent.run(message.text, thread_id=message.user_id)

                response_text = result.messages[-1].content if result.messages else "Got it!"
            else:
                response_text = ""

            # Return TwiML
            twiml = MessagingResponse()
            twiml.message(response_text)

            return Response(content=str(twiml), media_type="application/xml")

        @router.get("/webhooks/whatsapp")
        async def whatsapp_webhook_verify():
            """Twilio webhook verification."""
            return "OK"

        return router


# =============================================================================
# Discord Handler
# =============================================================================


class DiscordHandler(PlatformHandler):
    """Discord integration handler."""

    def __init__(self):
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    async def handle_inbound(self, payload: dict) -> Optional[InboundMessage]:
        """Handle Discord interactions."""
        interaction_type = payload.get("type")

        # Handle slash commands / buttons
        if interaction_type in [1, 2, 3, 4]:  # Ping, ApplicationCommand, MessageComponent, ModalSubmit
            data = payload.get("data", {})
            
            # Extract user info
            member = payload.get("member", {})
            user = member.get("user", {})
            user_id = user.get("id")
            username = user.get("username", "User")

            # Get command/button input
            if interaction_type == 2:  # ApplicationCommand
                options = data.get("options", [])
                text = ""
                for opt in options:
                    if opt.get("type") == 1:  # Subcommand group
                        text += opt.get("name", "") + " "
                        for sub_opt in opt.get("options", []):
                            text += sub_opt.get("value", "") + " "
                    elif opt.get("type") == 2:  # Subcommand
                        text += opt.get("name", "") + " "
                        for sub_opt in opt.get("options", []):
                            text += sub_opt.get("value", "") + " "
                    else:
                        text += opt.get("value", "")
            elif interaction_type == 3:  # MessageComponent
                text = data.get("custom_id", "")
            else:
                text = ""

            # Get channel
            channel_id = payload.get("channel_id")

            return InboundMessage(
                platform=Platform.DISCORD,
                user_id=user_id or "unknown",
                user_name=username,
                text=text.strip(),
                channel_id=channel_id or "unknown",
                raw_data=payload,
            )

        return None

    async def send_message(self, message: OutboundMessage) -> bool:
        """Send message to Discord."""
        import httpx

        # Prefer webhook if available
        if self.webhook_url:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.webhook_url,
                    json={
                        "content": message.text,
                        "embeds": message.embeds,
                    },
                )
                return resp.status_code == 204

        # Otherwise use bot API
        if not self.bot_token:
            logger.warning("DISCORD_BOT_TOKEN not configured")
            return False

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://discord.com/api/v10/channels/{message.channel_id}/messages",
                headers={"Authorization": f"Bot {self.bot_token}"},
                json={
                    "content": message.text,
                    "embeds": message.embeds,
                },
            )
            return resp.status_code == 200

    def get_webhook_handler(self):
        """Return FastAPI route for Discord webhooks."""
        from fastapi import APIRouter, Request, JSONResponse
        from fastapi.responses import Response

        router = APIRouter()

        @router.post("/webhooks/discord")
        async def discord_webhook(request: Request):
            # Handle interaction response immediately
            payload = await request.json()

            # First, handle the interaction ACK
            interaction_type = payload.get("type")
            if interaction_type == 1:  # Ping
                return JSONResponse({"type": 1})

            # Process the command
            message = await self.handle_inbound(payload)

            if message:
                from mcp.agent import OnboardingAgent
                agent = OnboardingAgent()
                result = await agent.run(message.text, thread_id=message.user_id)

                response_text = result.messages[-1].content if result.messages else "Got it!"

                # Send followup response
                await self.send_message(OutboundMessage(
                    platform=Platform.DISCORD,
                    channel_id=message.channel_id,
                    text=response_text,
                ))

                # Acknowledge the interaction
                return JSONResponse({
                    "type": 4,  # ChannelMessageWithSource
                    "data": {"content": response_text},
                })

            return JSONResponse({"type": 1})

        return router


# =============================================================================
# Messaging Router
# =============================================================================


class MessagingRouter:
    """Routes messages between platforms and the agent."""

    def __init__(self):
        self.handlers: dict[Platform, PlatformHandler] = {
            Platform.SLACK: SlackHandler(),
            Platform.WHATSAPP: WhatsAppHandler(),
            Platform.DISCORD: DiscordHandler(),
        }

    def get_handler(self, platform: Platform) -> PlatformHandler:
        """Get handler for platform."""
        return self.handlers.get(platform)

    def get_all_routes(self):
        """Get all webhook routes."""
        from fastapi import APIRouter

        main_router = APIRouter()

        for platform, handler in self.handlers.items():
            routes = handler.get_webhook_handler()
            for route in routes.routes:
                main_router.routes.append(route)

        return main_router

    async def send_to_user(
        self,
        platform: Platform,
        user_id: str,
        text: str,
    ) -> bool:
        """Send message to a user on a specific platform."""
        handler = self.get_handler(platform)
        if not handler:
            return False

        message = OutboundMessage(
            platform=platform,
            channel_id=user_id,
            text=text,
        )

        return await handler.send_message(message)


# =============================================================================
# Configuration
# =============================================================================

# Environment variables needed:
"""
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_API_KEY=SK...
TWILIO_API_SECRET=...
TWILIO_WHATSAPP_NUMBER=+1...

# Discord
DISCORD_BOT_TOKEN=...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
"""


__all__ = [
    "Platform",
    "InboundMessage",
    "OutboundMessage",
    "PlatformHandler",
    "SlackHandler",
    "WhatsAppHandler",
    "DiscordHandler",
    "MessagingRouter",
]