# Design System Strategy: The Intelligent Ethereal

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Curator."** 

Unlike standard AI platforms that lean into cold, robotic efficiency or "gaming" aesthetics, this system treats information as a high-end editorial gallery. We move beyond the "template" look by utilizing intentional asymmetry, expansive negative space, and a focus on "Object Depth." The goal is to make the user feel like they are interacting with a sophisticated, invisible intelligence—one that is creative and mysterious, yet grounded in professional reliability. 

We break the grid through overlapping elements (e.g., a card bleeding into a section header) and a drastic typographic scale that juxtaposes oversized, elegant display type with tightly tracked, utilitarian labels.

---

## 2. Colors & Surface Architecture
The color palette is rooted in a refined light theme, using high-chroma accents (Indigo, Violet, Teal) sparingly to signal intelligence and action.

### The "No-Line" Rule
To maintain a premium feel, **1px solid borders for sectioning are strictly prohibited.** Boundaries must be defined through background color shifts or tonal transitions.
- Use `surface-container-low` (#f2f4f6) sections sitting atop a `surface` (#f7f9fb) background to create a logical break without visual noise.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—stacked sheets of fine paper or frosted glass.
*   **Base Layer:** `surface` (#f7f9fb)
*   **Secondary Sectioning:** `surface-container-low` (#f2f4f6)
*   **Primary Content Cards:** `surface-container-lowest` (#ffffff)
*   **Floating Interactivity:** `surface-bright` (#f7f9fb)

### The "Glass & Gradient" Rule
Standard flat colors feel static. To inject "soul":
*   **CTAs:** Use a subtle linear gradient from `primary` (#4648d4) to `primary-container` (#6063ee) at a 135-degree angle.
*   **Floating Overlays:** Use `surface-container-lowest` with a 70% opacity and a `backdrop-blur` of 20px to create a "Frosted Glass" effect, allowing the accent colors to bleed through softly.

---

## 3. Typography
We use a dual-font strategy to balance the "Creative Mystery" with "Professional Legibility."

*   **Display & Headlines (Manrope):** The "Voice." Used for high-impact moments. Its geometric yet slightly warm curves provide a modern, intelligent feel. Use `display-lg` (3.5rem) with tighter letter-spacing (-0.02em) to create an editorial, high-end look.
*   **Body & Labels (Inter):** The "Workhorse." Chosen for its extreme legibility in complex AI data environments.
*   **Hierarchy Note:** Always maintain a high contrast between headers and body. If a headline is `headline-lg`, the supporting text should skip a level down to `body-md` to create breathing room and clear intent.

---

## 4. Elevation & Depth
Hierarchy is achieved through **Tonal Layering** rather than structural lines.

### The Layering Principle
Depth is created by stacking tiers. Place a `surface-container-lowest` card on a `surface-container-low` section. This creates a soft, natural lift that feels architectural rather than "pasted on."

### Ambient Shadows
For floating elements (Modals, Popovers), shadows must be "Atmospheric":
*   **Shadow Specs:** `0px 20px 40px rgba(25, 28, 30, 0.06)`. 
*   The shadow color is a tinted version of `on-surface`, never pure black, to mimic natural ambient light.

### The "Ghost Border" Fallback
If a border is required for accessibility, use a **Ghost Border**:
*   `outline-variant` (#c7c4d7) at **15% opacity**.
*   **Forbid:** 100% opaque, high-contrast borders.

---

## 5. Components

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary-container`), `xl` (1.5rem) roundedness. Subtle inner-glow (1px white top-stroke at 20% opacity).
*   **Secondary:** `surface-container-highest` background with `primary` text. No border.
*   **Hover State:** Increase shadow spread and shift gradient saturation by 5%.

### Input Fields
*   **Default:** `surface-container-low` background, no border, `md` (0.75rem) roundedness.
*   **Active:** A 2px "Glow" using `primary` at 30% opacity, rather than a solid stroke.

### Cards & Lists
*   **The Divider Rule:** Strictly forbid horizontal line dividers. Use vertical white space (Spacing `6` or `8`) or a subtle shift to `surface-container-lowest` to separate list items.
*   **Rounding:** All cards must use `xl` (1.5rem) or `lg` (1rem) corner radius to feel approachable and modern.

### Contextual AI Component: "The Intelligence Pulse"
A custom component for this system: A small, high-blur teal/violet gradient orb that sits behind AI-generated content or insights, pulsating at a slow "breathing" frequency (4s duration). This signifies "Thinking" or "Insight" without using cliché robot icons.

---

## 6. Do’s and Don’ts

### Do
*   **DO** use extreme white space. If you think there is enough space, add 20% more.
*   **DO** use `tertiary` (Teal) for "Success" or "Discovery" moments to keep the vibe creative.
*   **DO** align text-heavy content to a strict left margin but allow images/cards to break the right margin for an editorial feel.

### Don’t
*   **DON'T** use pure black (#000000) for text. Always use `on-surface` (#191c1e).
*   **DON'T** use "Gaming Neon." Accents should be soft and integrated, not glowing like a futuristic HUD.
*   **DON'T** use 1px dividers. Use the Spacing Scale (Token `3` or `4`) to create "Visual Silences" between content blocks.