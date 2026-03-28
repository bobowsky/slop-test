# Room2Escape — Software Requirements (Hackathon MVP)

## Document Scope
This document defines concise, implementation-oriented requirements for the **Room2Escape** hackathon MVP: a multimodal agent that transforms a real-world photo into a voice-guided puzzle experience.

Format:
- **Requirement ID**
- **Description**

---

## 1. Product & Scope Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-001 | The system shall provide a web-based single-page application named **Room2Escape**. |
| SRS-E2R-002 | The system shall allow a user to upload a real-world scene image as the main input. |
| SRS-E2R-003 | The system shall generate a puzzle experience from the uploaded image using multimodal reasoning. |
| SRS-E2R-004 | The system shall position itself as a **multimodal agent** rather than a static content generator. |
| SRS-E2R-005 | The MVP scope shall focus on a single end-to-end flow: image upload → analysis → puzzle generation → transformed image → voice guidance. |
| SRS-E2R-006 | The system shall support hackathon MVP delivery within a constrained implementation scope of approximately 8 hours. |
| SRS-E2R-007 | The system shall avoid non-essential platform features such as authentication, user accounts, multiplayer, and persistent profiles in the MVP. |

---

## 2. Input & Configuration Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-008 | The system shall provide an image upload control supporting drag-and-drop and click-to-select interactions. |
| SRS-E2R-009 | The system shall accept at least one image file as input per generation request. |
| SRS-E2R-010 | The system shall allow the user to select a **theme** before generation. |
| SRS-E2R-011 | The supported theme options shall include at minimum: Fantasy, Sci-Fi, Horror, and Detective. |
| SRS-E2R-012 | The system shall allow the user to select a **mode** before generation. |
| SRS-E2R-013 | The supported mode options shall include at minimum: Play and Learning. |
| SRS-E2R-014 | The system shall allow the user to select a **difficulty** before generation. |
| SRS-E2R-015 | The supported difficulty options shall include at minimum: Easy, Medium, and Hard. |
| SRS-E2R-016 | The system shall provide a primary call-to-action to start generation. |
| SRS-E2R-017 | The system shall provide a secondary option to use a sample scene instead of uploading a custom image. |
| SRS-E2R-018 | The system shall display a selected-image preview before generation when a file is chosen. |

---

## 3. Application State Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-019 | The system shall visually distinguish the following UI states: idle, file selected, loading, results ready, and error. |
| SRS-E2R-020 | The system shall provide a clear empty state before any image is uploaded. |
| SRS-E2R-021 | The system shall provide a loading state while generation is in progress. |
| SRS-E2R-022 | The loading state shall display a multi-step processing sequence representing multimodal reasoning. |
| SRS-E2R-023 | The loading sequence shall include at minimum the following statuses: scanning scene, detecting puzzle anchors, generating transformed environment, and preparing voice host. |
| SRS-E2R-024 | The system shall display a results state once generation is complete. |
| SRS-E2R-025 | The system shall display an error state when upload or generation fails. |
| SRS-E2R-026 | The error state shall provide a retry option. |

---

## 4. Scene Analysis Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-027 | The system shall analyze the uploaded image using a multimodal model or pipeline. |
| SRS-E2R-028 | The system shall identify at least 3 and at most 5 visible objects from the image for MVP generation. |
| SRS-E2R-029 | The system shall infer an overall scene mood or atmosphere from the uploaded image. |
| SRS-E2R-030 | The system shall identify candidate puzzle anchors from detected objects. |
| SRS-E2R-031 | The system shall use only image-derived objects as the basis for puzzle content generation. |
| SRS-E2R-032 | The system shall represent scene analysis results in structured data suitable for downstream generation. |

---

## 5. Puzzle Experience Generation Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-033 | The system shall generate a titled puzzle experience from the uploaded image. |
| SRS-E2R-034 | The system shall generate a short story summary consistent with the selected theme, mode, and difficulty. |
| SRS-E2R-035 | The system shall transform detected real-world objects into themed puzzle-world roles. |
| SRS-E2R-036 | The system shall generate exactly 3 puzzle steps in the MVP. |
| SRS-E2R-037 | Each puzzle step shall contain a title and a short description. |
| SRS-E2R-038 | Each puzzle step shall include a hint. |
| SRS-E2R-039 | Each puzzle step shall include a solution in the structured output. |
| SRS-E2R-040 | The puzzle steps shall form a logical progression. |
| SRS-E2R-041 | The generated experience shall include one final objective or final escape mechanism. |
| SRS-E2R-042 | The final objective shall resolve to a single clear answer, preferably a code or simple objective. |
| SRS-E2R-043 | The generated content shall remain concise enough for live hackathon demo presentation. |
| SRS-E2R-044 | The generated content shall use only the selected theme, mode, and difficulty values for conditioning. |

---

