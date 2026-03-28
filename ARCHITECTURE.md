# Room2Escape MVP Architecture

## Overview
Room2Escape is a hackathon MVP that turns one uploaded image into a multimodal puzzle experience.

Frontend is a static HTML application styled with Tailwind CSS.
Backend is a Python FastAPI service.
The system uses a multimodal model for scene understanding, an LLM for puzzle generation, an image generation step for the transformed scene, and a voice layer for the host experience.

The architecture is optimized for:
- fast implementation
- clear end to end flow
- minimal moving parts
- reliable demo delivery in about 8 hours



---

## High-Level Flow

1. User opens the HTML app in the browser
2. User uploads one image
3. User selects:
   - theme
   - mode
   - difficulty
4. Frontend sends a multipart request to FastAPI
5. Backend:
   - validates input
   - analyzes the image
   - generates structured puzzle JSON
   - generates or requests a transformed themed image
   - returns one normalized response object
6. Frontend renders:
   - original image preview
   - transformed image
   - title and story
   - object transformations
   - puzzle steps
   - final objective
   - JSON preview (debug mode only)
7. User can:
   - click the transformed image to open a modal
   - trigger voice host actions
   - request a hint
8. If generation fails, frontend routes to a dedicated error page with retry/sample actions

---

## Architecture Style

### Frontend
Static multi-page client-side app:
- index.html (upload/configuration + processing overlay)
- results.html (dashboard + play mode + voice controls)
- error.html (dedicated failure states + recovery actions)
- js/upload.js
- js/results.js
- js/error.js

Responsibilities:
- upload handling
- UI state transitions
- rendering API responses into the DOM
- modal open and close behavior
- voice host button actions
- error handling
- loading state display
- **latency handling:** disable the upload button and prevent double-submissions during the 10-20 second generation window

### Backend
Single FastAPI service (Stateless)

Responsibilities:
- file upload endpoint
- image validation
- orchestration of multimodal analysis
- orchestration of puzzle generation
- orchestration of transformed image generation
- response normalization
- hint generation endpoint (stateless, accepts full context from frontend)
- optional voice context preparation
- **CORS configuration:** explicitly configure CORS middleware to accept all origins during the hackathon phase

---

## Frontend Structure

### Files
- index.html
- results.html
- error.html
- js/upload.js
- js/results.js
- js/error.js
- optional assets folder for sample images and voice audio

### Main UI Sections
- Upload page: Header, Hero/upload form, Loading overlay, Use-cases section, Footer
- Results page: Header, Results dashboard, Generated image modal, Voice host panel, Play mode, Footer
- Error page: Header, error-state cards, recovery actions, technical tips, Footer
- Debug-only: JSON preview section on results page

### Required Frontend States
- idle
- file selected
- loading
- success
- error

### Frontend Responsibilities in Detail

#### Upload and configuration
The frontend collects:
- image file
- theme
- mode
- difficulty

#### Request handling
The frontend sends data to the backend using fetch and FormData.
It must handle long polling or extended timeouts (15+ seconds) gracefully without crashing.

#### Result rendering
The frontend maps response fields into:
- title
- badges
- story
- object transformations
- puzzle list
- final objective
- generated image
- JSON block

#### Modal interaction
The transformed image is clickable.
Hover should show click affordance.
Click opens the enlarged modal.
The modal closes on close button click or background click.

#### Voice actions
The frontend exposes buttons such as:
- Start Voice Host
- Give Me a Hint
- Explain Puzzle Logic

These actions may call:
- Vapi directly
- backend hint endpoint
- or a local pre-generated audio playback fallback with text transcript

---

## Backend Structure

### Recommended Python Project Layout

app
- main.py
- .env
- .env.example
- routers
  - generate.py
  - hint.py
- services
  - image_analysis.py
  - puzzle_generation.py
  - image_transform.py
  - response_normalizer.py
- models
  - request_models.py
  - response_models.py
- utils
  - validators.py
  - logging.py
  - prompts.py (Centralized prompt management)

### Core Backend Responsibilities

#### Secrets Management
Never hardcode API keys. Use the `.env` file for all external integrations (OpenAI, Gemini, Vapi, etc.) and ensure it is included in `.gitignore`. Provide a `.env.example` for the repository.

#### Input validation
Validate:
- file presence
- supported mime type if possible
- theme value
- mode value
- difficulty value

#### Scene analysis
Analyze the uploaded image to extract:
- 3 to 5 visible objects
- approximate scene mood
- possible puzzle anchors

#### Puzzle generation (via prompts.py)
Generate:
- title
- short story
- transformed object roles
- exactly 3 puzzle steps
- final objective
- voice host intro
- transformed image prompt

#### Image transformation
Generate or request one themed transformed image based on:
- uploaded image
- theme
- object mapping
- mood

#### Response normalization
Return one stable JSON object even if model outputs vary.
This normalized object becomes the single source of truth for the frontend.

#### Hint generation (Stateless)
Given the scenario context provided by the frontend, generate:
- one short helpful hint
- or one short spoken explanation

---

## API Design

### POST /api/generate
Purpose:
Generate the complete puzzle experience from one uploaded image.

Input:
- multipart form data
- image
- theme
- mode
- difficulty

Response:
- normalized scenario JSON
- transformed image reference or generated image URL

