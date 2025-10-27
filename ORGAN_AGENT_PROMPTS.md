# Customizing Individual Organ Agent Prompts

The system now uses **individual specialized agents** for each standard organ, each with their own customized prompt.

---

## 📋 Individual Organ Agents

### 1. Liver Agent
**Location**: `radiology_agent_system.py` - `LiverAgent` class

**Current Specialization**:
- Hepatic imaging and liver pathology
- Liver size, echotexture, and margins
- Focal lesions with size, location, characteristics
- Hepatic vasculature
- Hepatomegaly assessment

**Key Guidelines**:
- Liver span measurements in cm
- Reports on focal lesions
- Vascular assessment

---

### 2. Gallbladder Agent
**Location**: `radiology_agent_system.py` - `GallbladderAgent` class

**Current Specialization**:
- Gallbladder and biliary imaging
- Wall thickness (normal <3mm)
- Stones/polyps with size and number
- CBD diameter (normal <6mm, <8mm post-cholecystectomy)
- Pericholecystic fluid
- Cholelithiasis, cholecystitis

**Key Guidelines**:
- GB wall thickness measurement
- CBD diameter assessment
- Stone characterization

---

### 3. Pancreas Agent
**Location**: `radiology_agent_system.py` - `PancreasAgent` class

**Current Specialization**:
- Pancreatic imaging
- Size for head, body, tail
- Echotexture assessment
- MPD diameter (normal <3mm)
- Masses, cysts, calcifications
- Atrophy or lipomatosis

**Key Guidelines**:
- Regional size measurements
- MPD diameter assessment
- Focal lesion characterization

---

### 4. Spleen Agent
**Location**: `radiology_agent_system.py` - `SpleenAgent` class

**Current Specialization**:
- Splenic imaging
- Size assessment (normal <12-13cm)
- Echotexture
- Splenomegaly (size >13cm)
- Focal lesions
- Accessory spleens

**Key Guidelines**:
- Size measurement in cm
- Splenomegaly threshold
- Focal lesion assessment

---

### 5. Kidney Agent
**Location**: `radiology_agent_system.py` - `KidneyAgent` class

**Current Specialization**:
- Renal imaging
- Size for both kidneys (normal 10-12cm)
- Cortical thickness and echogenicity
- Hydronephrosis assessment
- Stones, cysts, masses
- Cortical scarring

**Key Guidelines**:
- Bilateral kidney assessment
- Size measurements
- Hydronephrosis grading
- Parenchymal disease

---

### 6. Aorta Agent
**Location**: `radiology_agent_system.py` - `AortaAgent` class

**Current Specialization**:
- Vascular imaging focused on aorta
- Aortic caliber/diameter
- Aneurysm definition (>3cm for abdominal)
- Mural thrombus
- Calcifications
- Dissection detection

**Key Guidelines**:
- Diameter measurements
- Aneurysm thresholds
- Location specification
- Urgent findings flagging

---

## 🎯 How to Customize Agent Prompts

### Method 1: Edit in radiology_agent_system.py

Each agent class has its prompt in the `__init__` method:

```python
class LiverAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Liver"
        self.system_prompt = """YOUR CUSTOM PROMPT HERE"""
```

**To customize**:
1. Open `radiology_agent_system.py`
2. Find the agent class (e.g., `LiverAgent`)
3. Modify the `self.system_prompt` string
4. Save and test

---

### Method 2: Edit in config.py (Reference Copy)

The `config.py` file contains reference copies of all prompts:

```python
AGENT_CONFIG = {
    "liver": {
        "system_prompt": """YOUR CUSTOM PROMPT"""
    },
    "gallbladder": {
        "system_prompt": """YOUR CUSTOM PROMPT"""
    },
    # ... etc
}
```

**Note**: These are reference copies. To actually change the agent behavior, you must edit `radiology_agent_system.py`.

---

## 📝 Customization Examples

### Example 1: Add More Detail to Liver Agent

