#!/usr/bin/env python3
"""
Main Security Vulnerability Scanner
Orchestrates vulnerability scanning with database storage
"""
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.database_manager import SecurityDatabaseManager
from security.cpe_generator import CPEGenerator
from security.sbom_generator import SBOMGenerator
from security.utils.scanner_parsers import ScannerParsers
from security.utils.vulnerability_analyzer import VulnerabilityAnalyzer
from common.logger import get_logger
from common.config_loader import load_config
from common.pipeline_utils import get_pipeline_info

logger = get_logger(__name__)

class SecurityScanner:
    """Main coordinator for security vulnerability scanning"""
    
    def __init__(self, config_path: str = "config/scanner-config.json"):
        """Initialize security scanner"""
        self.config = load_config(config_path)
        self.db_manager = SecurityDatabaseManager()
        self.cpe_generator = CPEGenerator()
        self.sbom_generator = SBOMGenerator()
        self.scanner_parsers = ScannerParsers()
        self.vulnerability_analyzer = VulnerabilityAnalyzer()
        
    def find_requirements_files(self) -> List[str]:
        """Find all requirements.txt files to scan"""
        logger.info("🔍 Finding requirements files to scan...")
        
        requirements_files = [
            "local/log_processor/requirements.txt",
            "remote/log_collector/requirements.txt"
        ]
        
        existing_files = [f for f in requirements_files if Path(f).exists()]
        logger.info(f"📄 Found {len(existing_files)} requirements files")
        return existing_files
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run complete security vulnerability scan"""
        start_time = time.time()
        
        logger.info("🛡️ Starting security vulnerability scan...")
        
        # Start scan tracking
        pipeline_info = get_pipeline_info()
        scan_type = os.environ.get('SCAN_TYPE', 'manual')
        scan_id = self.db_manager.start_scan(scan_type, pipeline_info)
        
        # Find requirements files
        requirements_files = self.find_requirements_files()
        if not requirements_files:
            logger.warning("⚠️ No requirements files found to scan")
            return {'success': False, 'message': 'No requirements files found'}
        
        total_packages = 0
        total_vulnerabilities = 0
        
        # Process each requirements file
        for req_file in requirements_files:
            logger.info(f"📦 Processing {req_file}...")
            
            # Generate CPE assets
            packages = self.cpe_generator.parse_requirements_file(req_file)
            logger.info(f"Found {len(packages)} packages in {req_file}")
            
            # Store packages in database
            package_ids = {}
            for pkg in packages:
                package_id = self.db_manager.store_package(
                    pkg['name'], pkg['version'], pkg['cpe_id'],
                    pkg['source_file'], pkg.get('line_number')
                )
                package_ids[pkg['name']] = package_id
                total_packages += 1
            
            # Run vulnerability scans
            scan_results = self._run_vulnerability_scans(req_file)
            
            # Process and store vulnerabilities
            for tool_name, tool_result in scan_results.items():
                if not tool_result['success']:
                    continue
                
                vulnerabilities = self.scanner_parsers.parse_results(tool_name, tool_result)
                
                for vuln in vulnerabilities:
                    package_name = vuln.get('package_name', '')
                    if package_name in package_ids:
                        stored = self.db_manager.store_vulnerability(
                            package_ids[package_name], scan_id, vuln, tool_name
                        )
                        if stored:
                            total_vulnerabilities += 1
        
        # Generate SBOM
        logger.info("📋 Generating Software Bill of Materials...")
        sbom_files = self.sbom_generator.generate_sbom(requirements_files)
        
        # Calculate scan duration
        duration = int(time.time() - start_time)
        
        # Complete scan
        self.db_manager.complete_scan(scan_id, total_packages, total_vulnerabilities, duration)
        
        # Generate summary
        summary = self._generate_summary(scan_id, total_packages, total_vulnerabilities, duration, sbom_files)
        
        # Save summary
        self._save_summary(summary)
        
        logger.info(f"✅ Security scan completed! Found {total_vulnerabilities} vulnerabilities")
        return summary
    
    def _run_vulnerability_scans(self, requirements_file: str) -> Dict[str, Dict[str, Any]]:
        """Run all configured vulnerability scanners"""
        results = {}
        
        # Safety scan
        logger.info(f"🔍 Running Safety scan on {requirements_file}...")
        results['safety'] = self.scanner_parsers.run_safety_scan(requirements_file)
        
        # pip-audit scan
        logger.info(f"🔍 Running pip-audit scan on {requirements_file}...")
        results['pip-audit'] = self.scanner_parsers.run_pip_audit_scan(requirements_file)
        
        # Add more scanners as configured
        if self.config.get('enable_grype', False):
            logger.info(f"🔍 Running Grype scan on {requirements_file}...")
            results['grype'] = self.scanner_parsers.run_grype_scan(requirements_file)
        
        return results
    
    def _generate_summary(self, scan_id: str, total_packages: int, 
                         total_vulnerabilities: int, duration: int, sbom_files: List[str]) -> Dict[str, Any]:
        """Generate scan summary"""
        # Get vulnerability breakdown
        vulnerability_summary = self.db_manager.get_vulnerability_summary(scan_id)
        
        summary = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'scan_type': os.environ.get('SCAN_TYPE', 'manual'),
            'packages_scanned': total_packages,
            'total_vulnerabilities': total_vulnerabilities,
            'vulnerability_breakdown': vulnerability_summary,
            'duration_seconds': duration,
            'sbom_files': sbom_files,
            'database_file': self.db_manager.db_path,
            'success': True
        }
        
        return summary
    
    def _save_summary(self, summary: Dict[str, Any]):
        """Save summary for pipeline artifacts"""
        os.makedirs('artifacts/reports/security', exist_ok=True)
        
        with open('artifacts/reports/security/vulnerability-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Also save in root for backward compatibility
        with open('vulnerability-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

def main():
    """Main entry point"""
    try:
        scanner = SecurityScanner()
        result = scanner.run_security_scan()
        
        if result['success']:
            # Check security gates
            vulnerability_breakdown = result['vulnerability_breakdown']
            critical = vulnerability_breakdown.get('critical', 0)
            high = vulnerability_breakdown.get('high', 0)
            
            if critical > 0:
                logger.error(f"❌ Critical vulnerabilities found: {critical}")
                return 1
            elif high > 10:  # Configurable threshold
                logger.error(f"❌ Too many high-severity vulnerabilities: {high}")
                return 1
            else:
                logger.info("✅ Security scan passed!")
                return 0
        else:
            logger.error(f"❌ Security scan failed: {result.get('message', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Security scanner failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())