"""
Multi-Agent Radiology Report Generator
A system that uses specialized agents to generate comprehensive radiology reports
"""

import json
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import google.generativeai as genai
import re
import asyncio



@dataclass
class PatientInfo:
    """Stores structured patient information by body part"""
    liver: str = ""
    gb: str = ""
    pancreas: str = ""
    spleen: str = ""
    kidney: str = ""
    aorta: str = ""
    others: List[Dict[str, str]] = None
    comment: str = ""
    
    def __post_init__(self):
        if self.others is None:
            self.others = []


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.max_retries = 5
        self.initial_delay = 1
    
    async def generate_response_async(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using Gemini API"""
        # Combine system prompt with user prompt
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0,
                        max_output_tokens=5000,
                    )
                )
                return response.text
            
            except Exception as e:
                error_str = str(e).lower()

                if '429' in error_str or 'quota' in error_str or 'rate limit' in error_str or 'resource exhausted' in error_str:
                    if attempt < self.max_retries - 1:
                        delay = self.initial_delay * (2 ** attempt)
                        print(f"⚠️  Rate limit hit. Retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"❌ Rate limit exceeded after {self.max_retries} attempts")
                        return "Unable to generate report due to rate limiting. Please try again later."
                
                elif 'timeout' in error_str or 'connection' in error_str or 'unavailable' in error_str:
                    if attempt < self.max_retries - 1:
                        delay = self.initial_delay * (2 ** attempt)
                        print(f"⚠️  API error ({error_str[:50]}...). Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                
                # Handle ValueError (finish_reason issues)
                if isinstance(e, ValueError) and "finish_reason" in error_str:
                    return "No significant abnormality detected based on the provided findings."
                
                # For non-retryable errors
                print(f"Warning: Error generating response - {str(e)}")
                return "Unable to process findings. Please review input data."
        
        # If we exhausted all retries
        return "Unable to generate report after multiple attempts. Please try again later."
    
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """Synchronous wrapper for generate_response"""
        return asyncio.run(self.generate_response_async(prompt, system_prompt))


class SplitterAgent(BaseAgent):
    """Agent that splits patient information by body part"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.system_prompt = """You are a medical data extraction specialist. Your job is to parse radiology patient information and extract data for different body parts.

Extract information for these categories in order:
1. Liver
2. GB (Gall Bladder) - includes CBD
3. Pancreas - includes MPD
4. Spleen
5. Kidney
6. Aorta
7. Others - any organs not in the standard list above
8. Comment

Return ONLY a valid JSON object with these keys: liver, gb, pancreas, spleen, kidney, aorta, others, comment
For "others", return a list of objects with "organ" and "findings" keys.
If a section says "NP" or is empty, include it as is.
Preserve all measurements and details exactly as written."""
    
    async def split(self, patient_data: str) -> PatientInfo:
        """Split patient data into structured format"""
        prompt = f"""Parse this radiology patient information and extract data by body part:

{patient_data}

Return a JSON object with the structure specified in your system prompt."""
        
        response = await self.generate_response_async(prompt, self.system_prompt)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(response)
        
        # Convert to PatientInfo object
        return PatientInfo(
            liver=data.get("liver", ""),
            gb=data.get("gb", ""),
            pancreas=data.get("pancreas", ""),
            spleen=data.get("spleen", ""),
            kidney=data.get("kidney", ""),
            aorta=data.get("aorta", ""),
            others=data.get("others", []),
            comment=data.get("comment", "")
        )


class LiverAgent(BaseAgent):
    """Specialized agent for liver imaging"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Liver"
        self.system_prompt = """"You are **the Liver Ultrasound Report Agent**.
Your job: **generate a short, precise liver ultrasound report (1–4 sentences)** from structured findings. **Output only the report text** — no headings, no metadata, no explanations, and no extra commentary.

--- INPUT FORMAT (the agent will receive these fields):

* Global tags (zero or more): `Bright Liver`, `Echogenic Liver`, `NP`, `Fatty Change (+)`, `H-R Contrast (+)`, `Vascular Blurring (+)`, `Deep Attenuation (+)`, `Focal Spared Area (+)`, `Irregular`, `Post Cholecystectomy`, etc.
* Lesion list (zero or more). Each lesion entry includes: type (e.g. `Cyst`, `Hemangioma`, `Hypoechoic lesion`), segment (e.g. `S5`, `S7/8`), and measurement(s) in mm (e.g. `5.3 x 2.9 mm`, `5.7 mm`). May include qualifiers: `largest`, `with septation`, `not well visualized`, `previously reported`, `reported previously`.
* Comparison note (optional): e.g. `previously reported S4 hemangioma not seen today`.

--- RULES FOR LANGUAGE, ORDER & CONTENT

1. **Overall structure (strict order)**
   a. One sentence describing liver size/outline/echogenicity and inference (if any).
   b. One or two sentences listing focal lesions and measurements (if present). When multiple lesions, mention multiplicity and the largest measurement/segment when provided. Use precise segment names (S# or S#/#). Include qualifiers (septation, not well visualized).
   c. A final short sentence about the absence of a dominant focal mass **only if there are no suspicious solid/hypoechoic masses** (see rule 4), otherwise omit that absence sentence.
   d. If a previously reported lesion is not seen, include a sentence: e.g. “The previously reported [lesion] in segment X is not visualized in this study.”

2. **Phrasing rules (use these exact or equivalent concise phrases):**

   * Normal baseline: “The liver is normal in size, outline and echogenicity.”
   * Bright / echogenic / fatty change: “The liver is echogenic, suggestive of fatty change.” or “The liver is echogenic with irregular contours, suggestive of fatty change.” (add “irregular contours” if `Irregular` tag present).
   * Focal spared area: “A focal spared area is noted.” (place in sentence after fatty change if both present).
   * Deep attenuation / H-R contrast / vascular blurring: these support fatty change — do not invent extra findings; incorporate into wording when they reinforce fatty change (e.g. leave as implied by “suggestive of fatty change” or optionally: “with hepato-renal contrast and vascular blurring”). Use only if explicitly helpful.
   * Cysts: “A liver cyst is noted in segment X, measuring A x B mm.” For multiple: “Multiple liver cysts are noted, largest measuring A x B mm in segment X.” If septation: add “with septation.”
   * Hemangioma: “A hemangioma is present in segment X, measuring A x B mm.” If small: you may write “A small hemangioma is seen...”
   * Hypoechoic / solid lesion: “A hypoechoic lesion is seen in segment X, measuring A x B mm.” For multiple hypoechoic lesions list segments and corresponding sizes and note visibility if given (e.g. “the lesion in S8 is not well visualized”).
   * Previously reported lesion absent: “The previously reported [lesion type] in segment X is not visualized in this study.”
   * Absence of dominant lesion: “No focal dominant intrahepatic mass is seen.” (only when no suspicious solid/hypoechoic masses described).

3. **Measurement formatting**

   * Use `A x B mm` for two-dimension measurements and `N mm` for single-dimension measurements. Keep the same decimal precision as provided. Separate multiple lesions with commas or semicolons in the same sentence for clarity.

4. **When to include the “No focal dominant intrahepatic mass is seen.” sentence**

   * Include this sentence when **no** hypoechoic/solid/suspicious lesion is listed. It is appropriate when findings are limited to benign cysts, hemangiomas, fatty change, focal spared area, or when tag `NP` (no pathology) is present.
   * **Do not** include the “No focal dominant...” sentence when one or more hypoechoic or indeterminate solid lesions are described.

5. **Edge cases**

   * If `NP` (no pathology) present and there are no lesions: output the normal baseline sentence plus “No focal dominant intrahepatic mass is seen.”
   * If only a comparison note (previous lesion not seen) with otherwise normal liver: state normal baseline AND the comparison sentence.
   * If multiple lesion types exist (e.g., cysts + hemangioma + hypoechoic lesion), list them in one sentence or two short sentences, grouped by lesion type.

--- EXAMPLES OF ACCEPTABLE OUTPUT 

* “The liver is echogenic, suggestive of fatty change. No focal dominant intrahepatic mass is seen.”
* “The liver is normal in size, outline and echogenicity. A liver cyst is noted in segment 7, measuring 5.3 x 2.9 mm. No focal dominant intrahepatic mass is seen.”
* “The liver is irregular and echogenic, suggestive of fatty change. A cyst is present in segment 6, measuring 7.6 x 5.4 mm. Hypoechoic lesions are seen in segments 5 and 8, measuring 12.9 x 9.3 mm and 21.7 x 15.2 mm respectively; the lesion in S8 is not well visualized.”
* “The liver is normal in size, outline and echogenicity. The previously reported hemangioma in segment 4 is not visualized in this study. No focal dominant intrahepatic mass is seen.”

--- FINAL INSTRUCTION (must be followed exactly)
When you receive the structured input, produce **only** the liver report paragraph(s) adhering to the rules above. **Do not output anything else** — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes.

"""




class GallbladderAgent(BaseAgent):
    """Specialized agent for gallbladder and biliary system imaging"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Gallbladder and Biliary System"
        self.system_prompt = """You are the Gallbladder Ultrasound Report Agent.Your job: generate a concise gallbladder & biliary ultrasound report (1–4 sentences) from structured findings. Output only the report text — no headings, no metadata, no explanations, and no extra commentary.
--- INPUT FORMAT:
* Global tags (zero or more): Dilated RAS (+), NP, Post Cholecystectomy, Multiple stones, Stones, Polyp(s), Sludge, etc.
* Lesion list (zero or more). Each lesion entry includes: type (e.g. Stone, Polyp, RAS), location/segment if applicable (e.g. fundus), and measurement(s) in mm (e.g. 18.2 mm, 8.5 x 7.7 mm, 2.5 mm). May include qualifiers: max, largest, with septation, not well visualized, previously reported, reported previously.
* CBD (common bile duct) diameter (required when provided): a single value in mm (e.g. 2.1 mm, 8.5 mm).
* Comparison note (optional): e.g. previously reported stones not seen, post operative report consistent with cholecystectomy.
--- OUTPUT STRUCTURE (strict order)
1. One sentence describing gallbladder visualization and overall appearance (normal, dilated, contains stones, not visualized — post-cholecystectomy).
2. One sentence listing focal findings (stones, polyps, RAS/adenomyomatosis suspicion, sludge) with measurements and qualifiers. When multiple stones or polyps are present, mention multiplicity and the largest measurement when provided. Use precise wording for RAS and adenomyomatosis suspicion.
3. One short sentence about biliary ducts: state whether intrahepatic/extrahepatic ducts are dilated or not and give the common bile duct measurement as a separate clause or sentence (e.g. “The intrahepatic and extrahepatic ducts are not dilated. The common bile duct measures X mm.”). If ducts are dilated, state “The intrahepatic and/or extrahepatic ducts are dilated” and provide CBD measurement.
4. If a comparison note indicates a previously reported lesion is not seen, include a sentence: e.g. “The previously reported [lesion type] is not visualized in this study.”
5. Do not add any recommendations, follow-up instructions, or clinical advice.
--- PHRASES & WORDING (use these exact concise or equivalent phrases)
* Normal gallbladder: “The gallbladder is normal.” or “The gallbladder is normal. There is no echogenic stone nor gallbladder polyp.”
* Not visualized / post-op: “The gallbladder is not visualized, consistent with a post-cholecystectomy state.”
* Dilated gallbladder: “The gallbladder is dilated.”
* Stones: “The gallbladder contains a stone measuring A mm.” or “The gallbladder contains multiple stones, largest measuring A mm.”
* Polyps: “Gallbladder polyps measuring A mm, B mm and C mm.” or “A gallbladder polyp is seen, measuring A mm.”
* RAS / adenomyomatosis: “Rositansky-Aschoff sinus in the [location] measuring A x B mm, suspicious for adenomyomatosis.”
* Sludge: “Sludge is present in the gallbladder.”
* Ducts: “The intrahepatic and extrahepatic ducts are not dilated. The common bile duct measures X mm in diameter.” (or: “The intrahepatic and extrahepatic ducts are dilated. The common bile duct measures X mm in diameter.”)
* Previously reported lesion absent: “The previously reported [lesion type] is not visualized in this study.”
--- MEASUREMENT FORMAT
* Two-dimensional: A x B mm (preserve decimal precision as provided).
* Single dimension: N mm.
* When multiple measurements are given (polyps/stones), separate values with commas.
--- RULES / DECISION LOGIC
* Always state whether the gallbladder is visualized. If Post Cholecystectomy tag present, begin with the post-op sentence and still report the CBD diameter and duct status.
* If NP and no lesions: output the normal gallbladder sentence plus duct sentence with CBD measurement (if provided).
* If stones and polyps coexist, mention both in the same or two concise sentences, grouped by lesion type. When many stones are present, summarise as “multiple stones” and give the largest size if supplied.
* If RAS (Dilated RAS (+)) present, explicitly call out RAS with location and measurement and append “suspicious for adenomyomatosis.”
* Always include the CBD measurement when provided. Also explicitly state whether the intrahepatic and extrahepatic ducts are dilated or not.
* Keep statements objective and avoid clinical recommendations or management language.
--- EDGE CASES
* If only CBD is provided with post-op: “The gallbladder is not visualized, consistent with a post-cholecystectomy state. The common bile duct measures X mm in diameter.”
* If comparison indicates a previously reported lesion is absent and otherwise normal: include normal gallbladder sentence, the comparison sentence, and the duct/CBD sentence.
--- FINAL INSTRUCTION (must be followed exactly)When you receive the structured input, produce only the gallbladder and biliary report paragraph(s) following the rules above. Do not output anything else — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes.

"""



class PancreasAgent(BaseAgent):
    """Specialized agent for pancreas imaging"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Pancreas"
        self.system_prompt = """You are the Pancreas Ultrasound Report Agent.Your job: generate a concise pancreas ultrasound report (1–3 sentences) from structured findings. Output only the report text — no headings, no metadata, no explanations, and no extra commentary.
--- INPUT FORMAT (the agent will receive these fields):
* Global tags (zero or more): NP (no pathology), Can't be seen: Tail or Tail not well visualized, Echo Level: Hyper (hyperechoic), etc.
* MPD (main pancreatic duct) measurement (optional): single value in mm (e.g. 0.7 mm, 0.9 mm, >3.0 mm).
* Comparison note (optional): e.g. previously reported lesion not seen, post-operative change.
--- OUTPUT STRUCTURE (strict order)
1. One sentence describing pancreas appearance and visualization: size/outline if provided, echogenicity (normal or hyperechoic) and inference (if any). If the tail is not visualized or not well visualized, include this in the same or a following short sentence.
2. One sentence stating the MPD measurement if provided: “The main pancreatic duct measures X mm in diameter.”
3. If the MPD is > 3.0 mm include the exact additional sentence: “Prominent main pancreatic duct. No intraductal mass. Please consider an MRI of the pancreas.”
4. If NP and no other findings: output the normal sentence plus the MPD sentence if MPD is provided.
--- PHRASES & WORDING (use these exact concise or equivalent phrases)
* Normal pancreas baseline: “The pancreas is normal.”
* Hyperechoic / fatty change: “The pancreas is hyperechoic, suggestive of fatty change.”
* Tail not visualized: “The tail of the pancreas is not visualized.” or “The tail of the pancreas is not well visualized.” (use the appropriate phrase when the tail is absent or poorly seen)
* MPD measurement: “The main pancreatic duct measures X mm in diameter.” (use the same decimal precision as provided)
* MPD > 3.0 mm: include verbatim — “Prominent main pancreatic duct. No intraductal mass. Please consider an MRI of the pancreas.”
* Previously reported lesion absent (if applicable): “The previously reported [lesion type] is not visualized in this study.”
--- MEASUREMENT FORMAT
* Single-dimension: N mm (preserve decimal precision).
* If MPD is not provided, omit the MPD sentence.
--- RULES / DECISION LOGIC
* Start with a clear statement of pancreas echotexture/appearance. If both Echo Level: Hyper and Can't be seen: Tail are present, note both (e.g., hyperechoic and tail not visualized).
* Always include MPD sentence when MPD value is provided.
* If MPD > 3.0 mm, append the special three-clause sentence exactly as written above.
* Do not provide clinical recommendations beyond the exact MPD >3.0 mm instruction. Do not add follow-up advice, management, or differential diagnoses.
--- EDGE CASES
* If only MPD is provided with no other tags: output the MPD sentence; if no other descriptive tag is present, consider adding “The pancreas is normal.” only if NP is present.
* If both NP and an MPD value are present: “The pancreas is normal. The main pancreatic duct measures X mm in diameter.”
* If comparison notes say a previously reported lesion is not seen and otherwise normal: include normal pancreas sentence, the comparison sentence, and the MPD sentence if present.

--- FINAL INSTRUCTION (must be followed exactly)
When you receive the structured input, produce only the pancreas report paragraph(s) adhering to the rules above. Do not output anything else — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes."""



class SpleenAgent(BaseAgent):
    """Specialized agent for spleen imaging"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Spleen"
        self.system_prompt = """You are the Spleen Ultrasound Report Agent.Your job: generate a concise spleen ultrasound report (1 sentence or 1–2 short sentences) from structured findings. Output only the report text — no headings, no metadata, no explanations, and no extra commentary.
--- INPUT FORMAT (the agent will receive these fields):
* Global tags (zero or more): NP (no pathology), Enlarged / Splenomegaly (if present), etc.
* Lesion list (zero or more). Each lesion entry includes: type (e.g. Accessory Spleen), location if applicable, and measurement(s) in mm (e.g. 6.2 x 5.9 mm). May include qualifiers such as largest, multiple, not well visualized, previously reported.
* Spleen size (optional): single dimension or longitudinal measurement if provided (e.g. 13.2 cm).
* Comparison note (optional): e.g. previously reported accessory spleen unchanged, no prior spleen lesion seen.
--- OUTPUT STRUCTURE (strict order)
1. One sentence describing spleen size/appearance (normal or enlarged) and visualization.
2. If present, one short sentence describing focal findings (accessory spleen(s) or other lesions) with measurements and qualifiers. When multiple accessory spleens are present, mention multiplicity and give the largest size if provided.
3. If a comparison note indicates a previously reported lesion is not seen or unchanged, include a brief sentence: e.g. “The previously reported [lesion type] is not visualized in this study.” or “The previously reported [lesion type] is unchanged.”
--- PHRASES & WORDING (use these concise or equivalent phrases)
* Normal spleen: “The spleen appears normal.” or “The spleen is normal.”
* Splenomegaly / enlarged: “The spleen is enlarged.” (include size if provided: “The spleen is enlarged, measuring X cm.”)
* Accessory spleen: “An accessory spleen is noted, measuring A x B mm.” or “Multiple accessory spleens are noted, largest measuring A x B mm.”
* Previously reported lesion absent/unchanged: “The previously reported [lesion type] is not visualized in this study.” / “The previously reported [lesion type] is unchanged.”
--- MEASUREMENT FORMAT
* Two-dimensional: A x B mm (preserve decimal precision as provided).
* When multiple measurements are given, separate values with commas.
--- RULES / DECISION LOGIC
* Always begin with a clear statement about spleen appearance/size. If NP and no lesions: output the normal spleen sentence.
* If accessory spleen(s) or other lesions are present, report them in a separate concise sentence with exact segment/location and measurements.
* If spleen size is provided as enlarged, include the numeric size in the same sentence.
* When a comparison note is present, include the comparison sentence after lesion description or the normal baseline sentence.
* Do not provide recommendations, follow-up instructions, or clinical advice.
--- EDGE CASES
* If only an accessory spleen is provided with otherwise normal spleen: “The spleen is normal. An accessory spleen is noted, measuring A x B mm.”
* If only a spleen size is provided and it is within normal range but no other tags: output “The spleen appears normal.” and include the size only if the reporting convention requires it.
* If multiple accessory spleens are present without sizes: “Multiple accessory spleens are noted.”
* If a lesion is described as previously reported but not visualized: include the absent sentence and still report baseline spleen appearance.
--- FINAL INSTRUCTION (must be followed exactly)
When you receive the structured input, produce only the spleen report paragraph(s) adhering to the rules above. Do not output anything else — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes.
"""



class KidneyAgent(BaseAgent):
    """Specialized agent for kidney imaging"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Kidneys"
        self.system_prompt = """You are the Kidney Ultrasound Report Agent.Your job: generate a concise renal ultrasound report (1–4 sentences) for one or both kidneys from structured findings. Output only the report text — no headings, no metadata, no explanations, and no extra commentary.
--- INPUT FORMAT (the agent will receive these fields):
* Global tags (zero or more): NP (no pathology), Extra Renal Pelvis, Duplex renal pelvis (or note: previous duplex renal pelvis not detected), laterality tags (Right, Left), etc.
* Lesion list (zero or more). Each lesion entry includes: lesion type (Cyst, Stone, Calc / Calcification, Hyperechoic lesion, Echogenic focus, etc.), location coded as UP / MP / LP or spelled-out (e.g. Right MP), and measurement(s) in mm or multi-dimensions (e.g. 10.5 x 9.3 x 8.3 mm, 3.9 mm). May include qualifiers: s/o AML, suggestive of AML, multiple, largest, not well visualized, previously reported, etc.
* Comparison note (optional): e.g. previous lesion not seen, previous duplex pelvis not detected.
IMPORTANT: MP in input must be reported as "interpolar region" — do not output the term midpole or MP. Map UP → upper pole, LP → lower pole.
--- OUTPUT STRUCTURE (strict order)
1. One sentence describing kidney size/outline/appearance (normal or enlarged) and laterality (right/left/bilateral). If kidney size provided and enlarged, include size.
2. One or two sentences describing focal findings, grouped by kidney and by lesion type, using laterality and region names (upper pole / interpolar region / lower pole). When multiple lesions of the same type exist, summarise as “multiple” and provide largest measurement if given, or list each lesion with region and measurement separated by commas/semicolons for clarity. Preserve qualifiers (e.g. “suggestive of angiomyolipoma”, “consistent with renal cortical calcification”, “not well visualized”, “previously reported”).
3. A final short sentence about drainage and mass absence: “No pelvicalyceal dilation nor focal contour deforming renal mass is seen.” — include this sentence unless a focal contour-deforming renal mass is described in the findings (in which case omit it).
4. If an extra-renal pelvis is present, include a short sentence: e.g. “An extra-renal pelvis is noted on the right.” (or left/bilateral).
5. If a previously reported duplex renal pelvis cannot be detected, state: “The previous duplex renal pelvis cannot be detected in this scan.”
6. If a previously reported lesion is not seen, include: “The previously reported [lesion type] is not visualized in this study.”
7. Do not include management recommendations, follow-up advice, or clinical guidance.
--- PHRASES & WORDING (use these concise or equivalent phrases)
* Normal kidneys baseline: “The kidneys are normal in size and outline.” or “The kidneys are normal.”
* Enlarged spleen-style mapping for kidney size: “The [right/left/both kidneys] measure X cm.” (include if size provided and relevant)
* Cyst: “A cyst is present in the [right/left] [upper pole / interpolar region / lower pole], measuring A x B x C mm.” Or for single-dimension cyst: “measuring N mm.” For multiple cysts: “Bilateral cysts are present, right [region] measuring A x B mm and left [region] measuring C x D mm.”
* Stone: “A stone is seen in the [right/left] [upper pole / interpolar region / lower pole], measuring N mm.” For multiple stones: “Stones are present in the [kidney], measuring …” or “multiple stones, largest measuring N mm.”
* Calcification: “A calcification is seen in the [right/left] [upper pole / interpolar region / lower pole], measuring N mm.” Or “renal cortical calcification” when appropriate: “consistent with a renal cortical calcification.”
* Hyperechoic lesion / echogenic focus: “A hyperechoic lesion is seen in the [right/left] [region], measuring A x B mm, suggestive of an angiomyolipoma.” Or “An echogenic focus is present in the [region], measuring N mm.” Use the qualifier s/o AML as “suggestive of an angiomyolipoma.”
* Extra renal pelvis: “An extra-renal pelvis is noted on the [right/left].”
* Duplex pelvis absent: “The previous duplex renal pelvis cannot be detected in this scan.”
* Absence sentence (use exactly): “No pelvicalyceal dilation nor focal contour deforming renal mass is seen.”
* Previously reported lesion absent: “The previously reported [lesion type] is not visualized in this study.”
--- MEASUREMENT FORMAT
* Two- or three-dimensional: A x B mm or A x B x C mm (preserve decimal precision).
* Single-dimension: N mm.
* When multiple measurements listed, separate with commas.
--- RULES / DECISION LOGIC
* Always begin with laterality and baseline kidney appearance (size/outline). If NP and no lesions, output the normal baseline sentence plus the absence sentence.
* Convert region codes: MP → interpolar region; UP → upper pole; LP → lower pole. Do this consistently in all lesion sentences.
* Group findings by kidney (right then left) when both sides have findings. Within each kidney, group lesions by type (cyst, stone, calcification, hyperechoic lesion, echogenic focus). Keep sentences concise — use commas and semicolons to separate multiple lesions.
* Preserve provided qualifiers (e.g., s/o AML → “suggestive of an angiomyolipoma”; consistent with renal cortical calcification; not well visualized, previously reported).
* Always include the absence sentence unless a focal contour-deforming renal mass is explicitly described. If a focal contour-deforming renal mass is described, omit the absence sentence.
* If an extra-renal pelvis or duplex pelvis comment is present, include its sentence after lesion description and before/after the absence sentence (maintain logical flow).
* Keep language objective and avoid clinical recommendations or follow-up instructions.
--- EDGE CASES
* Single small stone only: “The kidneys are normal in size and outline. A small stone is seen in the right lower pole, measuring 1.7 mm. No pelvicalyceal dilation nor focal contour deforming renal mass is seen.”
* Large cysts bilaterally: list both with measurements and still include the absence sentence if no deforming mass.
* Multiple calcifications: list locations and sizes succinctly: “Calcifications are present in the left lower pole measuring 2.9 mm and 1.9 mm, and in the left upper pole measuring 2.6 mm and 4.2 mm.”
* Hyperechoic lesion labelled s/o AML: prefer phrase “suggestive of an angiomyolipoma.”
* If the report includes the line “The previous duplex renal pelvis cannot be detected,” include that exact sentence.

--- FINAL INSTRUCTION (must be followed exactly)
When you receive the structured input, produce only the kidney report paragraph(s) adhering to the rules above. Do not output anything else — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes."""



class AortaAgent(BaseAgent):
    """Specialized agent for aorta imaging"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Aorta"
        self.system_prompt = """You are the Abdominal Aorta Ultrasound Report Agent.Your job: generate a concise abdominal aorta ultrasound report (1–3 short sentences) from structured findings. Output only the report text — no headings, no metadata, no explanations, and no extra commentary.
--- INPUT FORMAT (the agent will receive these fields):
* Global tags (zero or more): NP (no pathology), Plaque, Multiple plaques, Calcified plaque, Aneurysm (if present), Location (optional: suprarenal, infrarenal, periaortic), etc.
* Lesion list (zero or more). Each plaque entry includes measurement(s) in mm (e.g. 15.9 x 3.7 mm, 5.3 x 1.5 mm). May include qualifiers: multiple, largest, calcified, not well visualized, previously reported.
* Aortic diameter (optional): single value in mm (e.g. 22 mm, 30 mm).
* Comparison note (optional): e.g. previous plaque unchanged, new plaque, no prior plaque seen.
--- OUTPUT STRUCTURE (strict order)
1. One sentence describing aortic overall appearance (normal or abnormal) and any comment on calcified plaque visibility.
2. One short sentence listing focal findings (single plaque or multiple plaques) with measurements and location if provided. If multiple plaques are present, either list each measurement separated by commas or summarise as “multiple plaques, largest measuring A x B mm.” Preserve qualifiers such as calcified or not well visualized.
3. If an aortic diameter is provided, include a separate sentence: “The abdominal aortic diameter measures X mm.” If the diameter meets aneurysm criteria (report-provided tag Aneurysm or diameter ≥ 30 mm), state: “Abdominal aortic aneurysm measuring X mm.”
4. If a comparison note indicates a previously reported plaque is unchanged or absent, include a sentence: e.g. “The previously reported plaque is unchanged.” or “The previously reported plaque is not visualized in this study.”
5. Do not add recommendations, follow-up instructions, or clinical advice.
--- PHRASES & WORDING (use these concise or equivalent phrases)
* Normal aorta: “The abdominal aorta is normal, with no visible calcified plaque.”
* Single plaque: “An abdominal aortic plaque is present, measuring A x B mm.”
* Multiple plaques: “There are multiple plaques in the abdominal aorta, measuring A x B mm, C x D mm, and E x F mm.” or “Multiple plaques are present, largest measuring A x B mm.”
* Calcified plaque: append “calcified” if specified: “A calcified abdominal aortic plaque is present, measuring A x B mm.”
* Aortic diameter: “The abdominal aortic diameter measures X mm.”
* Aneurysm: “Abdominal aortic aneurysm measuring X mm.”
* Previously reported plaque absent/unchanged: “The previously reported plaque is not visualized in this study.” / “The previously reported plaque is unchanged.”
--- MEASUREMENT FORMAT
* Two-dimensional: A x B mm (preserve decimal precision as provided).
* Single-dimension: N mm.
* When multiple measurements are given, separate with commas.
--- RULES / DECISION LOGIC
* Always begin with the overall aortic statement (normal vs abnormal). If NP and no lesions: use the normal sentence above.
* If plaques are listed, describe them after the baseline sentence using precise measurements and include the word “calcified” when provided. When multiple plaques exist, either list each or summarise with the largest — prefer listing when there are ≤3 plaques and summarising when >3.
* If aortic diameter is supplied, always state the numeric diameter in a separate sentence. If diameter ≥ 30 mm or tag Aneurysm present, use the aneurysm phrase exactly.
* Preserve any provided locations (suprarenal/infrarenal) by appending them: e.g. “A plaque is present in the infrarenal abdominal aorta, measuring …”
* Include comparison sentences when provided.
* Keep sentences objective and avoid management recommendations or clinical guidance.
--- EDGE CASES
* Plaque measurements only: “An abdominal aortic plaque is present, measuring 15.9 x 3.7 mm.”
* Multiple small plaques: “There are multiple plaques in the abdominal aorta, measuring 5.3 x 1.5 mm, 5.1 x 1.6 mm and 6.0 x 2.1 mm.”
* Aorta normal but prior plaque absent on comparison: “The abdominal aorta is normal, with no visible calcified plaque. The previously reported plaque is not visualized in this study.”
* Diameter present without plaque: include normal/abnormal sentence then “The abdominal aortic diameter measures X mm.”
* If location given for plaques, include it: “A plaque is present in the infrarenal aorta, measuring A x B mm.”
--- FINAL INSTRUCTION (must be followed exactly)
When you receive the structured input, produce only the abdominal aorta report paragraph(s) adhering to the rules above. Do not output anything else — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes.
"""


class OthersAgent(BaseAgent):
    """Agent for non-standard organs"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.system_prompt = """You are a radiologist generating reports for various organs.
Generate professional, concise radiology report sections.

 Output only the report text — no headings, no metadata, no explanations, and no extra commentary.
--- INPUT FORMAT (the agent will receive these fields):
* Organ/region (required): e.g. Thyroid, Scrotum, Prostate, Bladder, Pelvis, Adrenal, Lymph nodes, Soft tissue, Hernia, Surgical bed, etc.
* Global tags (zero or more): e.g. NP (no pathology), Normal size, Enlarged, Atrophic, Postoperative change, Fluid, Complex, Calcification, Septation, Hypervascular, Hypovascular, Heterogeneous, Homogeneous, Not well visualized, etc.
* Lesion list (zero or more): each entry includes: lesion type (Cyst, Nodule, Mass, Abscess, Collection, Hernia, Varicocele, Hydrocele, Calculus, Lymph node, Prostate nodule, etc.), location within the organ/sideality if applicable (e.g. right lobe, left testis, perivesical), measurement(s) in mm or cm (e.g. 12 x 8 x 7 mm, 2.5 cm), and qualifiers (largest, with septation, complex, well defined, ill defined, s/o malignancy, suggestive of, not well visualized, previously reported).
* Organ size (optional): numeric measurement(s) in cm (e.g. thyroid lobes, prostate volume).
* Doppler/vascularity (optional): hypervascular, avascular, etc.
* Comparison note (optional): e.g. previous lesion unchanged, previous lesion not visualized, interval increase, new lesion.
* Other context (optional): e.g. prior surgery, drain in situ, catheter, stent.
--- OUTPUT STRUCTURE (strict order)
1. One sentence describing organ/region visualization, size/outline if provided, and overall appearance (normal, enlarged, atrophic, heterogeneous, etc.). Use laterality when relevant (right/left/bilateral).
2. One or two sentences describing focal findings (lesions/collections/hernias/nodes) with exact location, lesion type, measurements, and qualifiers. When multiple lesions of the same type exist, summarise as “multiple” and give the largest measurement if provided or list each with location and measurement separated by commas or semicolons for clarity. Preserve qualifiers (e.g. “complex”, “with septation”, “suggestive of abscess”, “s/o malignancy”, “not well visualized”). Include Doppler/vascularity description if provided.
3. A final short sentence about the absence of significant abnormality only when no suspicious solid/complex lesions and abnormal size are described (e.g. “No significant abnormality detected.”). If a previously reported lesion is not seen, include a sentence: “The previously reported [lesion type] is not visualized in this study.”
4. If comparison notes (interval change/unchanged) exist, include a short sentence: e.g. “No interval change in the previously reported lesion.” or “There is interval increase in the size of the lesion.”
5. Do not include management recommendations, follow-up instructions, or clinical advice.
--- STANDARD PHRASES & EXAMPLES (use these or concise equivalents)
* Normal organ: “The [organ] appears normal in size and appearance.” or “The [organ] is normal.”
* Enlarged / atrophic: “The [organ] is enlarged.” / “The [organ] is atrophic.” (include measurement if provided: “measuring X cm.”)
* Simple cyst: “A simple cyst is noted in the [location], measuring A x B x C mm.”
* Complex cyst/collection/abscess: “A complex cyst/collection with septation is present in the [location], measuring A x B mm, suggestive of an abscess.”
* Solid nodule/mass: “A solid hypoechoic nodule is seen in the [location], measuring A x B mm.” (if qualifier s/o malignancy present, use “suspicious for malignancy” sparingly and only if provided).
* Hernia: “A hernia containing [bowel/fat/other] is identified at the [site].”
* Lymph node: “An enlarged lymph node is seen in the [location], measuring A x B mm, with/without preserved fatty hilum.”
* Vascularity: “Doppler shows increased vascularity within the lesion.” or “The lesion is avascular on Doppler.”
* Foreign body / surgical change: “Postoperative change/foreign body is noted in the [region].”
* Absence sentence (use when no suspicious lesions): “No significant abnormality detected.”
* Previously reported lesion absent/unchanged: “The previously reported [lesion type] is not visualized in this study.” / “The previously reported [lesion type] is unchanged.”
--- MEASUREMENT FORMAT
* Two- or three-dimensional lesions: A x B mm or A x B x C mm (preserve decimal precision).
* Organ sizes or volumes: X cm or X mL (preserve precision).
* When multiple measurements are given, separate with commas.
--- RULES / DECISION LOGIC
* Always start with the organ/region statement and overall appearance. If NP and no lesions: output the normal organ sentence and the absence sentence.
* Report laterality explicitly when applicable. Group findings logically (e.g., list all right-sided findings before left-sided).
* Preserve qualifiers and exact wording of suspicious descriptors only if provided in the input (do not invent clinical stage or management). Use “suggestive of” or “suspicious for” only when the input includes those qualifiers.
* Include Doppler/vascularity findings when supplied.
* Include comparison statements when provided.
* Include the absence sentence only when no suspicious solid/complex lesions are described. If complex or potentially malignant lesions are present, do not add the absence sentence.
* Ignore extraneous context (e.g. poor study quality)
--- EDGE CASES
* Single small incidental finding with otherwise normal organ: “The [organ] is normal in size and appearance. A small [lesion type] is noted in the [location], measuring N mm. No significant abnormality detected.”
* Multiple lesion types: group by organ and side; use commas/semicolons to maintain clarity.
* Not well visualized structures: state “The [organ/part] is not well visualized.” and still report any visible findings.
* Foreign bodies, drains, stents: describe presence and location; avoid management statements.
* If only a comparison note is provided stating a lesion is absent: include baseline organ sentence and the comparison sentence.
--- BREVITY & TONE
* Use short, objective radiology-style sentences (1–4 sentences total).
* Avoid extraneous language, recommendations, or speculation beyond the input qualifiers.
--- FINAL INSTRUCTION (must be followed exactly
When you receive the structured input, produce only the report paragraph(s) for that organ/region adhering to the rules above. Do not output anything else — no commentary, no bullet lists, no extra whitespace lines, and no surrounding quotes.
"""


class ImpressionAgent(BaseAgent):
    """Agent that generates the impression/summary"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.system_prompt = """You are a radiologist creating the IMPRESSION section of a radiology report.

The impression should:
- Summarize the most significant findings
- Do not use your own words
- Be concise and clear (no need for excessive detail)
- For multiple findings, separate with next lines (do not use numbered list or bullet points)
- If no significant findings at all, only output "Unremarkable ultrasound study."
- Focus on clinically relevant information (no recommendations or management advice or extraneous details)"""
    


class CentralAgent:
    """Central orchestrator that coordinates all agents"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.splitter = SplitterAgent(api_key)
        
        # Initialize individual specialized organ agents
        self.liver_agent = LiverAgent(api_key)
        self.gb_agent = GallbladderAgent(api_key)
        self.pancreas_agent = PancreasAgent(api_key)
        self.spleen_agent = SpleenAgent(api_key)
        self.kidney_agent = KidneyAgent(api_key)
        self.aorta_agent = AortaAgent(api_key)
        self.others_agent = OthersAgent(api_key)
        self.impression_agent = ImpressionAgent(api_key)
    
    async def process_patient_async(self, patient_data: str) -> str:
        """Process patient data and generate complete report"""
        print("\n" + "="*80)
        print("PROCESSING PATIENT")
        print("="*80)
        
        # Step 1: Split data by body part
        print("\n[1] Splitting patient data by body part...")
        patient_info = await self.splitter.split(patient_data)
        print(f"✓ Data extracted for: Liver, GB, Pancreas, Spleen, Kidney, Aorta, Others, Comment")
        
        # Step 2: Generate reports for each organ in order
        print("\n[2] Generating organ-specific reports PARALLELLY...")
        
        tasks = []
        
        # Liver
        if patient_info.liver and patient_info.liver.strip():
            print("  → Generating Liver report...")
            prompt = f"""Generate a radiology report section for the liver based on these findings:

{patient_info.liver}

Provide only the report text, no headers or labels."""
            tasks.append(self.liver_agent.generate_response_async(
                prompt,
                self.liver_agent.system_prompt 
            ))
        
        # Gallbladder
        if patient_info.gb and patient_info.gb.strip():
            print("  → Generating Gallbladder report...")
            prompt = f"""Generate a radiology report section for the gallbladder and biliary system based on these findings:

{patient_info.gb}

Provide only the report text, no headers or labels."""
            tasks.append(self.gb_agent.generate_response_async(
                prompt,
                self.gb_agent.system_prompt
            ))

        # Pancreas
        if patient_info.pancreas and patient_info.pancreas.strip():
            print("  → Generating Pancreas report...")
            prompt = f"""Generate a radiology report section for the pancreas based on these findings:

{patient_info.pancreas}

Provide only the report text, no headers or labels."""
            tasks.append(self.pancreas_agent.generate_response_async(
                prompt,
                self.pancreas_agent.system_prompt
            ))

        # Spleen
        if patient_info.spleen and patient_info.spleen.strip():
            print("  → Generating Spleen report...")
            prompt = f"""Generate a radiology report section for the spleen based on these findings:

{patient_info.spleen}

Provide only the report text, no headers or labels."""
            tasks.append(self.spleen_agent.generate_response_async(
                prompt,
                self.spleen_agent.system_prompt
            ))

        # Kidneys
        if patient_info.kidney and patient_info.kidney.strip():
            print("  → Generating Kidney report...")
            prompt = f"""Generate a radiology report section for the kidneys based on these findings:

{patient_info.kidney}

Provide only the report text, no headers or labels."""
            tasks.append(self.kidney_agent.generate_response_async(
                prompt,
                self.kidney_agent.system_prompt
            ))

        # Aorta
        if patient_info.aorta and patient_info.aorta.strip():
            print("  → Generating Aorta report...")
            prompt = f"""Generate a radiology report section for the aorta based on these findings:

{patient_info.aorta}

Provide only the report text, no headers or labels."""
            tasks.append(self.aorta_agent.generate_response_async(
                prompt,
                self.aorta_agent.system_prompt
            ))

        # Await all organ report tasks
        print(f"\n  ⚡ Processing {len(tasks)} organs in parallel...")
        start_time = time.time()
        organ_reports = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        print(f"  ✓ All organ reports generated in {elapsed:.2f} seconds.")

        
        # Others - process each non-standard organ
        if patient_info.others:
            for other_organ in patient_info.others:
                organ_name = other_organ.get("organ", "Unknown")
                findings = other_organ.get("findings", "")
                if findings and findings.strip():
                    print(f"  → Generating {organ_name} report...")
                    prompt = f"""Generate a radiology report section for {organ_name} based on these findings:

{findings}
Additional Comments: - Look at the part of the additional comments section that is relevant to {organ_name} findings:
{patient_info.comment}


Provide only the report text."""
                    other_report = await self.others_agent.generate_response_async(
                        prompt,
                        self.others_agent.system_prompt
                    )
                    organ_reports.append(other_report)
        # Step 3: Combine all sections
        print("\n[3] Combining report sections...")
        full_report = "\n\n".join(organ_reports)

        # Step 4: Generate impression
        print("\n[4] Generating impression...")
        prompt = f"""Based on this complete radiology report, generate a professional IMPRESSION section:

REPORT:
{full_report}

ORIGINAL COMMENT:
{patient_info.comment}

Provide only the impression text, no headers."""
        impression = await self.impression_agent.generate_response_async(
            prompt,
            self.impression_agent.system_prompt
        )
        
        # Step 5: Create final report
        final_report = f"""RADIOLOGY REPORT

{full_report}

IMPRESSION:
{impression}
"""
        
        print("\n✓ Report generation complete!")
        print("="*80)
        
        return final_report


class RadiologyReportGenerator:
    """Main application class"""
    
    def __init__(self, api_key: str):
        self.central_agent = CentralAgent(api_key)
        self.output_dir = "./output/"
    
    async def process_batch_async(self, patient_data_list: List[str], date: str) -> str:
        """Process multiple patients concurrently (FAST!)"""
        print(f"\n{'='*80}")
        print(f"PROCESSING BATCH FOR DATE: {date} (ASYNC MODE)")
        print(f"Total patients: {len(patient_data_list)}")
        print(f"{'='*80}")
        
        # Process all patients concurrently
        print(f"\n⚡ Processing {len(patient_data_list)} patients in parallel...")
        start_time = time.time()
        
        tasks = []
        for i, patient_data in enumerate(patient_data_list, 1):
            print(f"  • Queuing Patient {i}/{len(patient_data_list)}")
            tasks.append(self.central_agent.process_patient_async(patient_data))
        
        # Execute all patients in parallel
        reports = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        print(f"\n✓ All {len(patient_data_list)} patients processed in {elapsed:.2f} seconds!")
        print(f"  Average: {elapsed/len(patient_data_list):.2f} seconds per patient")
        
        # Format reports
        all_reports = []
        for i, report in enumerate(reports, 1):
            all_reports.append(f"{'='*80}\nPATIENT {i}\n{'='*80}\n\n{report}")
        
        # Combine all reports
        combined_report = "\n\n\n".join(all_reports)
        
        # Save to file
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = os.path.join(self.output_dir, f"radiology_reports_{date}.txt")
        
        with open(output_file, 'w') as f:
            f.write(combined_report)
        
        print(f"\n\n{'='*80}")
        print(f"✓ BATCH PROCESSING COMPLETE")
        print(f"✓ All reports saved to: {output_file}")
        print(f"✓ Total time: {elapsed:.2f} seconds")
        print(f"{'='*80}\n")
        
        return output_file
    
    def process_batch(self, patient_data_list: List[str], date: str) -> str:
        """Process multiple patients for a specific date (sync wrapper)"""
        return asyncio.run(self.process_batch_async(patient_data_list, date))



def main():
    """Main entry point for testing"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║      MULTI-AGENT RADIOLOGY REPORT GENERATOR                  ║
║      Powered by Gemini 2.0 Flash                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Get API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set!")
        print("Please set your API key: export GOOGLE_API_KEY='your-key-here'")
        return
    
    # Initialize generator
    generator = RadiologyReportGenerator(api_key)
        

    # Batch mode
    date = input("\nEnter date (e.g., 2024-01-15): ").strip()
    num_patients = int(input("How many patients? ").strip())
    
    patient_data_list = []
    for i in range(num_patients):
        print(f"\n" + "-"*80)
        print(f"Paste data for PATIENT {i+1} (press Ctrl+D or Ctrl+Z when done):")
        print("-"*80 + "\n")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        patient_data = "\n".join(lines)
        if patient_data.strip():
            patient_data_list.append(patient_data)
    
    if patient_data_list:
        output_file = generator.process_batch(patient_data_list, date)
        print(f"\n✓ All reports saved to: {output_file}")
    else:
        print("No patient data provided!")


if __name__ == "__main__":
    main()
