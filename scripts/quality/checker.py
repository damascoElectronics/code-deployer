#!/usr/bin/env python3
"""
Main Code Quality Checker
Orchestrates all quality analysis tools for Google Python Style Guide compliance
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

from quality.database_manager import QualityDatabaseManager
from quality.google_style_validator import GoogleStyleValidator
from quality.utils.style_checker import StyleCheckerUtils
from quality.utils.scoring import QualityScorer
from common.logger import get_logger
from common.config_loader import load_config
from common.pipeline_utils import get_pipeline_info

logger = get_logger(__name__)

class CodeQualityChecker:
    """Main coordinator for code quality analysis"""
    
    def __init__(self, config_path: str = "config/quality-gates.json"):
        """Initialize quality checker"""
        self.config = load_config(config_path)
        self.db_manager = QualityDatabaseManager()
        self.style_checker = StyleCheckerUtils()
        self.scorer = QualityScorer(self.config)
        self.scan_id = self.db_manager.generate_scan_id()
        
    def find_python_files(self) -> List[str]:
        """Find all Python files to analyze"""
        logger.info("🔍 Finding Python files to analyze...")
        
        python_files = []
        scan_dirs = ['local/log_processor', 'remote/log_collector', 'scripts']
        
        for scan_dir in scan_dirs:
            if Path(scan_dir).exists():
                for py_file in Path(scan_dir).rglob('*.py'):
                    if not self._should_skip_file(py_file):
                        python_files.append(str(py_file))
        
        logger.info(f"📁 Found {len(python_files)} Python files to analyze")
        return python_files
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = self.config.get('skip_patterns', [
            '__pycache__', '.pyc', 'test_', 'tests/', '.git/'
        ])
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def run_quality_analysis(self) -> Dict[str, Any]:
        """Run complete quality analysis"""
        start_time = time.time()
        
        logger.info("🚀 Starting Google Python Style Guide compliance check...")
        
        # Start scan tracking
        pipeline_info = get_pipeline_info()
        scan_id = self.db_manager.start_scan(pipeline_info)
        
        # Find files to analyze
        python_files = self.find_python_files()
        if not python_files:
            logger.warning("⚠️ No Python files found to analyze")
            return {'success': False, 'message': 'No Python files found'}
        
        # Run all quality tools
        all_results = []
        
        # Pylint (Google Style Guide)
        logger.info("🔍 Running Pylint analysis...")
        pylint_result = self.style_checker.run_pylint(python_files)
        all_results.append(pylint_result)
        
        # Black (Code Formatting)
        logger.info("🔍 Running Black formatting check...")
        black_result = self.style_checker.run_black(python_files)
        all_results.append(black_result)
        
        # isort (Import Sorting)
        logger.info("🔍 Running isort import sorting check...")
        isort_result = self.style_checker.run_isort(python_files)
        all_results.append(isort_result)
        
        # MyPy (Type Checking)
        logger.info("🔍 Running MyPy type checking...")
        mypy_result = self.style_checker.run_mypy(python_files)
        all_results.append(mypy_result)
        
        # Google Style Validator (Custom checks)
        logger.info("🔍 Running Google Style validations...")
        google_result = self._run_google_validator(python_files)
        all_results.append(google_result)
        
        # Store results in database
        total_issues = self.db_manager.store_results(scan_id, all_results)
        
        # Calculate quality score
        quality_score = self.scorer.calculate_overall_score(all_results, len(python_files))
        
        # Complete scan
        duration = int(time.time() - start_time)
        self.db_manager.complete_scan(scan_id, len(python_files), total_issues, quality_score, duration)
        
        # Generate summary
        summary = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': len(python_files),
            'total_issues': total_issues,
            'quality_score': quality_score,
            'duration_seconds': duration,
            'tools_run': [r['tool'] for r in all_results if r['success']],
            'database_file': self.db_manager.db_path,
            'success': True
        }
        
        # Save summary for pipeline
        self._save_summary(summary)
        
        logger.info(f"✅ Quality analysis completed! Score: {quality_score:.1f}/100")
        return summary
    
    def _run_google_validator(self, python_files: List[str]) -> Dict[str, Any]:
        """Run Google-specific style validations"""
        validator = GoogleStyleValidator()
        all_issues = []
        
        for file_path in python_files:
            try:
                issues = validator.validate_file(file_path)
                all_issues.extend(issues)
            except Exception as e:
                logger.warning(f"Failed to validate {file_path}: {e}")
        
        return {
            'tool': 'google-validator',
            'issues': all_issues,
            'success': True
        }
    
    def _save_summary(self, summary: Dict[str, Any]):
        """Save summary for pipeline artifacts"""
        os.makedirs('artifacts/reports/quality', exist_ok=True)
        
        with open('artifacts/reports/quality/code-quality-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Also save in root for backward compatibility
        with open('code-quality-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

def main():
    """Main entry point"""
    try:
        checker = CodeQualityChecker()
        result = checker.run_quality_analysis()
        
        if result['success']:
            # Check quality gates
            quality_score = result['quality_score']
            total_issues = result['total_issues']
            
            min_score = checker.config.get('quality_gates', {}).get('overall_score_minimum', 70)
            max_issues = checker.config.get('quality_gates', {}).get('maximum_total_issues', 50)
            
            if quality_score < min_score:
                logger.error(f"❌ Quality score {quality_score:.1f} below minimum {min_score}")
                return 1
            elif total_issues > max_issues:
                logger.error(f"❌ Too many issues: {total_issues} > {max_issues}")
                return 1
            else:
                logger.info("✅ Quality gates passed!")
                return 0
        else:
            logger.error(f"❌ Quality analysis failed: {result.get('message', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Quality checker failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())