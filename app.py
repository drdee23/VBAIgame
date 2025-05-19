# Adventure Game
import os
import sys
if sys.platform == 'darwin':
    os.environ['SDL_VIDEODRIVER'] = 'cocoa'  # Use native macOS window system
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
import sys
import textwrap
import openai
from dotenv import load_dotenv
import time
from speech_system import SpeechSystem
import asyncio

# Load environment variables
load_dotenv()
# Ensure OpenAI API Key is loaded
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("[OpenAI] API key not found. Please set OPENAI_API_KEY in your .env file.")
    sys.exit(1)
openai.api_key = api_key
print("[OpenAI] API key loaded successfully.")

# Initialize Pygame with macOS specific settings
pygame.init()
display = (800, 600)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
screen = pygame.display.get_surface()

# Set up the camera and perspective
glEnable(GL_DEPTH_TEST)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)

# Set up basic lighting
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_POSITION, [0, 5, 5, 1])
glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

# Enable blending for transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Initial camera position
glTranslatef(0.0, 0.0, -5)

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Game map
GAME_MAP = [
    "WWWWWWWWWWWWWWWWWWWW",
    "W..................W",
    "W..................W",
    "W........N.........W",
    "W..................W",
    "W..................W",
    "W..................W",
    "W....P.............W",
    "W..................W",
    "W..................W",
    "W..................W",
    "W..................W",
    "WWWWWWWWWWWWWWWWWWWW"
]

# Add these constants near the other constants
TITLE = "Venture Builder AI"
SUBTITLE = "Our Digital Employees"
MENU_BG_COLOR = (0, 0, 0)  # Black background
MENU_TEXT_COLOR = (0, 255, 0)  # Matrix-style green
MENU_HIGHLIGHT_COLOR = (0, 200, 0)  # Slightly darker green for effects

def draw_cube():
    vertices = [
        # Front face
        [-0.5, -0.5,  0.5],
        [ 0.5, -0.5,  0.5],
        [ 0.5,  0.5,  0.5],
        [-0.5,  0.5,  0.5],
        # Back face
        [-0.5, -0.5, -0.5],
        [-0.5,  0.5, -0.5],
        [ 0.5,  0.5, -0.5],
        [ 0.5, -0.5, -0.5],
    ]
    
    surfaces = [
        [0, 1, 2, 3],  # Front
        [3, 2, 6, 5],  # Top
        [0, 3, 5, 4],  # Left
        [1, 7, 6, 2],  # Right
        [4, 5, 6, 7],  # Back
        [0, 4, 7, 1],  # Bottom
    ]
    
    glBegin(GL_QUADS)
    for surface in surfaces:
        glNormal3f(0, 0, 1)  # Simple normal for lighting
        for vertex in surface:
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_sphere(radius, slices, stacks):
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            
            glNormal3f(x * zr0, y * zr0, z0)
            glVertex3f(x * zr0 * radius, y * zr0 * radius, z0 * radius)
            glNormal3f(x * zr1, y * zr1, z1)
            glVertex3f(x * zr1 * radius, y * zr1 * radius, z1 * radius)
        glEnd()

