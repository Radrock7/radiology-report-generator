# System Architecture

## Overview

The Multi-Agent Radiology Report Generator uses a **hierarchical agent architecture** where specialized AI agents work together to generate comprehensive medical reports.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                   │
│                  (Raw Patient Data - Text Format)                   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   SPLITTER AGENT                             │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │ Role: Parse and Structure Data                      │    │
    │  │ Input: Raw text                                     │    │
    │  │ Output: Structured JSON                             │    │
    │  │ {                                                   │    │
    │  │   "liver": "...",                                   │    │
    │  │   "gb": "...",                                      │    │
    │  │   "pancreas": "...",                                │    │
    │  │   "others": [{"organ": "X", "findings": "..."}]    │    │
    │  │ }                                                   │    │
    │  └─────────────────────────────────────────────────────┘    │
    └──────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
    ┌────────────────────────────────────────────────────────────────┐
    │                   CENTRAL AGENT                                 │
    │  ┌────────────────────────────────────────────────────────┐    │
    │  │ Role: Orchestrate Workflow                             │    │
    │  │ • Route data to appropriate agents                     │    │
    │  │ • Maintain processing order                            │    │
    │  │ • Combine agent outputs                                │    │
    │  │ • Coordinate report generation                         │    │
    │  └────────────────────────────────────────────────────────┘    │
    └─┬────┬────┬────┬────┬────┬────┬────────────────────────────────┘
      │    │    │    │    │    │    │
      ▼    ▼    ▼    ▼    ▼    ▼    ▼
   ┌───┐┌───┐┌────┐┌────┐┌────┐┌────┐┌──────┐
   │ L ││GB ││Pan.││Spl.││Kid.││Aor.││Others│
   │ i ││   ││    ││    ││    ││    ││      │
   │ v ││Ag.││Ag. ││Ag. ││Ag. ││Ag. ││ Ag.  │
   │ e ││   ││    ││    ││    ││    ││      │
   │ r ││   ││    ││    ││    ││    ││(Loop)│
   │   ││   ││    ││    ││    ││    ││      │
   │Ag.││   ││    ││    ││    ││    ││      │
   └─┬─┘└─┬─┘└──┬─┘└──┬─┘└──┬─┘└──┬─┘└───┬──┘
     │    │     │     │     │     │      │
     │    │     │     │     │     │      │  Each Agent:
     │    │     │     │     │     │      │  • Specialized knowledge
     │    │     │     │     │     │      │  • Medical terminology
     │    │     │     │     │     │      │  • Measurement handling
     │    │     │     │     │     │      │  • Standard formatting
     └────┴─────┴─────┴─────┴─────┴──────┘
                      │
                      │ All reports collected
                      ▼
    ┌──────────────────────────────────────────────────────────┐
    │               CENTRAL AGENT (Combine)                     │
    │  ┌─────────────────────────────────────────────────┐     │
    │  │ Combine all organ reports in proper order:      │     │
    │  │                                                  │     │
    │  │ FINDINGS:                                        │     │
    │  │ LIVER: [liver report]                           │     │
    │  │ GALLBLADDER: [gb report]                        │     │
    │  │ PANCREAS: [pancreas report]                     │     │
    │  │ ...                                             │     │
    │  └─────────────────────────────────────────────────┘     │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       │ Complete findings report
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │               IMPRESSION AGENT                            │
    │  ┌─────────────────────────────────────────────────┐     │
    │  │ Role: Generate Clinical Summary                 │     │
    │  │ • Analyze all findings                          │     │
    │  │ • Identify key pathologies                      │     │
    │  │ • Prioritize by clinical importance             │     │
    │  │ • Generate concise impression                   │     │
    │  └─────────────────────────────────────────────────┘     │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │                  FINAL REPORT OUTPUT                      │
    │  ┌─────────────────────────────────────────────────┐     │
    │  │ RADIOLOGY REPORT                                │     │
    │  │                                                  │     │
    │  │ FINDINGS:                                        │     │
    │  │ [All organ sections combined]                   │     │
    │  │                                                  │     │
    │  │ IMPRESSION:                                      │     │
    │  │ [Clinical summary]                              │     │
    │  └─────────────────────────────────────────────────┘     │
    └──────────────────────────────────────────────────────────┘
```

## Agent Details

### 1. Splitter Agent
**Purpose**: Parse raw patient data into structured format

**Input Example**:
```
Liver
- NP
GB
Polyp: (2.5mm)
...
```

**Output Example**:
```json
{
  "liver": "- NP",
  "gb": "Polyp: (2.5mm)",
  "pancreas": "...",
  ...
}
```

**Technology**: Gemini 2.0 Flash with specialized parsing prompt

---

### 2. Central Agent (Orchestrator)
**Purpose**: Coordinate all agents and manage workflow

**Responsibilities**:
- Initialize all specialized agents
- Route data to appropriate agents
- Maintain organ processing order
- Combine reports into final document
- Handle batch processing

**Flow**:
```
Central Agent receives structured data
  ↓
For each organ in order:
  → Send data to organ-specific agent
  → Receive formatted report section
  → Add to report collection
  ↓
For each "other" organ:
  → Loop through Others Agent
  → Add each section to collection
  ↓
Combine all sections
  ↓
Send to Impression Agent
  ↓
