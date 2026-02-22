
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_generator import generate_pdf_report

try:
    print("Generating PDF report...")
    pdf_bytes = generate_pdf_report(
        report_type="Thesis Verification Report",
        date_range="Last 7 Days",
        include_charts=True,
        include_raw=True,
        executive_summary=True
    )
    
    if len(pdf_bytes) > 1000:
        print(f"Success! PDF generated with size: {len(pdf_bytes)} bytes")
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("Saved to test_report.pdf")
    else:
        print("Error: PDF too small, something went wrong.")
        sys.exit(1)

except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