class DialogueSystem:
    def __init__(self):
        self.active = False
        self.user_input = ""
        try:
            pygame.font.init()
            self.font = pygame.font.Font(None, 24)
            print("[DialogueSystem] Font loaded successfully")
        except Exception as e:
            print("[DialogueSystem] Font loading failed:", e)
        self.npc_message = ""
        self.input_active = False
        self.last_npc_text = ""
        self.last_input_text = ""
        self.conversation_history = []
        self.speech_system = SpeechSystem()
        self.speech_enabled = False
        self.current_npc = None
        self.initial_player_pos = None
        self.current_emotion = None

        # Create a surface for the UI
        self.ui_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.ui_texture = glGenTextures(1)

    def start_conversation(self, npc_role="HR", player_pos=None):
        """Start a new conversation with an NPC"""
        self.active = True
        self.input_active = True
        self.initial_player_pos = player_pos
        self.current_npc = npc_role
        
        # Set initial voice based on NPC role
        if npc_role == "HR":
            self.speech_system.set_npc_voice("nova", speed=1.0, pitch=1.0)
            self.current_emotion = "friendly"
        elif npc_role == "CEO":
            self.speech_system.set_npc_voice("onyx", speed=0.9, pitch=0.9)
            self.current_emotion = "authoritative"
        
        # Add greeting message
        greeting = f"Hello! I'm the {npc_role}. How can I help you today?"
        self.npc_message = greeting
        self.last_npc_text = greeting
        self.conversation_history.append(("NPC", greeting))
        
        # Convert greeting to speech if speech is enabled
        if self.speech_enabled:
            asyncio.run(self.speech_system._text_to_speech(greeting))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.send_message()
            elif event.key == pygame.K_BACKSPACE:
                self.user_input = self.user_input[:-1]
            elif event.key == pygame.K_ESCAPE:
                # Properly exit chat and reset all states
                print("Exiting conversation...")
                self.active = False
                self.input_active = False
                self.user_input = ""
                self.npc_message = ""
                self.last_npc_text = ""
                self.current_npc = None
                if self.speech_enabled:
                    self.speech_system.stop_listening()
                    self.speech_system.interrupt_speech()  # Stop any ongoing speech
                    self.speech_enabled = False
                # Clear conversation history
                self.conversation_history = []
                print("Conversation exited and states reset")
            elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                # Handle paste
                try:
                    self.user_input += pygame.scrap.get(pygame.SCRAP_TEXT).decode('utf-8')
                except:
                    pass
            elif event.key == pygame.K_t and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                # Toggle speech mode with Shift+T
                print("Shift+T detected - Toggle speech mode")
                self.speech_enabled = not self.speech_enabled
                print(f"Speech mode toggled: {self.speech_enabled}")
                if self.speech_enabled:
                    self.speech_system.start_listening()
                else:
                    self.speech_system.stop_listening()
                    self.speech_system.interrupt_speech()  # Stop any ongoing speech
            elif event.key == pygame.K_SPACE and self.speech_system.is_currently_speaking():
                # Interrupt NPC speech with spacebar
                print("Interrupting NPC speech...")
                self.speech_system.interrupt_speech()
                # Add interruption message to conversation
                self.conversation_history.append(("System", "NPC speech interrupted"))
                # Clear any pending input to ensure clean state
                self.user_input = ""
            elif event.unicode.isprintable():
                self.user_input += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.input_active = True

    def render(self):
        if not self.active:
            return

        self.ui_surface.fill((0, 0, 0, 0))

        if self.active:
            box_height = 200
            box_y = WINDOW_HEIGHT - box_height - 20
            
            # Make the background MUCH darker - almost black with some transparency
            box_color = (0, 0, 0, 230)  # Changed to very dark, mostly opaque background
            pygame.draw.rect(self.ui_surface, box_color, (20, box_y, WINDOW_WIDTH - 40, box_height))
            
            # White border
            pygame.draw.rect(self.ui_surface, (255, 255, 255, 255), (20, box_y, WINDOW_WIDTH - 40, box_height), 2)

            # Controls instruction
            controls_text = "Press Shift+T to toggle speech mode | Press ESC to exit chat"
            controls_surface = self.font.render(controls_text, True, (255, 255, 255))
            self.ui_surface.blit(controls_surface, (40, box_y + 10))

            # Display conversation history
            y_offset = box_y + 40
            for role, message in self.conversation_history[-3:]:  # Show last 3 messages
                prefix = "NPC: " if role == "NPC" else "You: "
                message_text = prefix + message
                # Split long messages into multiple lines
                words = message_text.split()
                lines = []
                current_line = []
                current_width = 0
                
                for word in words:
                    word_surface = self.font.render(word + ' ', True, (255, 255, 255))
                    word_width = word_surface.get_width()
                    
                    if current_width + word_width <= WINDOW_WIDTH - 80:  # Leave margin
                        current_line.append(word)
                        current_width += word_width
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_width = word_width
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Render each line
                for line in lines:
                    line_surface = self.font.render(line, True, (255, 255, 255))
                    self.ui_surface.blit(line_surface, (40, y_offset))
                    y_offset += 25  # Increased line spacing

            # Input prompt in white
            if self.input_active:
                input_prompt = "> " + self.user_input + "_"
                input_surface = self.font.render(input_prompt, True, (255, 255, 255))
                self.ui_surface.blit(input_surface, (40, box_y + box_height - 40))

            # Display speech mode and emotion indicators
            indicators_y = box_y + box_height - 70
            if self.speech_enabled:
                speech_indicator = self.font.render("Speech Mode: ON", True, (0, 255, 0))
                self.ui_surface.blit(speech_indicator, (40, indicators_y))
            
            if self.current_emotion:
                emotion_indicator = self.font.render(f"Emotion: {self.current_emotion.capitalize()}", True, (255, 255, 0))
                self.ui_surface.blit(emotion_indicator, (200, indicators_y))

        # Convert surface to OpenGL texture
        texture_data = pygame.image.tostring(self.ui_surface, "RGBA", True)

        # Save current OpenGL state
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Setup for 2D rendering
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)

        # Bind and update texture
        glBindTexture(GL_TEXTURE_2D, self.ui_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

        # Draw the UI texture
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(WINDOW_WIDTH, 0)
        glTexCoord2f(1, 1); glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glTexCoord2f(0, 1); glVertex2f(0, WINDOW_HEIGHT)
        glEnd()

        # Restore OpenGL state
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

    def send_message(self):
        if self.user_input.strip():
            print(f"Sending message: {self.user_input}")
            self.last_input_text = self.user_input
            self.conversation_history.append(("Player", self.user_input))
            
            # Process speech if enabled
            if self.speech_enabled:
                print("Speech mode enabled, processing speech input")
                asyncio.run(self._process_speech_input(self.user_input))
            else:
                print("Speech mode disabled, processing text input")
                # Regular text-based processing
                self._process_text_input(self.user_input)
            
            self.user_input = ""

    async def _process_speech_input(self, text):
        try:
            # Check if we should interrupt current speech
            if self.speech_system.is_currently_speaking():
                self.speech_system.interrupt_speech()
                self.conversation_history.append(("System", "Previous response interrupted"))
                # Add a small delay to ensure clean state
                await asyncio.sleep(0.1)

            # Get response from OpenAI with emotion detection
            response = await self.speech_system._get_openai_response(text)
            if response:
                print(f"Speech response received: {response}")
                # Update both text and voice
                self.npc_message = response
                self.last_npc_text = response
                self.conversation_history.append(("NPC", response))
                
                # Convert response to speech
                await self.speech_system._text_to_speech(response)
        except Exception as e:
            print(f"Error processing speech input: {e}")
            error_msg = "Sorry, I couldn't process that."
            self.npc_message = error_msg
            self.last_npc_text = error_msg
            self.conversation_history.append(("NPC", error_msg))

    def _process_text_input(self, text):
        # Existing text-based processing logic
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": text}]
            )
            npc_response = response.choices[0].message.content
            print(f"OpenAI response: {npc_response}")
            self.npc_message = npc_response
            self.last_npc_text = npc_response
            self.conversation_history.append(("NPC", npc_response))
        except Exception as e:
            print(f"Error processing text input: {e}")
            self.npc_message = "Sorry, I couldn't process that."

