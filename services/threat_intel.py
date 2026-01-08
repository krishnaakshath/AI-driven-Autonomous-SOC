import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

CACHE_FILE = ".threat_intel_cache.json"
CACHE_DURATION = 3600


class ThreatIntelligence:
    
    def __init__(self):
        self.abuseipdb_key = os.getenv("ABUSEIPDB_API_KEY", "")
        self.virustotal_key = os.getenv("VIRUSTOTAL_API_KEY", "")
        self.otx_key = os.getenv("OTX_API_KEY", "")
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)
    
    def _is_cached(self, key: str) -> bool:
        if key in self.cache:
            cached_time = self.cache[key].get('timestamp', 0)
            if time.time() - cached_time < CACHE_DURATION:
                return True
        return False
    
    def check_ip_abuseipdb(self, ip: str) -> Dict:
        cache_key = f"abuseipdb_{ip}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        if not self.abuseipdb_key:
            return {"error": "API key not configured", "is_malicious": False}
        
        try:
            headers = {
                'Key': self.abuseipdb_key,
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip,
                'maxAgeInDays': 90
            }
            response = requests.get(
                'https://api.abuseipdb.com/api/v2/check',
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                result = {
                    'ip': ip,
                    'is_malicious': data.get('abuseConfidenceScore', 0) > 50,
                    'abuse_score': data.get('abuseConfidenceScore', 0),
                    'country': data.get('countryCode', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'total_reports': data.get('totalReports', 0),
                    'last_reported': data.get('lastReportedAt', None),
                    'source': 'AbuseIPDB'
                }
                self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
                self._save_cache()
                return result
        except Exception as e:
            return {"error": str(e), "is_malicious": False}
        
        return {"error": "API request failed", "is_malicious": False}
    
    def check_ip_virustotal(self, ip: str) -> Dict:
        cache_key = f"virustotal_{ip}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        if not self.virustotal_key:
            return {"error": "API key not configured", "is_malicious": False}
        
        try:
            headers = {'x-apikey': self.virustotal_key}
            response = requests.get(
                f'https://www.virustotal.com/api/v3/ip_addresses/{ip}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {}).get('attributes', {})
                stats = data.get('last_analysis_stats', {})
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                
                result = {
                    'ip': ip,
                    'is_malicious': malicious > 0 or suspicious > 2,
                    'malicious_votes': malicious,
                    'suspicious_votes': suspicious,
                    'country': data.get('country', 'Unknown'),
                    'as_owner': data.get('as_owner', 'Unknown'),
                    'reputation': data.get('reputation', 0),
                    'source': 'VirusTotal'
                }
                self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
                self._save_cache()
                return result
        except Exception as e:
            return {"error": str(e), "is_malicious": False}
        
        return {"error": "API request failed", "is_malicious": False}
    
    def get_otx_pulses(self, limit: int = 10) -> List[Dict]:
        cache_key = "otx_pulses"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        if not self.otx_key:
            return self._get_public_otx_pulses()
        
        try:
            headers = {'X-OTX-API-KEY': self.otx_key}
            response = requests.get(
                'https://otx.alienvault.com/api/v1/pulses/subscribed',
                headers=headers,
                params={'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                pulses = response.json().get('results', [])
                result = []
                for pulse in pulses[:limit]:
                    result.append({
                        'id': pulse.get('id'),
                        'name': pulse.get('name'),
                        'description': pulse.get('description', '')[:200],
                        'author': pulse.get('author_name'),
                        'created': pulse.get('created'),
                        'tags': pulse.get('tags', [])[:5],
                        'indicators': len(pulse.get('indicators', []))
                    })
                self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
                self._save_cache()
                return result
        except Exception as e:
            pass
        
        return self._get_public_otx_pulses()
    
    def _get_public_otx_pulses(self) -> List[Dict]:
        try:
            response = requests.get(
                'https://otx.alienvault.com/api/v1/pulses/activity',
                timeout=10
            )
            if response.status_code == 200:
                pulses = response.json().get('results', [])[:10]
                return [{
                    'id': p.get('id'),
                    'name': p.get('name'),
                    'description': p.get('description', '')[:200],
                    'author': p.get('author_name'),
                    'created': p.get('created'),
                    'tags': p.get('tags', [])[:5],
                    'indicators': len(p.get('indicators', []))
                } for p in pulses]
        except:
            pass
        return []
    
    def get_global_threat_stats(self) -> Dict:
        cache_key = "global_stats"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            response = requests.get(
                'https://otx.alienvault.com/api/v1/pulses/activity',
                timeout=10
            )
            
            if response.status_code == 200:
                pulses = response.json().get('results', [])
                
                country_counts = {}
                attack_types = {}
                
                for pulse in pulses[:50]:
                    tags = pulse.get('tags', [])
                    for tag in tags:
                        tag_lower = tag.lower()
                        if tag_lower in ['malware', 'ransomware', 'phishing', 'botnet', 'apt', 'ddos', 'exploit']:
                            attack_types[tag] = attack_types.get(tag, 0) + 1
                
                result = {
                    'total_pulses': len(pulses),
                    'attack_types': attack_types,
                    'last_updated': datetime.now().isoformat(),
                    'source': 'OTX AlienVault'
                }
                
                self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
                self._save_cache()
                return result
        except Exception as e:
            pass
        
        return {
            'total_pulses': 0,
            'attack_types': {},
            'last_updated': datetime.now().isoformat(),
            'source': 'Offline'
        }
    
    def check_ip(self, ip: str) -> Dict:
        results = {
            'ip': ip,
            'is_malicious': False,
            'sources': [],
            'details': {}
        }
        
        if self.abuseipdb_key:
            abuse_result = self.check_ip_abuseipdb(ip)
            if 'error' not in abuse_result:
                results['sources'].append('AbuseIPDB')
                results['details']['abuseipdb'] = abuse_result
                if abuse_result.get('is_malicious'):
                    results['is_malicious'] = True
        
        if self.virustotal_key:
            vt_result = self.check_ip_virustotal(ip)
            if 'error' not in vt_result:
                results['sources'].append('VirusTotal')
                results['details']['virustotal'] = vt_result
                if vt_result.get('is_malicious'):
                    results['is_malicious'] = True
        
        return results


threat_intel = ThreatIntelligence()


def check_ip_reputation(ip: str) -> Dict:
    return threat_intel.check_ip(ip)


def get_latest_threats() -> List[Dict]:
    return threat_intel.get_otx_pulses(10)


def get_threat_stats() -> Dict:
    return threat_intel.get_global_threat_stats()
