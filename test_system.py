"""
Quick Test Script for Radiology Report Generator
Tests all components of the multi-agent system
"""

import os
import sys
from radiology_agent_system import (
    RadiologyReportGenerator,
    CentralAgent,
    SplitterAgent,
    OrganAgent,
    ImpressionAgent
)

# Test data
MINIMAL_TEST = """Liver
- NP
GB
- NP
Pancreas
- NP
Spleen
- NP
Kidney
- NP
Aorta
- NP
Comment
- No significant findings"""

COMPLEX_TEST = """Liver
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


def test_api_connection():
    """Test 1: Verify API connection"""
    print("\n" + "="*80)
    print("TEST 1: API Connection")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ FAILED: GOOGLE_API_KEY not set")
        print("   Please run: export GOOGLE_API_KEY='your-key-here'")
        return False
    
    print(f"✓ API key found: {api_key[:20]}...")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        print("✓ Google Generative AI client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_splitter_agent():
    """Test 2: Splitter Agent"""
    print("\n" + "="*80)
    print("TEST 2: Splitter Agent")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ SKIPPED: No API key")
        return False
    
    try:
        splitter = SplitterAgent(api_key)
        print("✓ Splitter agent created")
        
        print("\nTesting with minimal data...")
        patient_info = splitter.split(MINIMAL_TEST)
        print(f"✓ Parsed liver: {patient_info.liver[:50]}...")
        print(f"✓ Parsed GB: {patient_info.gb[:50] if patient_info.gb else 'Empty'}...")
        print(f"✓ Parsed comment: {patient_info.comment[:50] if patient_info.comment else 'Empty'}...")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_organ_agents():
    """Test 3: Individual Organ Agents"""
    print("\n" + "="*80)
    print("TEST 3: Individual Organ Agents")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ SKIPPED: No API key")
        return False
    
    try:
        from radiology_agent_system import LiverAgent, GallbladderAgent, PancreasAgent
        
        print("✓ Liver agent created")
        liver_agent = LiverAgent(api_key)
        
        print("✓ Gallbladder agent created")
        gb_agent = GallbladderAgent(api_key)
        
        print("✓ Pancreas agent created")
        pancreas_agent = PancreasAgent(api_key)
        
        print("\nGenerating test report for 'NP' finding...")
        report = liver_agent.generate_report("- NP")
        print(f"✓ Generated report: {report[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_impression_agent():
    """Test 4: Impression Agent"""
    print("\n" + "="*80)
    print("TEST 4: Impression Agent")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ SKIPPED: No API key")
        return False
    
    try:
        impression_agent = ImpressionAgent(api_key)
        print("✓ Impression agent created")
        
        sample_report = """LIVER: No significant abnormality detected.
GALLBLADDER: Multiple gallbladder stones noted."""
        
        print("\nGenerating impression...")
        impression = impression_agent.generate_impression(sample_report, "Cholelithiasis")
        print(f"✓ Generated impression: {impression[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_full_workflow():
    """Test 5: Full Workflow (Single Patient)"""
    print("\n" + "="*80)
    print("TEST 5: Full Workflow - Single Patient")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ SKIPPED: No API key")
        return False
    
    try:
        generator = RadiologyReportGenerator(api_key)
        print("✓ Generator initialized")
        
        print("\nProcessing minimal test case...")
        report = generator.process_single_patient(MINIMAL_TEST)
        
        print("\n" + "-"*80)
        print("GENERATED REPORT:")
        print("-"*80)
        print(report[:500] + "..." if len(report) > 500 else report)
        
        # Save report
        output_file = os.path.join(generator.output_dir, "test_minimal_report.txt")
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"\n✓ Report saved to: {output_file}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_case():
    """Test 6: Complex Case with Multiple Organs"""
    print("\n" + "="*80)
    print("TEST 6: Complex Case")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ SKIPPED: No API key")
        return False
    
    try:
        generator = RadiologyReportGenerator(api_key)
        print("✓ Generator initialized")
        
        print("\nProcessing complex test case...")
        print("(This includes: AAA, cholecystitis, hydronephrosis, adenoma, etc.)")
        
        report = generator.process_single_patient(COMPLEX_TEST)
        
        # Save report
        output_file = os.path.join(generator.output_dir, "test_complex_report.txt")
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"✓ Report saved to: {output_file}")
        print(f"✓ Report length: {len(report)} characters")
        
        # Check if key findings are mentioned
        checks = {
            "AAA": "aneur" in report.lower(),
            "Cholecystitis": "cholecyst" in report.lower(),
            "Adenoma": "adenoma" in report.lower(),
            "Hydronephrosis": "hydroneph" in report.lower()
        }
        
        print("\nKey findings verification:")
        for finding, present in checks.items():
            status = "✓" if present else "❌"
            print(f"  {status} {finding}: {'Found' if present else 'Not found'}")
        
        return all(checks.values())
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processing():
    """Test 7: Batch Processing"""
    print("\n" + "="*80)
    print("TEST 7: Batch Processing")
    print("="*80)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ SKIPPED: No API key")
        return False
    
    try:
        generator = RadiologyReportGenerator(api_key)
        print("✓ Generator initialized")
        
        print("\nProcessing 2-patient batch...")
        patient_list = [MINIMAL_TEST, COMPLEX_TEST]
        output_file = generator.process_batch(patient_list, "2024-01-15-test")
        
        print(f"✓ Batch report saved to: {output_file}")
        
        # Verify file exists and has content
        with open(output_file, 'r') as f:
            content = f.read()
            patient_count = content.count("PATIENT")
            print(f"✓ Found {patient_count} patient sections in report")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     RADIOLOGY REPORT GENERATOR - TEST SUITE                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    tests = [
        ("API Connection", test_api_connection),
        ("Splitter Agent", test_splitter_agent),
        ("Organ Agents", test_organ_agents),
        ("Impression Agent", test_impression_agent),
        ("Full Workflow", test_full_workflow),
        ("Complex Case", test_complex_case),
        ("Batch Processing", test_batch_processing),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
    
    print("\n" + "="*80)


def main():
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        test_map = {
            "api": test_api_connection,
            "splitter": test_splitter_agent,
            "organ": test_organ_agents,
            "impression": test_impression_agent,
            "workflow": test_full_workflow,
            "complex": test_complex_case,
            "batch": test_batch_processing,
        }
        
        if test_name in test_map:
            test_map[test_name]()
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available tests: {', '.join(test_map.keys())}")
    else:
        run_all_tests()


if __name__ == "__main__":
    main()