class World:
    def __init__(self):
        self.size = 5
        # Define office furniture colors
        self.colors = {
            'floor': (0.76, 0.6, 0.42),  # Light wood color
            'walls': (0.85, 0.85, 0.85),  # Changed to light gray (from 0.95)
            'desk': (0.6, 0.4, 0.2),  # Brown wood
            'chair': (0.2, 0.2, 0.2),  # Dark grey
            'computer': (0.1, 0.1, 0.1),  # Black
            'plant': (0.2, 0.5, 0.2),  # Green
            'partition': (0.3, 0.3, 0.3)  # Darker solid gray for booth walls
        }
        
    def draw_desk(self, x, z, rotation=0):
        glPushMatrix()
        glTranslatef(x, 0, z)  # Start at floor level
        glRotatef(rotation, 0, 1, 0)
        
        # Desk top (reduced size)
        glColor3f(*self.colors['desk'])
        glBegin(GL_QUADS)
        glVertex3f(-0.4, 0.4, -0.3)
        glVertex3f(0.4, 0.4, -0.3)
        glVertex3f(0.4, 0.4, 0.3)
        glVertex3f(-0.4, 0.4, 0.3)
        glEnd()
        
        # Desk legs (adjusted for new height)
        for x_offset, z_offset in [(-0.35, -0.25), (0.35, -0.25), (-0.35, 0.25), (0.35, 0.25)]:
            glBegin(GL_QUADS)
            glVertex3f(x_offset-0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0.4, z_offset-0.02)
            glVertex3f(x_offset-0.02, 0.4, z_offset-0.02)
            glEnd()
        
        # Computer monitor (smaller)
        glColor3f(*self.colors['computer'])
        glTranslatef(-0.15, 0.4, 0)
        glBegin(GL_QUADS)
        glVertex3f(-0.1, 0, -0.05)
        glVertex3f(0.1, 0, -0.05)
        glVertex3f(0.1, 0.2, -0.05)
        glVertex3f(-0.1, 0.2, -0.05)
        glEnd()
        
        glPopMatrix()
    
    def draw_chair(self, x, z, rotation=0):
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glColor3f(*self.colors['chair'])
        
        # Seat (lowered and smaller)
        glBegin(GL_QUADS)
        glVertex3f(-0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.25, 0.15)
        glVertex3f(-0.15, 0.25, 0.15)
        glEnd()
        
        # Back (adjusted height)
        glBegin(GL_QUADS)
        glVertex3f(-0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.5, -0.15)
        glVertex3f(-0.15, 0.5, -0.15)
        glEnd()
        
        # Chair legs (adjusted height)
        for x_offset, z_offset in [(-0.12, -0.12), (0.12, -0.12), (-0.12, 0.12), (0.12, 0.12)]:
            glBegin(GL_QUADS)
            glVertex3f(x_offset-0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0.25, z_offset-0.02)
            glVertex3f(x_offset-0.02, 0.25, z_offset-0.02)
            glEnd()
            
        glPopMatrix()
    
    def draw_plant(self, x, z):
        glPushMatrix()
        glTranslatef(x, 0, z)
        
        # Plant pot (smaller)
        glColor3f(0.4, 0.2, 0.1)  # Brown pot
        pot_radius = 0.1
        pot_height = 0.15
        segments = 8
        
        # Draw the pot sides
        glBegin(GL_QUADS)
        for i in range(segments):
            angle1 = (i / segments) * 2 * math.pi
            angle2 = ((i + 1) / segments) * 2 * math.pi
            x1 = math.cos(angle1) * pot_radius
            z1 = math.sin(angle1) * pot_radius
            x2 = math.cos(angle2) * pot_radius
            z2 = math.sin(angle2) * pot_radius
            glVertex3f(x1, 0, z1)
            glVertex3f(x2, 0, z2)
            glVertex3f(x2, pot_height, z2)
            glVertex3f(x1, pot_height, z1)
        glEnd()
        
        # Plant leaves (smaller)
        glColor3f(*self.colors['plant'])
        glTranslatef(0, pot_height, 0)
        leaf_size = 0.15
        num_leaves = 6
        for i in range(num_leaves):
            angle = (i / num_leaves) * 2 * math.pi
            x = math.cos(angle) * leaf_size
            z = math.sin(angle) * leaf_size
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 0, 0)
            glVertex3f(x, leaf_size, z)
            glVertex3f(z, leaf_size/2, -x)
            glEnd()
        
        glPopMatrix()
        
    def draw(self):
        # Set material properties
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Draw floor at Y=0
        glBegin(GL_QUADS)
        glColor3f(*self.colors['floor'])
        glNormal3f(0, 1, 0)
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 0, -self.size)
        glEnd()
        
        # Draw walls starting from floor level
        glBegin(GL_QUADS)
        glColor3f(*self.colors['walls'])
        
        # Front wall
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(self.size, 0, -self.size)
        glVertex3f(self.size, 2, -self.size)
        glVertex3f(-self.size, 2, -self.size)
        
        # Back wall
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 2, self.size)
        glVertex3f(-self.size, 2, self.size)
        
        # Left wall
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(-self.size, 2, self.size)
        glVertex3f(-self.size, 2, -self.size)
        
        # Right wall
        glVertex3f(self.size, 0, -self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 2, self.size)
        glVertex3f(self.size, 2, -self.size)
        glEnd()
        
        # Draw office furniture in a more realistic arrangement
        # HR Area (left side)
        self.draw_desk(-4, -2, 90)
        self.draw_chair(-3.5, -2, 90)
        self.draw_partition_walls(-4, -2)  # Add booth walls for HR
        
        # CEO Area (right side)
        self.draw_desk(4, 1, -90)
        self.draw_chair(3.5, 1, -90)
        self.draw_partition_walls(4, 1)  # Add booth walls for CEO
        
        # Plants in corners (moved closer to walls)
        self.draw_plant(-4.5, -4.5)
        self.draw_plant(4.5, -4.5)
        self.draw_plant(-4.5, 4.5)
        self.draw_plant(4.5, 4.5)

    def draw_partition_walls(self, x, z):
        """Draw booth partition walls - all surfaces in solid gray"""
        glColor3f(0.3, 0.3, 0.3)  # Solid gray for all walls
        
        # Back wall (smaller and thinner)
        glPushMatrix()
        glTranslatef(x, 0, z)
        glScalef(0.05, 1.0, 1.0)  # Thinner wall, normal height, shorter length
        draw_cube()  # Replace glutSolidCube with draw_cube
        glPopMatrix()
        
        # Side wall (smaller and thinner)
        glPushMatrix()
        glTranslatef(x, 0, z + 0.5)  # Moved closer
        glRotatef(90, 0, 1, 0)
        glScalef(0.05, 1.0, 0.8)  # Thinner wall, normal height, shorter length
        draw_cube()  # Replace glutSolidCube with draw_cube
        glPopMatrix()

