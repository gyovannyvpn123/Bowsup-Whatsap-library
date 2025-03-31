#!/usr/bin/env python3
"""
Command-line interface for Bocksup.

This example provides a command-line interface for interacting with WhatsApp
using the Bocksup library, allowing users to send messages, create groups,
and more.
"""

import os
import sys
import asyncio
import logging
import argparse
import getpass
import json
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

# Add parent directory to path to import bocksup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bocksup
from bocksup.stack.builder import StackBuilder
from bocksup.messaging.messages import TextMessage, MediaMessage
from bocksup.registration.client import RegistrationClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bocksup.cli')

class BocksupCLI:
    """Command-line interface for interacting with WhatsApp using Bocksup."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.stack = None
        self.running = False
        self.phone_number = None
        self.password = None
        self.message_history = []
        
    async def start(self, phone_number: str, password: str) -> None:
        """
        Start the CLI.
        
        Args:
            phone_number: WhatsApp phone number
            password: WhatsApp password
        """
        logger.info("Starting Bocksup CLI")
        
        self.phone_number = phone_number
        self.password = password
        
        # Create stack builder
        builder = StackBuilder()
        
        # Set message handler
        builder.set_message_handler(self.handle_message)
        builder.set_receipt_handler(self.handle_receipt)
        builder.set_presence_handler(self.handle_presence)
        builder.set_disconnect_handler(self.handle_disconnect)
        
        # Build the stack
        self.stack = builder.build((self.phone_number, self.password))
        
        # Connect to WhatsApp
        if not await self.stack.connect():
            logger.error("Failed to connect to WhatsApp")
            return
            
        # Authenticate
        if not await self.stack.authenticate():
            logger.error("Failed to authenticate with WhatsApp")
            await self.stack.disconnect()
            return
            
        logger.info("Connected to WhatsApp")
        
        # Set running flag
        self.running = True
        
        # Run the command loop
        await self.command_loop()
        
    async def stop(self) -> None:
        """Stop the CLI."""
        logger.info("Stopping Bocksup CLI")
        
        if self.stack:
            await self.stack.disconnect()
            
        self.running = False
        logger.info("Bocksup CLI stopped")
        
    async def command_loop(self) -> None:
        """Run the command loop."""
        print("\nBocksup CLI - WhatsApp Command Line Interface")
        print("Type 'help' for a list of commands")
        
        while self.running:
            try:
                command = await ainput("\n> ")
                if not command:
                    continue
                    
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd == "exit" or cmd == "quit":
                    await self.cmd_exit()
                elif cmd == "help":
                    self.cmd_help()
                elif cmd == "send":
                    await self.cmd_send(args)
                elif cmd == "status":
                    self.cmd_status()
                elif cmd == "history":
                    self.cmd_history()
                elif cmd == "register":
                    await self.cmd_register()
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for a list of commands")
                    
            except KeyboardInterrupt:
                await self.cmd_exit()
            except Exception as e:
                logger.error(f"Error in command loop: {str(e)}")
                print(f"Error: {str(e)}")
                
    async def handle_message(self, message_data: Dict[str, Any]) -> None:
        """
        Handle incoming WhatsApp messages.
        
        Args:
            message_data: Message data dictionary
        """
        try:
            # Extract message details
            message_type = message_data.get('type')
            from_jid = message_data.get('from')
            
            # Add to history
            self.message_history.append({
                'direction': 'in',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': message_data
            })
            
            if message_type == 'text':
                body = message_data.get('body', '')
                print(f"\n[Message from {from_jid}]: {body}")
            elif message_type == 'media':
                media_type = message_data.get('media_type')
                print(f"\n[Media message from {from_jid}]: {media_type}")
            else:
                print(f"\n[Message from {from_jid}]: {message_type}")
                
            print("> ", end="", flush=True)  # Restore prompt
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            
    async def handle_receipt(self, receipt_data: Dict[str, Any]) -> None:
        """
        Handle message receipts.
        
        Args:
            receipt_data: Receipt data dictionary
        """
        try:
            # Extract receipt details
            receipt_type = receipt_data.get('receipt_type')
            message_id = receipt_data.get('message_id')
            
            print(f"\n[Receipt]: {receipt_type} for message {message_id}")
            print("> ", end="", flush=True)  # Restore prompt
            
        except Exception as e:
            logger.error(f"Error handling receipt: {str(e)}")
            
    async def handle_presence(self, presence_data: Dict[str, Any]) -> None:
        """
        Handle presence updates.
        
        Args:
            presence_data: Presence data dictionary
        """
        try:
            # Extract presence details
            jid = presence_data.get('jid')
            status = presence_data.get('status')
            
            print(f"\n[Presence]: {jid} is {status}")
            print("> ", end="", flush=True)  # Restore prompt
            
        except Exception as e:
            logger.error(f"Error handling presence: {str(e)}")
            
    async def handle_disconnect(self, event_data: Dict[str, Any]) -> None:
        """
        Handle disconnection events.
        
        Args:
            event_data: Event data dictionary
        """
        try:
            # Extract event details
            event_type = event_data.get('type')
            error = event_data.get('error')
            
            print(f"\n[Disconnect]: {event_type} - {error}")
            
            # If it's a permanent disconnection, exit the CLI
            if event_data.get('permanent', False):
                print("Permanent disconnection, exiting...")
                self.running = False
            else:
                print("> ", end="", flush=True)  # Restore prompt
                
        except Exception as e:
            logger.error(f"Error handling disconnect: {str(e)}")
            
    async def cmd_exit(self) -> None:
        """Handle the exit command."""
        print("Exiting...")
        await self.stop()
        
    def cmd_help(self) -> None:
        """Handle the help command."""
        print("\nAvailable commands:")
        print("  help                - Show this help message")
        print("  exit, quit          - Exit the CLI")
        print("  send <jid> <message> - Send a message to a contact")
        print("  status              - Show connection status")
        print("  history             - Show message history")
        print("  register            - Register a new WhatsApp account")
        
    async def cmd_send(self, args: str) -> None:
        """
        Handle the send command.
        
        Args:
            args: Command arguments
        """
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: send <jid> <message>")
            return
            
        jid = parts[0]
        message = parts[1]
        
        # Add '@s.whatsapp.net' if not present
        if '@' not in jid:
            jid = f"{jid}@s.whatsapp.net"
            
        # Create message
        message_data = {
            'type': 'text',
            'to': jid,
            'body': message
        }
        
        # Add to history
        self.message_history.append({
            'direction': 'out',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': message_data
        })
        
        # Send message
        if await self.stack.send_message(message_data):
            print(f"Message sent to {jid}")
        else:
            print(f"Failed to send message to {jid}")
            
    def cmd_status(self) -> None:
        """Handle the status command."""
        if not self.stack:
            print("Not connected")
            return
            
        print("\nConnection status:")
        print(f"  Connected: {self.stack.is_connected}")
        print(f"  Authenticated: {self.stack.is_authenticated}")
        print(f"  Phone number: {self.phone_number}")
        
    def cmd_history(self) -> None:
        """Handle the history command."""
        if not self.message_history:
            print("No message history")
            return
            
        print("\nMessage history:")
        for i, entry in enumerate(self.message_history[-10:], 1):
            direction = entry['direction']
            timestamp = entry['timestamp']
            message = entry['message']
            
            if direction == 'in':
                from_jid = message.get('from', 'unknown')
                if message.get('type') == 'text':
                    body = message.get('body', '')
                    print(f"  {i}. [{timestamp}] From {from_jid}: {body}")
                else:
                    print(f"  {i}. [{timestamp}] From {from_jid}: {message.get('type')} message")
            else:
                to_jid = message.get('to', 'unknown')
                if message.get('type') == 'text':
                    body = message.get('body', '')
                    print(f"  {i}. [{timestamp}] To {to_jid}: {body}")
                else:
                    print(f"  {i}. [{timestamp}] To {to_jid}: {message.get('type')} message")
                    
    async def cmd_register(self) -> None:
        """Handle the register command."""
        print("\nRegister a new WhatsApp account")
        
        # Get user input
        country_code = await ainput("Country code (without +): ")
        phone_number = await ainput("Phone number (without country code): ")
        
        # Create registration client
        client = RegistrationClient(country_code, phone_number)
        
        # Request verification code
        method = await ainput("Verification method (sms/voice) [sms]: ") or "sms"
        
        try:
            if await client.request_code(method=method):
                print(f"Verification code requested via {method}")
                print("Check your phone for the verification code")
                
                # Get verification code
                code = await ainput("Enter verification code: ")
                
                # Complete registration
                credentials = await client.register(code)
                
                # Save credentials
                creds_path = await client.save_credentials(credentials)
                
                print(f"Registration successful!")
                print(f"Credentials saved to: {creds_path}")
                print(f"Phone number: {credentials['phone']}")
                print(f"Password: {credentials['password']}")
                print("You can now use these credentials to login")
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            print(f"Error during registration: {str(e)}")

async def ainput(prompt: str = "") -> str:
    """
    Asynchronous version of input().
    
    Args:
        prompt: Input prompt
        
    Returns:
        User input string
    """
    # This is a simple wrapper around input() that runs in a thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))

async def main():
    """Main function to run the Bocksup CLI."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Bocksup Command Line Interface')
    parser.add_argument('--phone', help='Phone number (with country code)')
    parser.add_argument('--password', help='WhatsApp password')
    parser.add_argument('--credentials', help='Path to credentials file')
    args = parser.parse_args()
    
    # Load credentials
    phone = args.phone
    password = args.password
    
    if args.credentials:
        try:
            credentials = await RegistrationClient.load_credentials(args.credentials)
            phone = credentials.get('phone')
            password = credentials.get('password')
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            print(f"Error loading credentials: {str(e)}")
            return
            
    # Prompt for credentials if not provided
    if not phone:
        phone = input("Phone number (with country code): ")
        
    if not password:
        password = getpass.getpass("Password: ")
        
    # Create and start the CLI
    cli = BocksupCLI()
    try:
        await cli.start(phone, password)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping CLI")
    finally:
        await cli.stop()

if __name__ == '__main__':
    asyncio.run(main())
