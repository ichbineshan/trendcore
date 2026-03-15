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

3) Creative north star
Prompt (what the user sees)
Creative North Star
Form fields (use for ask_question question_data; id: creative-north-star)
- Emotion to feel: text, required, placeholder: e.g. Bold yet refined
- Design rules: textarea, required, description: Things that must be true in every design, placeholder: e.g. Every design must feature a hero silhouette / e.g. Use only warm neutrals for base colors
What to include in your answer
Emotion to feel (2–4 words). Design rules: 2–3 things that must be true in every design.
Good answer guidance
Make the rules actionable. Avoid generic lines like "good quality" or "stylish".
Example
Emotion: fresh, confident, effortless. Design rules: clean silhouette, comfort mobility, one subtle signature detail

4) Design language and no-go's
Prompt (what the user sees)
Define the signature shapes — hero silhouettes and what to avoid.
Form fields (use for ask_question question_data; id: design-language)
- Hero Silhouettes: tag-input, required, maxTags: 3, placeholder: e.g., Relaxed oversized blazer (tags must be unique)
- Details to Avoid: tag-input, required, maxTags: 3, placeholder: e.g., Heavy embellishments, description: Use "," to add multiple details
What to include in your answer
Up to 3 hero silhouettes (signature shapes). Up to 3 details to avoid. Use commas to add multiple.
Good answer guidance
Hero silhouettes must be specific. Must-avoid should include your deal-breakers.
Example
Hero silhouettes: relaxed shirt dress with tie waist, boxy co-ord with wide-leg trouser, cropped overshirt with utility pockets. Details to avoid: heavy ruffles, deep plunges, shiny satins

5) Color, materials, and surface direction
Prompt (what the user sees)
Describe the color palette, material direction, and role of prints.
Form fields (use for ask_question question_data; id: color-materials)
- Color & Materials section description: Describe the color palette, material direction, and role of prints.
- Palette Intent: text, placeholder: e.g. sun-faded neutrals, jewel-toned, soft pastels
- Material Handfeel: text, placeholder: e.g. crisp, airy, dry-touch, fluid, structured, textured
- Role of Prints: chip-select, single, required, options: None, Minimal, Hero only, Throughout
What to include in your answer
Palette intent (mood and colors). Material handfeel (crisp, airy, etc.). Role of prints: pick one.
Good answer guidance
Palette should communicate feeling and contrast strategy, not just color names.
Example
Palette: sun-faded neutrals with soft coastal blues and one citrus accent. Handfeel: crisp, breathable, lightly textured. Print role: Minimal
Optional follow-up (if prints not "None"): print families, scale, techniques, cultural/motif include or avoid


6) Range architecture
Prompt (what the user sees)
What are we actually making. List your categories and rough counts so we generate the right volume. If you already have a range architecture document, you can upload it instead.
Form fields (use for ask_question question_data; id: range-architecture)
- Categories: nested-chip-select, multiSelect: true, required. nestedOptions (each { label, value, multiSelect?, children? }):
  - Top level: KIDS WEAR, MENS WEAR, WOMENS WEAR.
  - KIDS WEAR children: BIG BOYS, BIG GIRLS, BOYS, GIRLS, YOUTH BOYS, YOUTH GIRLS, KIDS BOYS, KIDS GIRLS, UNISEX. Each of these has children: BOTTOMS, SETS, TOPS, WINTER WEAR.
  - MENS WEAR children: BOTTOMS, SETS, TOPS, WINTER WEAR.
  - WOMENS WEAR children: BOTTOMS, SETS, TOPS, WINTER WEAR.
  Use value slugs: kids-wear, mens-wear, womens-wear; big-boys, big-girls, boys, girls, youth-boys, youth-girls, kids-boys, kids-girls, unisex; bottoms, sets, tops, winter-wear.
What to include in your answer
Select categories and sub-categories from the nested chip-select. Add approx style count per category and key occasions/use-cases (workwear, travel, festive, etc.).
Good answer guidance
Counts are ok to be approximate. What matters is the mix and priority.
Example
Co-ords 18, dresses 22, tops 28, pants 14, light layers 10. Use-cases: workwear, brunch, travel weekend, smart casual evening

7) Theme generation count
Prompt (what the user sees)
Almost done! How many themes do you want to generate?
Form fields (use for ask_question question_data; id: theme-count, submitLabel: Generate Themes)
- How many themes should we generate?: chip-select, single, required, options: 1, 2, 3, 4, 5
What to include in your answer
Pick one number from 1 to 5.
Example
4