```python
class LiverAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Liver"
        self.system_prompt = """You are a radiologist specializing in hepatic imaging and liver pathology.
Generate a professional, concise radiology report section for the liver.

Guidelines:
- Use standard medical terminology for liver assessment
- Report liver size, echotexture, and margins
- ALWAYS specify liver segments for focal lesions (I-VIII)
- Describe focal lesions with size, location, and characteristics
- Report hepatic vein and portal vein patency
- Assess for cirrhotic morphology
- Comment on surface nodularity if present
- If findings show "NP" (No Pathology) or normal, report as "No significant abnormality detected"
- Include all measurements provided
- Use complete sentences
- Be concise but thorough"""
```

---

### Example 2: Customize Kidney Agent for Transplant Focus

```python
class KidneyAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Kidneys"
        self.system_prompt = """You are a radiologist specializing in renal imaging with focus on transplant assessment.
Generate a professional, concise radiology report section for the kidneys.

Guidelines:
- Report native kidneys and transplant kidney separately
- For transplant: assess perfusion, collecting system, perinephric fluid
- Measure resistive indices if provided
- Report size for both kidneys separately (normal 10-12cm)
- Describe cortical thickness and echogenicity
- Report presence/absence of hydronephrosis with grading
- Describe stones, cysts, or masses with size and characteristics
- Note vascular flow if mentioned
- If findings show "NP" or normal, report as "No significant abnormality detected"
- Use complete sentences
- Be concise but thorough"""
```

---

### Example 3: Enhanced Gallbladder Agent with Scoring

```python
class GallbladderAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "Gallbladder and Biliary System"
        self.system_prompt = """You are a radiologist specializing in gallbladder and biliary imaging.
Generate a professional, concise radiology report section for the gallbladder and biliary system.

Guidelines:
- Use standard medical terminology for gallbladder and biliary assessment
- Report gallbladder wall thickness (normal <3mm)
- If wall thickness >3mm, assess for acute cholecystitis signs
- Apply Tokyo criteria if cholecystitis suspected
- Describe stones/polyps with size and number
- Report CBD (Common Bile Duct) diameter (normal <6mm, <8mm if post-cholecystectomy)
- Note presence of pericholecystic fluid, Murphy's sign, hyperemia
- Assess for Mirizzi syndrome if appropriate
- Comment on presence/absence of cholelithiasis, cholecystitis
- Include intrahepatic biliary dilation if mentioned
- Be precise with all measurements
- Use complete sentences
- Be concise but thorough"""
```

---

## 🔧 Template for Creating Custom Agent Prompt

```python
class [Organ]Agent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.organ_name = "[Organ Name]"
        self.system_prompt = """You are a radiologist specializing in [organ] imaging.
Generate a professional, concise radiology report section for the [organ].

Guidelines:
- Use standard medical terminology for [organ] assessment
- Report [key measurement 1] (normal range: X-Y)
- Report [key measurement 2] (normal range: X-Y)
- Describe [common finding 1] if present
- Describe [common finding 2] if present
- Note [pathology 1] if present
- Note [pathology 2] if present
- If findings show "NP" (No Pathology) or normal, report as "No significant abnormality detected"
- Be precise with all measurements
- Use complete sentences
- Be concise but thorough
- Do not include section headers or labels, just the report text"""
```

---

## 🎓 Best Practices for Custom Prompts

### 1. **Be Specific About Measurements**
- Include normal ranges
- Specify units (cm, mm, mm/s for velocities)
- Define thresholds for abnormality

### 2. **Include Domain-Specific Knowledge**
- Reference relevant scoring systems (e.g., Tokyo criteria)
- Mention specific anatomical variants
- Include grading systems if applicable

### 3. **Maintain Consistency**
- Keep the same structure across all agents
- Use consistent terminology
- Maintain the same level of detail

### 4. **Focus on Clinical Relevance**
- Prioritize clinically significant findings
- Include follow-up recommendations when appropriate
- Flag urgent findings explicitly

### 5. **Test Your Changes**
```bash
# After editing prompts, test with:
python test_system.py

# Test specific organ:
python example_usage.py
```

---

## 📊 Comparison: Generic vs. Specialized Agents

### Before (Generic OrganAgent)
```python
class OrganAgent(BaseAgent):
    def __init__(self, api_key: str, organ_name: str):
        # One generic prompt for all organs
        self.system_prompt = f"""You are a radiologist specializing in {organ_name} imaging..."""
```

**Limitations**:
- Same prompt structure for all organs
- No organ-specific guidelines
- No specialized medical knowledge
- Generic measurements

---

