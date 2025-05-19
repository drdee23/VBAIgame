# VBAI Game Development Documentation

## Table of Contents
1. [Project Setup](#project-setup)
2. [Core Features](#core-features)
3. [Technical Implementation](#technical-implementation)
4. [Development Process](#development-process)
5. [Challenges & Solutions](#challenges--solutions)
6. [Learning Outcomes](#learning-outcomes)
7. [Future Improvements](#future-improvements)
8. [Voice System Documentation](#voice-system-documentation)

## Project Setup

### Environment Configuration

#### 1. Python Virtual Environment Setup
```bash
# Create a new virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate


```

#### 2. Install Dependencies
```bash
# Core dependencies
pip install pygame PyOpenGL numpy openai python-dotenv

# Speech and Audio dependencies
pip install websockets==12.0        # For real-time audio streaming
pip install sounddevice==0.4.6      # For audio input/output handling
pip install soundfile==0.12.1       # For audio file processing
pip install SpeechRecognition==3.10.1  # For speech-to-text conversion
pip install pydub==0.25.1           # For audio processing and manipulation
pip install python-socketio==5.11.1  # For real-time communication

# Or install all dependencies from requirements.txt
pip install -r requirements.txt
```

#### 3. Environment Variables
```bash
# Create .env file in project root
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Dependencies Overview
1. **Core Dependencies**
   - pygame: Game development and window management
   - PyOpenGL: 3D graphics rendering
   - numpy: Numerical computations
   - openai: AI integration for conversations
   - python-dotenv: Environment variable management

2. **Speech and Audio Dependencies**
   - websockets: Enables real-time audio streaming for speech recognition
   - sounddevice: Handles microphone input and audio output
   - soundfile: Processes audio files and formats
   - SpeechRecognition: Converts speech to text
   - pydub: Processes and manipulates audio data
   - python-socketio: Manages real-time communication for speech processing

### Initial Setup Steps
1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in .env:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Run the application: `python app.py`

### Troubleshooting Common Issues

#### Virtual Environment Issues
```bash
# If venv module is not found
python -m pip install virtualenv

# If activation fails on Windows
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# If pip is not found in venv
python -m ensurepip --upgrade
```

#### Audio Dependencies Issues
```bash
# On Windows: Install Visual C++ Build Tools
# On Linux: Install system audio dependencies
sudo apt-get install portaudio19-dev python3-pyaudio
sudo apt-get install libasound2-dev

# On macOS: Install portaudio
brew install portaudio
```

## Core Features

### 1. 3D Environment
- Immersive office environment using OpenGL
- Realistic office furniture (desks, chairs, plants)
- Partition walls for different office areas
- Professional color scheme

### 2. Character System
- NPCs with distinct roles (HR, CEO)
- Visually distinct characters
- Proper positioning and scaling
- Character-specific voice settings

### 3. Dialogue System
- Text-based conversation system with OpenAI GPT-4 integration
- Real-time speech-to-text and text-to-speech capabilities
- Conversation history tracking with last 3 messages display
- Dual-mode interaction (text and speech)
- Role-specific NPC responses and personalities
- Speech mode toggle with Shift+T
- ESC key for conversation exit

### 4. Speech System
- Real-time speech recognition using OpenAI's Whisper
- Text-to-speech synthesis for NPC responses
- Voice customization per NPC role:
  - HR: Professional, friendly tone
  - CEO: Authoritative, confident tone
- Speech mode toggle with visual indicator
- Ambient noise adjustment
- Audio queue processing for smooth interaction
- Error recovery for speech processing

### 5. Dynamic Voice System
- Emotion-based voice modulation
- Real-time voice adjustments based on conversation context
- Voice settings for different emotions:
  - Happy: Shimmer voice (speed: 1.1, pitch: 1.1)
  - Sad: Echo voice (speed: 0.9, pitch: 0.9)
  - Angry: Onyx voice (speed: 1.1, pitch: 0.9)
  - Excited: Nova voice (speed: 1.2, pitch: 1.2)
  - Calm: Alloy voice (speed: 1.0, pitch: 1.0)
  - Friendly: Nova voice (speed: 1.0, pitch: 1.1)
  - Authoritative: Onyx voice (speed: 0.9, pitch: 0.9)
- Automatic emotion detection in responses
- Visual emotion indicator in dialogue interface
- Seamless voice transitions between emotions
- Voice interruption handling with clean state reset

### 6. User Interface
- Clean, modern menu system
- Professional dialogue interface
- Visual feedback for system states
- Intuitive control schemes

## Technical Implementation

### 1. Graphics and Rendering
```python
class World:
    def __init__(self):
        self.size = 5
        self.colors = {
            'floor': (0.76, 0.6, 0.42),  # Light wood color
            'walls': (0.85, 0.85, 0.85),  # Light gray
            'desk': (0.6, 0.4, 0.2),     # Brown wood
            'chair': (0.2, 0.2, 0.2),    # Dark grey
            'computer': (0.1, 0.1, 0.1),  # Black
            'plant': (0.2, 0.5, 0.2),    # Green
            'partition': (0.3, 0.3, 0.3)  # Darker gray
        }
    
    def draw(self):
        # Set material properties
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Draw floor
        glBegin(GL_QUADS)
        glColor3f(*self.colors['floor'])
        glNormal3f(0, 1, 0)
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 0, -self.size)
        glEnd()
        
        # Draw office furniture
        self.draw_desk(-4, -2, 90)  # HR Area
        self.draw_desk(4, 1, -90)   # CEO Area
        self.draw_chair(-3.5, -2, 90)
        self.draw_chair(3.5, 1, -90)
        self.draw_plant(-4.5, -4.5)
        self.draw_plant(4.5, -4.5)
```

### 2. Dialogue System Core
```python
class DialogueSystem:
    def __init__(self):
        self.active = False
        self.user_input = ""
        self.npc_message = ""
        self.input_active = False
        self.last_npc_text = ""
        self.conversation_history = []
        self.speech_system = SpeechSystem()
        self.speech_enabled = False
        self.current_npc = None
        self.initial_player_pos = None

    def start_conversation(self, npc_role="HR", player_pos=None):
        """Start a new conversation with an NPC"""
        self.active = True
        self.input_active = True
        self.initial_player_pos = player_pos
        self.current_npc = npc_role
        
        # Add greeting message
        greeting = f"Hello! I'm the {npc_role}. How can I help you today?"
        self.npc_message = greeting
        self.last_npc_text = greeting
        self.conversation_history.append(("NPC", greeting))
        
        # Convert greeting to speech if speech is enabled
        if self.speech_enabled:
            asyncio.run(self.speech_system._text_to_speech(greeting))
```

### 3. Speech Processing
```python
async def _process_speech_input(self, text):
    try:
        # Get response from OpenAI
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

### 4. Dynamic Voice Implementation
```python
class SpeechSystem:
    def __init__(self):
        # Voice settings for different emotions
        self.emotion_voice_mapping = {
            "happy": {"voice": "shimmer", "speed": 1.1, "pitch": 1.1},
            "sad": {"voice": "echo", "speed": 0.9, "pitch": 0.9},
            "angry": {"voice": "onyx", "speed": 1.1, "pitch": 0.9},
            "excited": {"voice": "nova", "speed": 1.2, "pitch": 1.2},
            "calm": {"voice": "alloy", "speed": 1.0, "pitch": 1.0},
            "friendly": {"voice": "nova", "speed": 1.0, "pitch": 1.1},
            "authoritative": {"voice": "onyx", "speed": 0.9, "pitch": 0.9}
        }
        
    def adjust_voice_for_emotion(self, emotion):
        """Adjust voice settings based on detected emotion"""
        if emotion in self.emotion_voice_mapping:
            config = self.emotion_voice_mapping[emotion]
            self.set_npc_voice(config["voice"], config["speed"], config["pitch"])
            print(f"Adjusted voice for emotion: {emotion}")
        else:
            print(f"Unknown emotion: {emotion}, using default voice settings")
            
    async def _get_openai_response(self, text):
        """Get response from OpenAI API with emotion detection"""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an NPC in a game. Respond naturally and include an emotion tag at the start of your response in the format [EMOTION:emotion_name]. Available emotions: happy, sad, angry, excited, calm, friendly, authoritative."},
                    {"role": "user", "content": text}
                ],
                stream=True
            )
            
            full_response = ""
            emotion = None
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Check for emotion tag at the start
                    if not emotion and full_response.startswith("[EMOTION:"):
                        end_tag = full_response.find("]")
                        if end_tag != -1:
                            emotion = full_response[9:end_tag].lower()
                            full_response = full_response[end_tag + 1:].strip()
                            
            if emotion:
                self.adjust_voice_for_emotion(emotion)
                
            return full_response
        except Exception as e:
            print(f"Error getting OpenAI response: {e}")
            return None
```

## Development Process

### Recent Changes and Fixes

#### 1. Enhanced Speech System
- **Challenge**: Speech recognition and synthesis needed improvement
- **Solution**: 
  - Implemented proper audio queue management
  - Added error recovery for speech processing
  - Improved speech-to-text accuracy
  - Enhanced text-to-speech quality
  - Added emotion-based voice modulation
  - Implemented voice interruption handling

#### 2. Dialogue System Improvements
- **Challenge**: Need for better conversation flow and state management
- **Solution**:
  - Added conversation history tracking
  - Implemented proper state cleanup
  - Enhanced NPC role-specific responses
  - Added visual feedback for speech mode
  - Implemented emotion detection and display
  - Added seamless voice transitions

#### 3. 3D Environment Enhancement
- **Challenge**: Creating an immersive office environment
- **Solution**:
  - Implemented realistic office furniture
  - Added proper lighting and materials
  - Created distinct areas for different NPCs
  - Optimized rendering performance
  - Added collision detection
  - Implemented smooth camera controls

## Challenges & Solutions

### 1. Speech Recognition Issues
- **Challenge**: Inconsistent text response display and recognition accuracy
- **Solution**: 
  - Implemented proper audio queue management
  - Added ambient noise adjustment
  - Enhanced error handling and recovery
  - Improved speech-to-text processing
  - Added voice activity detection
  - Implemented automatic gain control

### 2. Dialogue System Integration
- **Challenge**: Seamless integration of text and speech modes
- **Solution**:
  - Unified input processing system
  - Added mode-specific handling
  - Improved state management
  - Enhanced error recovery
  - Implemented emotion-based responses
  - Added visual feedback indicators

### 3. 3D Graphics Performance
- **Challenge**: Maintaining smooth performance with complex 3D environment
- **Solution**:
  - Optimized rendering pipeline
  - Implemented level of detail system
  - Added frustum culling
  - Optimized texture usage
  - Implemented efficient collision detection
  - Added performance monitoring

## Learning Outcomes

### Technical Skills
- Enhanced OpenGL and 3D graphics knowledge
- Improved game development patterns understanding
- Gained AI integration experience
- Advanced audio processing techniques
- Real-time speech processing expertise
- Emotion detection and voice modulation
- Performance optimization techniques

### Design Principles
- Better UX design understanding
- Improved game interface design knowledge
- Enhanced accessibility requirements understanding
- Effective feedback system design
- Voice interaction design patterns
- Emotional response design
- User engagement strategies

### Project Management
- Agile development practices
- Version control best practices
- Documentation standards
- Testing methodologies
- Performance optimization techniques
- User feedback integration

## Future Improvements

### Voice System Enhancements
- More voice customization options
- Advanced emotion detection
- Voice style transfer
- Multi-language support
- Voice cloning capabilities
- Real-time voice effects

### Dialogue System Improvements
- More sophisticated conversation contexts
- Memory of previous interactions
- Personality-based responses
- Multi-turn conversation handling
- Context-aware responses
- Improved error recovery
- Better state management

### Technical Enhancements
- Advanced 3D effects
- More sophisticated AI interactions
- Improved speech recognition accuracy
- Performance optimization
- Enhanced collision detection
- Better lighting system
- Improved texture management

### User Experience
- More customization options
- Tutorial system
- Enhanced accessibility features
- Additional interactive elements
- Better visual feedback
- Improved navigation
- Enhanced immersion

## Voice System Documentation

### NPC Voices
1. **HR NPC**
   - Voice: "nova" (warm, friendly)
   - Speed: 1.0
   - Pitch: 1.1
   - Personality: Approachable, helpful
   - Use Cases: General inquiries, onboarding

2. **CEO NPC**
   - Voice: "onyx" (deep, authoritative)
   - Speed: 0.9
   - Pitch: 0.9
   - Personality: Professional, decisive
   - Use Cases: Strategic discussions, decisions

### Available Voices
```python
voice_settings = {
    "alloy": {"description": "Balanced, neutral voice", "use_case": "General purpose"},
    "echo": {"description": "Clear, articulate voice", "use_case": "Important announcements"},
    "fable": {"description": "Storytelling, expressive voice", "use_case": "Narrative content"},
    "onyx": {"description": "Deep, authoritative voice", "use_case": "Leadership roles"},
    "nova": {"description": "Warm, friendly voice", "use_case": "Customer service"},
    "shimmer": {"description": "Bright, energetic voice", "use_case": "Enthusiastic responses"}
}
```

### Emotion-Based Voice Settings
```python
emotion_voice_mapping = {
    "happy": {"voice": "shimmer", "speed": 1.1, "pitch": 1.1},
    "sad": {"voice": "echo", "speed": 0.9, "pitch": 0.9},
    "angry": {"voice": "onyx", "speed": 1.1, "pitch": 0.9},
    "excited": {"voice": "nova", "speed": 1.2, "pitch": 1.2},
    "calm": {"voice": "alloy", "speed": 1.0, "pitch": 1.0},
    "friendly": {"voice": "nova", "speed": 1.0, "pitch": 1.1},
    "authoritative": {"voice": "onyx", "speed": 0.9, "pitch": 0.9}
}
```

### Key Features
1. **Voice Selection**
   - Automatic voice assignment based on NPC role
   - Dynamic voice parameter adjustment
   - Fallback to default voice if needed
   - Emotion-based voice modulation
   - Real-time voice transitions

2. **Speech Controls**
   - Shift+T: Toggle speech mode
   - SPACE: Interrupt NPC response
   - ESC: Exit conversation
   - Visual feedback for current mode
   - Emotion indicator display

3. **Interruption System**
   - Immediate response to user input
   - Clean audio queue management
   - Smooth state transitions
   - Visual feedback for interruptions
   - Error recovery handling

### Usage Guide
1. Start game
2. Approach NPC (HR or CEO)
3. Press TAB to talk
4. Press Shift+T for speech mode
5. Speak to NPC
6. Press SPACE to interrupt
7. Press ESC to exit
8. Observe emotion indicators
9. Use appropriate emotional prompts
10. Monitor voice changes