Return final report
```

---

### 3. Organ-Specific Agents (6 individual specialized agents)

Each standard organ has its own specialized agent with domain-specific knowledge:

#### Liver Agent
- **Specialization**: Hepatic imaging, liver pathology
- **Handles**: Liver size, echotexture, margins, focal lesions, hepatic vasculature, hepatomegaly
- **Key Metrics**: Liver span (cm), focal lesion characteristics
- **Medical Knowledge**: Hepatic anatomy, common liver pathologies

#### Gallbladder Agent
- **Specialization**: Gallbladder and biliary system imaging
- **Handles**: GB wall thickness, stones, polyps, CBD diameter, pericholecystic fluid
- **Key Metrics**: Wall thickness (<3mm normal), CBD diameter (<6mm normal), stone sizes
- **Medical Knowledge**: Cholelithiasis, cholecystitis, biliary dilation

#### Pancreas Agent
- **Specialization**: Pancreatic imaging
- **Handles**: Pancreatic size (head/body/tail), echotexture, MPD diameter, masses, cysts
- **Key Metrics**: MPD diameter (<3mm normal), regional measurements
- **Medical Knowledge**: Pancreatic anatomy, atrophy, lipomatosis

#### Spleen Agent
- **Specialization**: Splenic imaging
- **Handles**: Splenic size, echotexture, splenomegaly, focal lesions, accessory spleens
- **Key Metrics**: Size (<12-13cm normal), splenomegaly threshold (>13cm)
- **Medical Knowledge**: Splenic pathology, size variations

#### Kidney Agent
- **Specialization**: Renal imaging
- **Handles**: Bilateral kidney assessment, size, cortical thickness, hydronephrosis, stones, cysts
- **Key Metrics**: Size (10-12cm normal), cortical measurements, hydronephrosis grading
- **Medical Knowledge**: Renal parenchymal disease, anatomical variants

#### Aorta Agent
- **Specialization**: Vascular imaging with focus on aorta
- **Handles**: Aortic caliber, aneurysms, mural thrombus, calcifications, dissection
- **Key Metrics**: Diameter measurements, aneurysm threshold (>3cm abdominal)
- **Medical Knowledge**: Vascular pathology, urgent findings (dissection, large aneurysms)

**Common Features of All Specialized Agents**:
- Domain-specific medical terminology
- Organ-specific measurement ranges and thresholds
- Precise reporting guidelines
- Handles "NP" (No Pathology) gracefully
- Consistent professional formatting
- Clinical relevance focus

---

### 4. Impression Agent
**Purpose**: Generate clinical summary

**Process**:
1. Analyze complete findings report
2. Extract all abnormal findings
3. Prioritize by clinical importance
4. Consider original comments
5. Generate numbered list or statement

**Output Styles**:
- No findings: "No significant abnormality detected"
- Single finding: Brief statement
- Multiple findings: Numbered list by importance

---

## Data Flow

```
Raw Text → Parse → Structure → Route → Process → Combine → Summarize → Output
   (User)   (Split) (JSON)    (Central) (Agents) (Central) (Impress) (Report)
```

## Processing Order

The system maintains strict order:
1. Liver
2. Gallbladder (+ CBD)
3. Pancreas (+ MPD)
4. Spleen
5. Kidney
6. Aorta
7. Others (each organ separately)

This order ensures:
- Consistent report structure
- Professional formatting
- Easy comparison between reports
- Standard medical documentation

## Agent Communication

```
Central Agent
    ↓ (sends organ data)
Organ Agent
    ↓ (returns formatted text)
Central Agent
    ↓ (sends combined report)
Impression Agent
    ↓ (returns summary)
Central Agent
    ↓ (outputs final report)
User
```

## Batch Processing

```
Date Folder with Multiple Patients
         ↓
Central Agent processes each patient sequentially
         ↓
      Patient 1 → Full workflow → Report 1
      Patient 2 → Full workflow → Report 2
      Patient 3 → Full workflow → Report 3
         ↓
All reports combined into single file
         ↓
Output: radiology_reports_{date}.txt
```

## Technology Stack

- **Language**: Python 3.8+
- **AI Model**: Gemini 2.0 Flash
- **API**: Google API
- **Data Format**: JSON for intermediate, TXT for output
- **Architecture Pattern**: Multi-agent hierarchical

## Key Design Principles

1. **Separation of Concerns**: Each agent has one clear responsibility
2. **Specialization**: Domain-specific knowledge in each organ agent
3. **Order Preservation**: Maintains medical documentation standards
4. **Scalability**: Easy to add new organ agents
5. **Modularity**: Agents can be used independently or together
6. **Error Handling**: Graceful degradation if any agent fails
7. **Consistency**: Standard output format across all reports

## Extension Points

The system can be extended at:
- **New Organ Agents**: Add specialized agents for new organs
- **Custom Formatting**: Modify report templates
- **Input Parsers**: Add PDF, DICOM, HL7 parsers
- **Output Formats**: Generate HTML, PDF, DICOM SR
- **Validation**: Add medical validation rules
- **Integration**: Connect to PACS, EHR systems

## Performance Characteristics

- **Processing Time**: ~30-60 seconds per patient (API dependent)
- **Batch Processing**: Sequential (can be parallelized)
- **Token Usage**: ~2000-4000 tokens per patient
- **Accuracy**: Depends on input quality and AI model
- **Consistency**: High (low temperature = 0.3)

## Security Considerations

- **API Key**: Stored in environment variables
- **Data**: Patient data not stored permanently
- **Output**: Saved to configurable directory
- **PHI**: No built-in PHI protection (add as needed)

---

This architecture ensures high-quality, consistent radiology report generation through specialized AI agents working together in a coordinated workflow.