class Player:
    def __init__(self):
        self.pos = [0, 0.5, 0]  # Lowered Y position to be just above floor
        self.rot = [0, 0, 0]
        self.speed = 0.3
        self.mouse_sensitivity = 0.5
        
    def move(self, dx, dz):
        # Convert rotation to radians (negative because OpenGL uses clockwise rotation)
        angle = math.radians(-self.rot[1])
        
        # Calculate movement vector
        move_x = (dx * math.cos(angle) + dz * math.sin(angle)) * self.speed
        move_z = (-dx * math.sin(angle) + dz * math.cos(angle)) * self.speed
        
        # Calculate new position
        new_x = self.pos[0] + move_x
        new_z = self.pos[2] + move_z
        
        # Wall collision check (room is 10x10)
        room_limit = 4.5  # Slightly less than room size/2 to prevent wall clipping
        if abs(new_x) < room_limit:
            self.pos[0] = new_x
        if abs(new_z) < room_limit:
            self.pos[2] = new_z

    def update_rotation(self, dx, dy):
        # Multiply mouse movement by sensitivity for faster turning
        self.rot[1] += dx * self.mouse_sensitivity

class NPC:
    def __init__(self, x, y, z, role="HR"):
        self.scale = 0.6  # Make NPCs smaller (about 60% of current size)
        # Position them beside the desks, at ground level
        # Adjust Y position to be half their height (accounting for scale)
        self.pos = [x, 0.65, z]  # This puts their feet on the ground
        self.size = 0.5
        self.role = role
        
        # Enhanced color palette
        self.skin_color = (0.8, 0.7, 0.6)  # Neutral skin tone
        self.hair_color = (0.2, 0.15, 0.1) if role == "HR" else (0.3, 0.3, 0.3)  # Dark brown vs gray
        
        # Updated clothing colors
        if role == "HR":
            self.clothes_primary = (0.8, 0.2, 0.2)    # Bright red
            self.clothes_secondary = (0.6, 0.15, 0.15) # Darker red
        else:  # CEO
            self.clothes_primary = (0.2, 0.3, 0.8)    # Bright blue
            self.clothes_secondary = (0.15, 0.2, 0.6)  # Darker blue

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glScalef(self.scale, self.scale, self.scale)
        
        # Head
        glColor3f(*self.skin_color)
        draw_sphere(0.12, 16, 16)
        
        # Hair (slightly larger than head)
        glColor3f(*self.hair_color)
        glPushMatrix()
        glTranslatef(0, 0.05, 0)  # Slightly above head
        draw_sphere(0.13, 16, 16)
        glPopMatrix()
        
        # Body (torso)
        glColor3f(*self.clothes_primary)
        glPushMatrix()
        glTranslatef(0, -0.3, 0)  # Move down from head
        glScalef(0.3, 0.4, 0.2)   # Make it rectangular
        draw_cube()
        glPopMatrix()
        
        # Arms
        glColor3f(*self.clothes_secondary)
        for x_offset in [-0.2, 0.2]:  # Left and right arms
            glPushMatrix()
            glTranslatef(x_offset, -0.3, 0)
            glScalef(0.1, 0.4, 0.1)
            draw_cube()
            glPopMatrix()
        
        # Legs
        glColor3f(*self.clothes_secondary)
        for x_offset in [-0.1, 0.1]:  # Left and right legs
            glPushMatrix()
            glTranslatef(x_offset, -0.8, 0)
            glScalef(0.1, 0.5, 0.1)
            draw_cube()
            glPopMatrix()
        
        glPopMatrix()