## 6. Structured Output Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-045 | The system shall generate a structured JSON output representing the puzzle experience. |
| SRS-E2R-046 | The structured JSON shall serve as the source of truth for UI rendering and voice-host context. |
| SRS-E2R-047 | The structured JSON shall include title, theme, mode, difficulty, story, detected objects, transformations, puzzles, final escape, and voice host intro fields. |
| SRS-E2R-048 | The structured JSON shall be displayable in the UI inside a formatted code block when debug mode is enabled. |
| SRS-E2R-049 | In debug mode, the UI shall provide a button to copy the structured JSON. |
| SRS-E2R-050 | In debug mode, the UI shall provide a button to download the structured JSON. |
| SRS-E2R-051 | The backend shall validate or sanitize malformed model output before rendering when feasible. |
| SRS-E2R-052 | If JSON output is invalid, the system shall retry generation or return an actionable error state. |

---

## 7. Visual Transformation Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-053 | The system shall generate one transformed scene image based on the uploaded image and selected theme. |
| SRS-E2R-054 | The transformed image shall reflect a stylized reinterpretation of the uploaded scene rather than a random unrelated image. |
| SRS-E2R-055 | The transformed image generation shall preserve the approximate spatial layout of major objects when feasible. |
| SRS-E2R-056 | The results dashboard shall display both the original uploaded image and the generated transformed image. |
| SRS-E2R-057 | The original image shall be labeled as an input artifact. |
| SRS-E2R-058 | The transformed image shall be labeled as an output artifact. |

---

## 8. Generated Image Interaction Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-059 | The generated transformed image shall be visibly styled as a clickable interactive element. |
| SRS-E2R-060 | On hover over the generated image, the cursor shall change to pointer. |
| SRS-E2R-061 | On hover over the generated image, a visible overlay shall appear containing the text **“Click to enlarge”** or equivalent. |
| SRS-E2R-062 | On hover over the generated image, the card or image shall show a visual affordance such as lift, glow, or scale change. |
| SRS-E2R-063 | The generated image shall include a visible expand or zoom icon affordance. |
| SRS-E2R-064 | Clicking the generated image shall open a modal, popup, or lightbox with an enlarged version of the image. |
| SRS-E2R-065 | The enlarged-image modal shall not be displayed open by default. |
| SRS-E2R-066 | The enlarged-image modal shall dim the page background. |
| SRS-E2R-067 | The enlarged-image modal shall provide a visible close control. |
| SRS-E2R-068 | The enlarged-image modal shall display the transformed image at a larger size than the dashboard card. |

---

## 9. Results Dashboard Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-069 | The system shall display the generated output in a structured results dashboard layout. |
| SRS-E2R-070 | The results dashboard shall include an overview card containing title, theme, mode, difficulty, story summary, and final objective. |
| SRS-E2R-071 | The overview card shall include a status indicator such as “Ready to Play.” |
| SRS-E2R-072 | The results dashboard shall include an object transformations section. |
| SRS-E2R-073 | The object transformations section shall display each transformation as real object → transformed role → puzzle function. |
| SRS-E2R-074 | The results dashboard shall include a puzzle progression section. |
| SRS-E2R-075 | The puzzle progression section shall visually present Puzzle 1, Puzzle 2, Puzzle 3, and Final Escape as a guided sequence. |
| SRS-E2R-076 | The puzzle progression section shall support concise hint and dependency presentation. |
| SRS-E2R-077 | The results dashboard shall be renderable directly from the structured JSON response. |

---

## 10. Voice Host / Agent Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-078 | The system shall include a Voice Host feature integrated via Vapi or an equivalent voice interaction layer. |
| SRS-E2R-079 | The Voice Host shall be presented as a functional agent control panel in the UI. |
| SRS-E2R-080 | The Voice Host panel shall provide a “Start Voice Host” action. |
| SRS-E2R-081 | The Voice Host shall be able to deliver an introductory narration based on the generated puzzle experience. |
| SRS-E2R-082 | The Voice Host panel shall provide a “Give Me a Hint” action. |
| SRS-E2R-083 | The Voice Host panel shall provide an “Explain Puzzle Logic” action. |
| SRS-E2R-084 | The Voice Host responses shall be grounded in the generated structured puzzle data. |
| SRS-E2R-085 | The Voice Host shall behave as an interactive agent rather than a decorative voice widget. |
| SRS-E2R-086 | The system shall support at least a minimal voice-host interaction flow sufficient for demo use. |
| SRS-E2R-087 | If full conversational voice interaction is unavailable, the system may support button-triggered voice actions as an MVP fallback. |

---

