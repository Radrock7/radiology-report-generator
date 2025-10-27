"""
Example usage of the Radiology Report Generator
This script demonstrates how to use the system programmatically
"""

import os
from radiology_agent_system import RadiologyReportGenerator

# Sample patient data based on your example
SAMPLE_PATIENT_4 = """Liver
- NP
GB
Polyp:
- (2.5mm, 2.1mm, 1.6mm)
CBD
Diameter
- (1.6 mm)
Pancreas
- NP
MPD:
- (0.5 mm)
Spleen
- NP
Kidney
- NP
Aorta
- NP
Comment
- Gallbladder polyps"""

SAMPLE_PATIENT_1 = """Liver
- Echogenic Liver - H-R Contrast - Focal Spared Area - Fatty Change
GB - NP
CBD
Diameter - ( 3.9 mm)
Pancreas
MPD: - ( 0.6 mm)
Echo Level: - Hyper
Can't be seen: - Tail
Spleen - Accessory Spleen ( 8.6 x 5.8 mm )
Kidney
Dilated right renal pelvis with AP diameter of ( 19.2 mm) with a calculus noted at the proximal
ureter ( 10.9 mm)
Another calculus noted at the distal ureter ( 16.1 mm)
Ureter Dilatation - Right
Calculus:
- Right MP ( 3.6 mm)
Left renal calcification reported previously was not seen in today's scan.
Bladder - Not well distended
Prostate
- V= 39.9 cm3 ( 41.9 x 46.0 x 39.5 )3.14/6 mm
- Calc+
Aorta - Plaques: ( 15.8 x 2.4 mm) - Largest
Comment
- Poor Study, due to the bowel gas (+)
- Fatty liver
- Accessory spleen
- Right renal calculus
- Dilated right ureter with ureteric stones ( proximal and distal )
- Enlarged prostate with intra-prostatic calcifications
- Pancreas fatty changes
- Aortic plaques"""



def example_single_patient():
    """Example: Process a single patient"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Single Patient Processing")
    print("="*80)
    
    # Initialize generator
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Please set GOOGLE_API_KEY environment variable")
        return
    
    generator = RadiologyReportGenerator(api_key)
    
    # Process single patient
    report = generator.process_single_patient(SAMPLE_PATIENT_1)
    
    # Save report
    output_file = os.path.join(generator.output_dir, "example_single_patient.txt")
    with open(output_file, 'w') as f:
        f.write(report)
    
    print("\n" + "="*80)
    print("GENERATED REPORT:")
    print("="*80)
    print(report)
    print(f"\n✓ Saved to: {output_file}")


def example_batch_processing():
    """Example: Process multiple patients"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Batch Processing")
    print("="*80)
    
    # Initialize generator
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Please set GOOGLE_API_KEY environment variable")
        return
    
    generator = RadiologyReportGenerator(api_key)
    
    # Process batch
    patient_data_list = [SAMPLE_PATIENT_1, SAMPLE_PATIENT_4]
    date = "2024-01-15"
    
    output_file = generator.process_batch(patient_data_list, date)
    
    print(f"\n✓ All reports saved to: {output_file}")


def example_custom_workflow():
    """Example: Custom workflow using individual agents"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Custom Workflow with Individual Agents")
    print("="*80)
    
    from radiology_agent_system import CentralAgent, LiverAgent, GallbladderAgent
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Please set GOOGLE_API_KEY environment variable")
        return
    
    central = CentralAgent(api_key)
    
    # Step 1: Split data
    print("\nStep 1: Splitting data...")
    patient_info = central.splitter.split(SAMPLE_PATIENT_1)
    print(f"✓ Liver: {patient_info.liver}")
    print(f"✓ GB: {patient_info.gb}")
    print(f"✓ Comment: {patient_info.comment}")
    
    # Step 2: Use individual specialized agents
    print("\nStep 2: Using individual specialized agents...")
    
    # Demonstrate Liver Agent
    print("\n  → Using LiverAgent (specialized for hepatic imaging)...")
    liver_agent = LiverAgent(api_key)
    liver_report = liver_agent.generate_report(patient_info.liver)
    print(f"  ✓ Liver Report: {liver_report[:100]}...")
    
    # Demonstrate Gallbladder Agent
    print("\n  → Using GallbladderAgent (specialized for GB/biliary)...")
    gb_agent = GallbladderAgent(api_key)
    gb_report = gb_agent.generate_report(patient_info.gb)
    print(f"  ✓ GB Report: {gb_report[:100]}...")
    
    # Step 3: Generate full report using CentralAgent
    print("\nStep 3: Generating full report with CentralAgent...")
    full_report = central.process_patient(SAMPLE_PATIENT_1)
    print("✓ Full report generated with all 6 specialized organ agents")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         RADIOLOGY REPORT GENERATOR - EXAMPLES                ║
╚══════════════════════════════════════════════════════════════╝

Select an example to run:
1. Single Patient Processing
2. Batch Processing (3 patients)
3. Custom Workflow
""")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        example_single_patient()
    elif choice == "2":
        example_batch_processing()
    elif choice == "3":
        example_custom_workflow()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