class MenuScreen:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 74)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.active = True
        self.start_time = time.time()
        
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Create a surface for 2D rendering
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        
        # Calculate vertical positions
        center_y = WINDOW_HEIGHT // 2
        title_y = center_y - 100
        subtitle_y = center_y - 20
        prompt_y = center_y + 100
        
        # Render title with "typing" effect
        elapsed_time = time.time() - self.start_time
        title_chars = int(min(len(TITLE), elapsed_time * 15))  # Type 15 chars per second
        partial_title = TITLE[:title_chars]
        title_surface = self.font_large.render(partial_title, True, MENU_TEXT_COLOR)
        title_x = (WINDOW_WIDTH - title_surface.get_width()) // 2
        surface.blit(title_surface, (title_x, title_y))
        
        # Render subtitle with fade-in effect
        if elapsed_time > len(TITLE) / 15:  # Start after title is typed
            subtitle_alpha = min(255, int((elapsed_time - len(TITLE) / 15) * 255))
            subtitle_surface = self.font_medium.render(SUBTITLE, True, MENU_TEXT_COLOR)
            subtitle_surface.set_alpha(subtitle_alpha)
            subtitle_x = (WINDOW_WIDTH - subtitle_surface.get_width()) // 2
            surface.blit(subtitle_surface, (subtitle_x, subtitle_y))
        
        # Render "Press ENTER" with blinking effect
        if elapsed_time > (len(TITLE) / 15 + 1):  # Start after subtitle fade
            if int(elapsed_time * 2) % 2:  # Blink every 0.5 seconds
                prompt_text = "Press ENTER to start"
                prompt_surface = self.font_small.render(prompt_text, True, MENU_TEXT_COLOR)
                prompt_x = (WINDOW_WIDTH - prompt_surface.get_width()) // 2
                surface.blit(prompt_surface, (prompt_x, prompt_y))
        
        # Add some retro effects (scanlines)
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(surface, (0, 50, 0), (0, y), (WINDOW_WIDTH, y))
        
        # Convert surface to OpenGL texture
        texture_data = pygame.image.tostring(surface, "RGBA", True)
        
        # Set up orthographic projection for 2D rendering
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Render the texture in OpenGL
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Draw the texture
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(WINDOW_WIDTH, 0)
        glTexCoord2f(1, 0); glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glTexCoord2f(0, 0); glVertex2f(0, WINDOW_HEIGHT)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        
        # Reset OpenGL state for 3D rendering
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_DEPTH_TEST)

        pygame.display.flip()