## 11. UI & UX Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-088 | The system shall provide a responsive web interface using a multi-page MVP flow. |
| SRS-E2R-089 | On desktop, the results section shall support a split or bento-style layout separating visuals and logic/data. |
| SRS-E2R-090 | On mobile, the layout shall collapse into a single-column arrangement. |
| SRS-E2R-091 | On mobile, visual cards shall appear before detailed data cards where feasible. |
| SRS-E2R-092 | The primary generation CTA shall remain visually prominent across screen sizes. |
| SRS-E2R-093 | The interface shall use a light-theme design with high legibility and accessible contrast. |
| SRS-E2R-094 | The interface shall avoid an overly dark, neon, or cluttered gaming aesthetic. |
| SRS-E2R-095 | The interface shall use reusable UI components such as cards, buttons, badges, timeline items, code blocks, and modal dialogs. |
| SRS-E2R-096 | The interface shall provide explicit hover and active states for interactive elements. |
| SRS-E2R-097 | The interface shall use realistic placeholder content rather than lorem ipsum during design/mock data states. |

---

## 12. Error Handling Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-098 | The system shall provide an error state for unsupported image input. |
| SRS-E2R-099 | The system shall provide an error state for upload failure. |
| SRS-E2R-100 | The system shall provide an error state for puzzle generation failure. |
| SRS-E2R-101 | The system shall provide an error state for transformed image generation failure. |
| SRS-E2R-102 | If transformed image generation fails, the system shall continue to display textual puzzle results when available. |
| SRS-E2R-103 | If voice-host functionality fails, the system shall continue to display the rest of the results dashboard when available. |
| SRS-E2R-104 | Error messages shall use concise, user-friendly wording with a recovery action where possible. |
| SRS-E2R-105 | The system shall allow the user to retry generation after a recoverable failure. |

---

## 13. API & Integration Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-106 | The frontend shall be structured so it can be wired to a Python backend. |
| SRS-E2R-107 | The system shall expose a generation API endpoint that accepts an uploaded image and configuration values. |
| SRS-E2R-108 | The generation API request shall include theme, mode, and difficulty values. |
| SRS-E2R-109 | The generation API response shall include the structured puzzle data required by the UI. |
| SRS-E2R-110 | The generation API response shall include a reference to the transformed image or the data required to render it. |
| SRS-E2R-111 | The system shall expose a hint or voice-context endpoint, or equivalent server-side function, for the Voice Host. |
| SRS-E2R-112 | The frontend components shall be organized so that response fields can be mapped directly into cards, lists, timelines, and code blocks. |
| SRS-E2R-113 | The system shall support integration with Vapi for voice-agent behavior. |
| SRS-E2R-114 | The system shall support integration with a multimodal model stack for image analysis and content generation. |

---

## 14. Real-World Impact Framing Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-115 | The system shall present at least one section describing real-world use cases beyond entertainment. |
| SRS-E2R-116 | The use-case section shall include at minimum classrooms, museums, teams, and families. |
| SRS-E2R-117 | The UI shall communicate that the product can support learning, engagement, and collaboration scenarios. |
| SRS-E2R-118 | The product presentation shall frame the system as an interactive multimodal experience tool rather than only a story generator. |

---

## 15. Demo & Hackathon Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-119 | The MVP shall be capable of a stable end-to-end demo using either custom uploads or prepared sample images. |
| SRS-E2R-120 | The team shall prepare at least one sample image for fallback demo use. |
| SRS-E2R-121 | The MVP shall prioritize working code over non-functional conceptual scope. |
| SRS-E2R-122 | The MVP shall demonstrate multimodal reasoning through visible input-output transformation. |
| SRS-E2R-123 | The MVP shall demonstrate agent behavior through voice interaction or button-triggered voice guidance. |
| SRS-E2R-124 | The MVP shall be concise enough to demo effectively in approximately 90–120 seconds. |

---

## 16. Non-Goals / Explicit Scope Exclusions

| Requirement ID | Description |
|---|---|
| SRS-E2R-125 | The MVP shall not require user authentication or account management. |
| SRS-E2R-126 | The MVP shall not require persistent storage of user sessions. |
| SRS-E2R-127 | The MVP shall not require multiplayer or collaborative real-time gameplay. |
| SRS-E2R-128 | The MVP shall not require more than one uploaded scene per generation flow. |
| SRS-E2R-129 | The MVP shall not require more than 3 puzzle steps. |
| SRS-E2R-130 | The MVP shall not require advanced game simulation, inventory systems, or combat systems. |
| SRS-E2R-131 | The MVP shall not require complex admin tooling, analytics dashboards, or production-grade user management. |

---

## 17. Optional Stretch Requirements

| Requirement ID | Description |
|---|---|
| SRS-E2R-132 | The system may support hotspot markers on the original image for detected objects or puzzle anchors. |
| SRS-E2R-133 | The system may support theme regeneration for the same uploaded scene. |
| SRS-E2R-134 | The system may support separate Player View and Host View modes. |
| SRS-E2R-135 | The system may support additional sample scenes. |
| SRS-E2R-136 | The system may support richer voice-host conversational behavior if time permits. |

---