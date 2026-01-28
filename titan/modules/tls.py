"""
TLS Fingerprinting Module
=========================
Handles JA3 fingerprint randomization and cipher suite rotation.
"""

import ssl
import random
import hashlib
from typing import Dict, List, Any, Optional
from collections import namedtuple
import logging

TLSFingerprint = namedtuple('TLSFingerprint', [
    'ja3', 'ja3_hash', 'cipher_suites', 'extensions', 'elliptic_curves', 
    'signature_algorithms', 'versions'
])

class JA3Generator:
    """Generates realistic JA3 fingerprints for different browsers"""
    
    BROWSER_FINGERPRINTS = {
        'chrome_120': {
            'ja3': '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0',
            'cipher_suites': [4865, 4866, 4867, 49195, 49199, 49196, 49200, 52393, 52392, 49171, 49172, 156, 157, 47, 53],
            'extensions': [0, 23, 65281, 10, 11, 35, 16, 5, 13, 18, 51, 45, 43, 27, 17513],
            'elliptic_curves': [29, 23, 24],
            'signature_algorithms': [0],
            'versions': [771]
        },
        'firefox_120': {
            'ja3': '771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-51-43-13-45-28-27,29-23-24-25-256-257,0',
             'cipher_suites': [4865, 4867, 4866, 49195, 49199, 52393, 52392, 49196, 49200, 49162, 49161, 49171, 49172, 156, 157, 47, 53],
             'extensions': [0, 23, 65281, 10, 11, 35, 16, 5, 51, 43, 13, 45, 28, 27],
             'elliptic_curves': [29, 23, 24, 25, 256, 257],
             'signature_algorithms': [0],
             'versions': [771]
        }
    }
    
    def __init__(self, browser_type: str = 'chrome'):
        self.browser_type = browser_type
        
    def generate_fingerprint(self, randomize: bool = True) -> TLSFingerprint:
        base = self.BROWSER_FINGERPRINTS.get('chrome_120') # Default
        if 'firefox' in self.browser_type:
            base = self.BROWSER_FINGERPRINTS.get('firefox_120')
            
        fingerprint = base.copy()
        if randomize:
            # Simple shuffle of middle ciphers
            ciphers = fingerprint['cipher_suites'][:]
            if len(ciphers) > 4:
                # Keep first few and last few stable, shuffle middle
                mid = ciphers[2:-2]
                random.shuffle(mid)
                fingerprint['cipher_suites'] = ciphers[:2] + mid + ciphers[-2:]
        
        ja3_str = self._build_ja3(fingerprint)
        ja3_hash = hashlib.md5(ja3_str.encode()).hexdigest()
        
        return TLSFingerprint(
            ja3=ja3_str,
            ja3_hash=ja3_hash,
            cipher_suites=fingerprint['cipher_suites'],
            extensions=fingerprint['extensions'],
            elliptic_curves=fingerprint['elliptic_curves'],
            signature_algorithms=fingerprint['signature_algorithms'],
            versions=fingerprint['versions']
        )
        
    def _build_ja3(self, fp):
        return f"{fp['versions'][0]},{'-'.join(map(str, fp['cipher_suites']))},{'-'.join(map(str, fp['extensions']))},{'-'.join(map(str, fp['elliptic_curves']))},{'-'.join(map(str, fp['signature_algorithms']))}"


class TLSManager:
    def __init__(self, browser_type: str = 'chrome'):
        self.generator = JA3Generator(browser_type)
        self.current_fingerprint = None
        self.ssl_context = None
        self.rotate()
        
    def rotate(self):
        self.current_fingerprint = self.generator.generate_fingerprint()
        self.ssl_context = self._create_context()
        
    def _create_context(self):
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        # In a real implementation we would set ciphers here
        # context.set_ciphers(...) 
        # But python's ssl module is picky. We normally rely on lower level adapters
        # For now, just setting check_hostname to false to allow proxying/inspection if needed
        context.check_hostname = False
        return context
        
    def get_adapter_kwargs(self):
        """Returns kwargs to be used with requests adapter if applicable"""
        return {
            'ssl_context': self.ssl_context
        }