# Modify the Game3D class to include the menu
class Game3D:
    def __init__(self):
        self.menu = MenuScreen()
        self.player = Player()
        self.world = World()
        self.dialogue = DialogueSystem()
        self.hr_npc = NPC(-3.3, 0, -2, "HR")  # Moved beside the desk
        self.ceo_npc = NPC(3.3, 0, 1, "CEO")  # Moved beside the desk
        self.interaction_distance = 2.0
        self.last_interaction_time = 0
        self.current_npc = None
        self.nearby_npc = None  # Track which NPC is nearby

    def check_nearby_npc(self):
        """Check which NPC is nearby without starting conversation"""
        # Check distance to HR NPC
        dx = self.player.pos[0] - self.hr_npc.pos[0]
        dz = self.player.pos[2] - self.hr_npc.pos[2]
        hr_distance = math.sqrt(dx*dx + dz*dz)
        
        # Check distance to CEO NPC
        dx = self.player.pos[0] - self.ceo_npc.pos[0]
        dz = self.player.pos[2] - self.ceo_npc.pos[2]
        ceo_distance = math.sqrt(dx*dx + dz*dz)
        
        # Determine which NPC is nearby
        if hr_distance < self.interaction_distance:
            self.nearby_npc = "HR"
        elif ceo_distance < self.interaction_distance:
            self.nearby_npc = "CEO"
        else:
            self.nearby_npc = None

    def start_npc_conversation(self):
        """Start conversation with nearby NPC using TAB key"""
        if self.nearby_npc and not self.dialogue.active:
            print(f"Starting conversation with {self.nearby_npc}")
            self.dialogue.start_conversation(self.nearby_npc, self.player.pos)
            self.current_npc = self.nearby_npc
            self.last_interaction_time = time.time()

    def run(self):
        running = True
        while running:
            if self.menu.active:
                # Menu loop
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN and time.time() - self.menu.start_time > (len(TITLE) / 15 + 1):
                            self.menu.active = False
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_q and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                            running = False
                
                self.menu.render()
            else:
                # Main game loop
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.dialogue.active:
                                # Let the dialogue system handle ESC
                                self.dialogue.handle_input(event)
                            else:
                                pygame.mouse.set_visible(True)
                                pygame.event.set_grab(False)
                                running = False
                        elif event.key == pygame.K_q and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                            running = False
                        elif event.key == pygame.K_TAB:
                            # Start conversation with nearby NPC
                            self.start_npc_conversation()
                        
                        # Handle dialogue input
                        if self.dialogue.active:
                            self.dialogue.handle_input(event)
                    elif event.type == pygame.MOUSEMOTION:
                        x, y = event.rel
                        self.player.update_rotation(x, y)

                # Handle keyboard input for movement
                if not self.dialogue.active:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_w]: self.player.move(0, -1)
                    if keys[pygame.K_s]: self.player.move(0, 1)
                    if keys[pygame.K_a]: self.player.move(-1, 0)
                    if keys[pygame.K_d]: self.player.move(1, 0)

                # Check which NPC is nearby
                self.check_nearby_npc()

                # Clear the screen and depth buffer
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                # Save the current matrix
                glPushMatrix()

                # Apply player rotation and position
                glRotatef(self.player.rot[0], 1, 0, 0)
                glRotatef(self.player.rot[1], 0, 1, 0)
                glTranslatef(-self.player.pos[0], -self.player.pos[1], -self.player.pos[2])

                # Draw the world and NPCs
                self.world.draw()
                self.hr_npc.draw()
                self.ceo_npc.draw()

                # Restore the matrix
                glPopMatrix()

                # Render dialogue system (if active)
                self.dialogue.render()

                # Show interaction prompt if near an NPC
                if self.nearby_npc and not self.dialogue.active:
                    self.show_interaction_prompt()

                # Swap the buffers
                pygame.display.flip()

                # Maintain 60 FPS
                pygame.time.Clock().tick(60)

        pygame.quit()

    def show_interaction_prompt(self):
        """Show a prompt to press TAB when near an NPC"""
        if self.nearby_npc:
            # Create a surface for the prompt
            prompt_surface = pygame.Surface((WINDOW_WIDTH, 30), pygame.SRCALPHA)
            prompt_surface.fill((0, 0, 0, 180))  # Semi-transparent black background
            
            # Create the prompt text
            font = pygame.font.Font(None, 24)
            prompt_text = f"Press TAB to talk to {self.nearby_npc}"
            text_surface = font.render(prompt_text, True, (255, 255, 255))
            
            # Center the text
            text_x = (WINDOW_WIDTH - text_surface.get_width()) // 2
            text_y = (30 - text_surface.get_height()) // 2
            
            # Draw the text
            prompt_surface.blit(text_surface, (text_x, text_y))
            
            # Convert to OpenGL texture and render
            texture_data = pygame.image.tostring(prompt_surface, "RGBA", True)
            
            # Save current OpenGL state
            glPushAttrib(GL_ALL_ATTRIB_BITS)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            # Setup for 2D rendering
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_TEXTURE_2D)
            
            # Create and bind texture
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, 30, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
            
            # Draw the prompt at the bottom of the screen with corrected coordinates
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex2f(0, WINDOW_HEIGHT - 30)
            glTexCoord2f(1, 1); glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT - 30)
            glTexCoord2f(1, 0); glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
            glTexCoord2f(0, 0); glVertex2f(0, WINDOW_HEIGHT)
            glEnd()
            
            # Clean up
            glDeleteTextures(1, [texture])
            
            # Restore OpenGL state
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            glPopAttrib()

# Create and run game
game = Game3D()
game.run()

