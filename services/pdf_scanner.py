import os
import re
import hashlib
from typing import Dict, List, Tuple
from datetime import datetime

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFScanner:
    
    SUSPICIOUS_PATTERNS = [
        (r'/JavaScript', 'JavaScript code detected'),
        (r'/JS\s', 'Embedded JavaScript'),
        (r'/OpenAction', 'Auto-execute action'),
        (r'/AA\s', 'Additional actions'),
        (r'/Launch', 'Launch action'),
        (r'/EmbeddedFile', 'Embedded file'),
        (r'/RichMedia', 'Rich media content'),
        (r'/XFA', 'XFA forms (potential exploit)'),
        (r'eval\s*\(', 'Eval function'),
        (r'unescape\s*\(', 'Unescape function'),
        (r'/AcroForm', 'AcroForm (potential exploit)'),
        (r'/JBIG2Decode', 'JBIG2 decode (CVE vulnerability)'),
        (r'cmd\.exe', 'Windows command execution'),
        (r'/bin/sh', 'Unix shell execution'),
        (r'powershell', 'PowerShell execution'),
        (r'http://', 'HTTP URL (potential C2)'),
        (r'https://', 'HTTPS URL (potential C2)'),
    ]
    
    MALWARE_HASHES = {
        'd41d8cd98f00b204e9800998ecf8427e',
    }
    
    def __init__(self):
        self.scan_results = []
    
    def calculate_hash(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def scan_pdf(self, file_path: str) -> Dict:
        result = {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'scan_time': datetime.now().isoformat(),
            'file_size': os.path.getsize(file_path),
            'risk_score': 0,
            'verdict': 'CLEAN',
            'threats_found': [],
            'metadata': {}
        }
        
        file_hash = self.calculate_hash(file_path)
        result['file_hash'] = file_hash
        
        # Check against Threat Intel API (VirusTotal)
        try:
            from services.threat_intel import threat_intel
            vt_result = threat_intel.check_file_hash(file_hash)
            
            if vt_result.get('is_malicious'):
                 result['risk_score'] = 100
                 result['verdict'] = 'MALICIOUS'
                 result['threats_found'].append(f"VirusTotal Detection: {vt_result.get('threat_name', 'Malicious File')}")
                 result['metadata']['virustotal'] = vt_result
                 return result
            elif vt_result.get('is_suspicious'):
                 result['risk_score'] = max(result['risk_score'], 80)
                 result['threats_found'].append(f"VirusTotal Suspicion: {vt_result.get('threat_name', 'Suspicious File')}")
        except Exception as e:
            pass
        
        if file_hash in self.MALWARE_HASHES:
            result['risk_score'] = 100
            result['verdict'] = 'MALWARE'
            result['threats_found'].append('Known malware signature detected')
            return result
        
        try:
            with open(file_path, 'rb') as f:
                raw_content = f.read()
                raw_text = raw_content.decode('latin-1', errors='ignore')
        except Exception as e:
            result['threats_found'].append(f'Error reading file: {str(e)}')
            return result
        
        for pattern, description in self.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            if matches:
                result['threats_found'].append(f'{description} ({len(matches)} instances)')
                result['risk_score'] += 15
        
        if PDF_AVAILABLE:
            try:
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    result['metadata']['pages'] = len(pdf_reader.pages)
                    
                    if pdf_reader.metadata:
                        result['metadata']['author'] = str(pdf_reader.metadata.get('/Author', 'Unknown'))
                        result['metadata']['creator'] = str(pdf_reader.metadata.get('/Creator', 'Unknown'))
                        result['metadata']['producer'] = str(pdf_reader.metadata.get('/Producer', 'Unknown'))
                    
                    for i, page in enumerate(pdf_reader.pages[:5]):
                        try:
                            text = page.extract_text()
                            if text:
                                if re.search(r'(password|credential|login|bank|account)', text, re.IGNORECASE):
                                    if re.search(r'(urgent|verify|suspended|click here)', text, re.IGNORECASE):
                                        result['threats_found'].append(f'Phishing content detected on page {i+1}')
                                        result['risk_score'] += 25
                        except:
                            pass
            except Exception as e:
                result['threats_found'].append(f'PDF parsing error: {str(e)}')
        
        result['risk_score'] = min(100, result['risk_score'])
        
        if result['risk_score'] >= 70:
            result['verdict'] = 'MALICIOUS'
        elif result['risk_score'] >= 40:
            result['verdict'] = 'SUSPICIOUS'
        elif result['risk_score'] >= 20:
            result['verdict'] = 'POTENTIALLY_UNSAFE'
        else:
            result['verdict'] = 'CLEAN'
        
        self.scan_results.append(result)
        return result
    
    def scan_directory(self, directory: str) -> List[Dict]:
        results = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    result = self.scan_pdf(file_path)
                    results.append(result)
        return results
    
    def get_summary(self) -> Dict:
        total = len(self.scan_results)
        malicious = sum(1 for r in self.scan_results if r['verdict'] == 'MALICIOUS')
        suspicious = sum(1 for r in self.scan_results if r['verdict'] == 'SUSPICIOUS')
        clean = sum(1 for r in self.scan_results if r['verdict'] == 'CLEAN')
        
        return {
            'total_scanned': total,
            'malicious': malicious,
            'suspicious': suspicious,
            'clean': clean,
            'potentially_unsafe': total - malicious - suspicious - clean
        }


def scan_pdf_file(file_path: str) -> Dict:
    scanner = PDFScanner()
    return scanner.scan_pdf(file_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = scan_pdf_file(sys.argv[1])
        print(f"\nFile: {result['file_name']}")
        print(f"Verdict: {result['verdict']}")
        print(f"Risk Score: {result['risk_score']}/100")
        print(f"Threats: {len(result['threats_found'])}")
        for threat in result['threats_found']:
            print(f"  - {threat}")