### After (Specialized Agents)
```python
class LiverAgent(BaseAgent):
    def __init__(self, api_key: str):
        self.system_prompt = """You are a radiologist specializing in hepatic imaging...
        - Report liver size, echotexture, and margins
        - Describe focal lesions with size, location, and characteristics
        - Comment on hepatic vasculature if mentioned
        ..."""

class GallbladderAgent(BaseAgent):
    def __init__(self, api_key: str):
        self.system_prompt = """You are a radiologist specializing in gallbladder imaging...
        - Report gallbladder wall thickness (normal <3mm)
        - Describe stones/polyps with size and number
        - Report CBD diameter (normal <6mm)
        ..."""
```

**Benefits**:
- Organ-specific expertise
- Specialized medical knowledge
- Relevant measurement guidelines
- Domain-specific terminology
- Better quality reports

---

## 🧪 Testing Custom Prompts

### Quick Test
```bash
# Test all agents
python test_system.py

# Test with example data
python example_usage.py
```

### Detailed Test
```python
from radiology_agent_system import LiverAgent

# Initialize
agent = LiverAgent(api_key)

# Test with sample data
findings = "Hepatomegaly, span 18cm, multiple small cysts"
report = agent.generate_report(findings)
print(report)
```

---

## 📚 Where Prompts Are Located

1. **Primary Location** (actual code):
   - `radiology_agent_system.py`
   - Lines for each agent class

2. **Reference Copy** (documentation):
   - `config.py`
   - Under `AGENT_CONFIG`

3. **This Guide**:
   - `ORGAN_AGENT_PROMPTS.md`
   - Examples and templates

---

## 🔄 Workflow for Updating Prompts

1. **Decide what to change**
   - Which organ agent?
   - What specific guidelines?

2. **Edit the agent class**
   - Open `radiology_agent_system.py`
   - Find the agent class
   - Modify `self.system_prompt`

3. **Update config.py (optional)**
   - Keep reference copy in sync
   - Edit corresponding entry in `AGENT_CONFIG`

4. **Test the changes**
   ```bash
   python test_system.py
   ```

5. **Generate sample reports**
   ```bash
   python example_usage.py
   ```

6. **Iterate and refine**
   - Review output quality
   - Adjust prompts as needed
   - Re-test

---

## 💡 Common Customization Scenarios

### Scenario 1: Add Institution-Specific Guidelines
```python
self.system_prompt = """...[existing prompt]...
ADDITIONAL INSTITUTIONAL GUIDELINES:
- Use facility-specific reference ranges
- Include radiologist name in report
- Follow department template format
..."""
```

### Scenario 2: Focus on Specific Pathology
```python
# For oncology-focused liver imaging
self.system_prompt = """...[existing prompt]...
ONCOLOGY FOCUS:
- Describe all lesions with LI-RADS classification if applicable
- Report enhancement patterns
- Assess for washout characteristics
- Compare with prior studies if mentioned
..."""
```

### Scenario 3: Pediatric Specialization
```python
self.system_prompt = """You are a pediatric radiologist...
Guidelines:
- Use age-appropriate reference ranges
- Consider developmental variants
- Note growth parameters
- Use child-friendly terminology where appropriate
..."""
```

---

## ✅ Validation Checklist

After customizing prompts:

- [ ] Syntax is correct (no syntax errors in Python)
- [ ] Prompt is clear and specific
- [ ] Medical terminology is accurate
- [ ] Reference ranges are included
- [ ] Normal findings handling is specified
- [ ] Test passes (`python test_system.py`)
- [ ] Sample output is reviewed
- [ ] Prompt is documented in config.py
- [ ] Changes are backed up

---

## 🎯 Summary

**You now have 6 specialized organ agents**:
1. LiverAgent
2. GallbladderAgent
3. PancreasAgent
4. SpleenAgent
5. KidneyAgent
6. AortaAgent

Each can be **independently customized** with domain-specific prompts and guidelines.

**Benefits**:
- Higher quality, specialized reports
- Organ-specific medical knowledge
- Relevant measurement guidelines
- Better clinical accuracy
- Easy to customize per organ

**To customize**: Edit the `system_prompt` in each agent's `__init__` method in `radiology_agent_system.py`.

---

*Happy customizing!* 🎨🏥
