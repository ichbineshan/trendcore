Collection Brief Questions
1) Collection snapshot
Prompt (what the user sees)
In 1–2 lines, tell me what collection we're building. This sets the base context for everything that follows.
Form fields (use for ask_question question_data; id: collection-snapshot)
- Line: chip-select, single, required, options: Women, Men, Kids
- Season: chip-select, single, required, options: Spring/Summer, Fall/Winter, Resort/Cruise, Pre-Fall, Holiday, Year-Round
- Year: chip-select, single, optional, options: 2025, 2026, 2027
- Target Regions: chip-select, multi, optional, options: India, UAE, USA, UK, Europe, South Asia, Southeast Asia, Global
What to include in your answer
Line (pick one), Season + year (eg SS26, AW26), launch window (eg May–June 2026, capture only), target regions (confirm from options).
Good answer guidance
Keep it factual and short, no story yet.
Example
Women, SS26, May–June 2026, India + SEA

2) Customer persona
Prompt (what the user sees)
Who are we designing for? Select the customer segment or describe your target persona.
Form fields (use for ask_question question_data; id: customer-persona)
- Select customer segments: chip-select, multi, required, options: Teen / Youth (~13-17), Young Men (~18-30), Core Men (~25-50), Mature Men (~50+), Big & Tall (all ages)
- Or describe your persona: textarea, optional, placeholder: Describe your target customer persona in your own words
What to include in your answer
Select one or more customer segments (required). Optionally add a short description of the persona, lifestyle, or preferences.
Good answer guidance
Avoid "everyone" or "general audience". A specific customer leads to better outputs.
Example
Teen / Youth, Young Men; or: Urban working women who want comfort-first but polished outfits for office + after-work plans

3) Target age
Prompt (what the user sees)
What age group is this collection primarily for. This helps us calibrate styling, fit, and trend intensity.
What to include in your answer
One primary age range
For Kids, share age in years
Good answer guidance
Pick the main range first. If you truly need two ranges, mention the primary and secondary.
Example
Primary: 25–34

4) Creative north star
Prompt (what the user sees)
Now define the "feel" and the non-negotiables. These are rules the AI will follow while generating themes, moodboards, designs, and artworks.
What to include in your answer
Emotion to feel (2–4 words)
Examples: fresh, confident, playful, calm, bold, elevated
Absolutely true in every design (2–3 rules)
Think: the collection DNA that should show up in every piece
Good answer guidance
Make the rules actionable. Avoid generic lines like "good quality" or "stylish".
Example
Emotion: fresh, confident, effortless
Always true: clean silhouette, comfort mobility, one subtle signature detail

5) Range architecture
Prompt (what the user sees)
What are we actually making. List your categories and rough counts so we generate the right volume. If you already have a range architecture document, you can upload it instead.
What to include in your answer
Categories you want in the collection
Approx style count per category (doesn't need to be perfect)
Key occasions and use-cases
Examples: workwear, travel, festive, casual weekends, school, play
Good answer guidance
Counts are ok to be approximate. What matters is the mix and priority.
Example
Co-ords 18, dresses 22, tops 28, pants 14, light layers 10
Use-cases: workwear, brunch, travel weekend, smart casual evening

6) Fit guardrails
Prompt (what the user sees)
Tell me sizing and fit intent by category so the outputs don't feel wrong or unusable. This prevents issues like too tight fits, wrong proportions, or incorrect ease.
What to include in your answer
Size range (select sizes like XS, S, M, L, XL, XXL)
Fit intent by category
Fit words to use: relaxed, regular, boxy, straight, tapered, oversized, comfort-fit
Good answer guidance
Match fit to climate and customer lifestyle. If you want "relaxed but polished", say so.
Example
Sizes: XS–XXL
Dresses relaxed with optional waist definition
Tops easy fit, slightly boxy
Pants high-rise straight or wide
Layers cropped or hip-length, light and structured

7) Design language and no-go's
Prompt (what the user sees)
Define your signature shapes and what we should never generate. This keeps the collection consistent and avoids irrelevant outputs.
What to include in your answer
3 hero silhouettes (the signature shapes)
Example formats: "relaxed shirt dress with tie waist", "boxy co-ord with wide-leg trouser"
3 details to avoid completely
Examples: heavy ruffles, deep plunges, shiny satin, loud logos
Must-avoid list (hard constraints)
Examples: no sheer fabrics, no bodycon, no synthetic fibers, no heavy embellishment
Good answer guidance
Hero silhouettes must be specific. Must-avoid should include your deal-breakers.
Example
Hero silhouettes: relaxed shirt dress with tie waist, boxy co-ord with wide-leg trouser, cropped overshirt with utility pockets
Avoid details: heavy ruffles, deep plunges, shiny satins
Must-avoid: no sheer fabrics, no bodycon, no heavy embellishment, no large logos, no synthetic fibers

8) Color, materials, and surface direction
Prompt (what the user sees)
Describe the look and tactile feel. This guides palette selection, fabric recommendations, and surface design like prints, embroidery, and embellishment.
What to include in your answer
Palette intent in plain words
Describe mood: sun-faded, jewel-toned, stormy, soft pastels, monochrome
Material handfeel direction
Words like: crisp, airy, dry-touch, fluid, structured, textured
Role of prints in the collection
Choose one: none, minimal, hero-only, print-led
If possible, add a rough % like 15–20%
Good answer guidance
Palette should communicate feeling and contrast strategy, not just color names.
Example
Palette: sun-faded neutrals with soft coastal blues and one citrus accent
Handfeel: crisp, breathable, lightly textured, structured drape
Print role: minimal, hero-only around 15–20%
Only if prints are not "none", answer these
Print families allowed (eg stripes, botanicals, geometrics, watercolor)
Print scale preference (micro, medium, oversized, mixed)
Techniques allowed (screen print, embroidery, applique, foil)
Cultural/motif include or avoid (avoid religious motifs, avoid slogans, etc)
Example
Families: watercolor stripes, abstract botanical linework, minimal geometrics
Scale: micro and medium, one oversized hero max
Techniques: screen print yes, light embroidery yes, foil no, heavy beadwork no
Motifs: subtle craft cues ok, avoid religious motifs

9) References and assets
Prompt (what the user sees)
Share references that represent what "right" looks like. This helps us match your taste accurately. After that, upload your logo and reference images.
What to include in your answer
At least 3 references
Tag each reference with what it represents
Tags: silhouette, detailing, styling, palette, print
Good answer guidance
References without tags often get interpreted incorrectly. Tags make it precise.
Example
Ref 1 silhouette: relaxed shirt dress tie waist
Ref 2 detailing: pocket geometry + topstitch
Ref 3 styling: airy layering proportions
Uploads
Compulsory: brand logo, reference images
Optional: past bestsellers, competitor screenshots, fabric swatches, print artwork, brand guideline

10) Theme generation count
Prompt (what the user sees)
How many different theme directions do you want to explore. More themes gives variety, fewer themes gives speed and tighter focus.
What to include in your answer
Pick one number: 1, 2, 3, 4, 5
Example
3