### POST /api/hint
Purpose:
Return a short hint or explanation for the current puzzle state without requiring the backend to store session data.

Input (JSON):
- scenario_context (the full JSON object previously generated)
- current_step (integer)
- optional user_question (string)

Response:
- short hint text
- optional voice friendly response text

### GET /api/health
Purpose:
Basic service health check for demo readiness.

Response:
- ok status

---

## Canonical Response Object

The backend should return one normalized object like this:

- title
- theme
- mode
- difficulty
- story
- detected_objects
- transformations
- puzzles
- final_escape
- voice_host_intro
- generated_image_url
- transformed_image_prompt

This object is used by:
- the results dashboard
- the JSON preview
- the hint endpoint
- the voice host context

---

## Example Response Shape

title
The Last Study of Hollowmere

theme
Detective

mode
Play

difficulty
Medium

story
You are trapped inside the sealed study of a vanished archivist. Solve the clues hidden in the room to unlock the final mechanism.

detected_objects
- coffee mug
- notebook
- keys
- desk lamp

transformations
- real_object: coffee mug
  game_object: Cauldron of Ash Memory
  puzzle_role: contains the first clue
- real_object: notebook
  game_object: Archivist Journal
  puzzle_role: reveals the hidden symbol

puzzles
- step: 1
  title: Read the Journal
  description: Find the repeated symbol
  hint: Look for the oldest annotation
  solution: The repeated symbol is a triangle
- step: 2
  title: Reveal the Number
  description: Use the lamp to reveal the hidden number
  hint: Light changes what the page reveals
  solution: The number is 3
- step: 3
  title: Order the Seals
  description: Arrange the keys into the final order
  hint: Length determines order
  solution: The order is 3142

final_escape
- objective: Enter the final 4 digit code
- solution: 3142

voice_host_intro
Welcome, explorer. I have reconstructed a puzzle experience from your scene. Begin with the journal.

generated_image_url
generated/scene-001.png

transformed_image_prompt
Transform the uploaded desk scene into a detective style escape room while preserving object layout.

---

## Internal Processing Pipeline

### Step 1
Receive multipart request

### Step 2
Validate inputs

### Step 3
Run scene analysis service
Output:
- objects
- mood
- anchors

### Step 4
Run puzzle generation service
Output:
- structured puzzle experience
- transformed image prompt

### Step 5
Run image transform service
Output:
- generated themed image

### Step 6
Normalize all outputs into one consistent response

### Step 7
Return response to frontend

---

## Frontend and Backend Contract

The frontend should assume:
- one request produces one complete scenario
- the backend returns a ready to render response
- missing optional fields should not break rendering

The backend should assume:
- the frontend is DOM based, not React based
- response keys should remain stable
- concise fields are preferred over deeply nested structures when possible
- the frontend will pass back required context for stateless endpoints (like hints)

---

## Voice Host Architecture

### MVP approach
Keep voice host minimal.

The voice layer should use:
- voice_host_intro
- puzzle titles
- puzzle hints
- final objective

Supported actions:
- Start Voice Host
- Give Me a Hint
- Explain Puzzle Logic

### Practical implementation options
Option 1
Frontend triggers Vapi with scenario context

Option 2
Frontend calls backend hint endpoint and uses a simple voice playback layer

Option 3
Frontend plays pre-generated local audio files mapped to voice actions (mock voice host)

Option 4
Text only fallback if live voice integration or local audio playback fails

Voice is important for theme alignment, but the rest of the app must still work without it.

---

## Error Handling Strategy

### Frontend fallback behavior
If generation fails:
- route to a dedicated error page (`error.html`)
- show contextual error copy and allow retry/sample recovery actions

If transformed image fails:
- still show text results and original image

If voice host fails:
- still show the generated scenario and allow text hints

### Backend fallback behavior
If image transformation fails:
- return textual scenario with a null or empty image field
- do not fail the whole request if avoidable

If model output is malformed:
- retry once or normalize aggressively
- otherwise return a clear generation error

---

## Deployment Model

### Simplest demo setup
Frontend:
- served as static files
- can be opened locally or served by FastAPI static mount

Backend:
- FastAPI running locally or on a lightweight cloud instance

This is enough for a hackathon demo.

---

## Recommended Minimal Stack

### Frontend
- HTML
- Tailwind CSS
- Vanilla JavaScript

### Backend
- Python
- FastAPI
- Uvicorn
- python-dotenv (for secrets management)

### AI and integrations
- multimodal model for image analysis
- LLM for puzzle JSON generation
- image generation or transformation service
- Vapi for voice host if available

---

## Build Priorities

### Priority 0
- static HTML UI works
- upload form works
- generate endpoint works
- response renders into DOM
- transformed image card works
- image modal works
- CORS configured

### Priority 1
- hint endpoint works (stateless implementation)
- voice host intro works
- API keys secured in .env

### Priority 2
- loading state polish (button disabling, timeout protection)
- sample scene fallback
- better error states
- extra use case cards polish

---

## Success Criteria

The MVP is successful if a user can:
1. upload one image
2. choose theme mode and difficulty
3. generate one structured puzzle experience
4. view a transformed themed image
5. click the generated image to enlarge it
6. trigger at least one voice host or hint interaction

That is sufficient for a strong hackathon demo with working code.