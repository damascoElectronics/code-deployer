#!/usr/bin/env python3
"""
Google Python Style Guide Specific Validations
Custom checks beyond standard linters
Location: scripts/quality/google_style_validator.py
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

class GoogleStyleValidator:
    """Validator for Google Python Style Guide specific rules"""
    
    def __init__(self):
        self.issues = []
    
    def validate_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Validate a single Python file against Google style guide"""
        self.issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Parse AST for structural checks
            try:
                tree = ast.parse(content)
                self.check_ast_structure(tree, file_path)
            except SyntaxError as e:
                self.add_issue(file_path, e.lineno or 1, 'syntax-error', 
                             f"Syntax error: {e.msg}", 'error')
            
            # Line-by-line checks
            for line_num, line in enumerate(lines, 1):
                self.check_line_style(file_path, line_num, line)
            
            # Overall file structure checks
            self.check_file_structure(file_path, lines)
            
        except Exception as e:
            self.add_issue(file_path, 1, 'file-error', 
                         f"Could not process file: {e}", 'error')
        
        return self.issues
    
    def add_issue(self, file_path: str, line_num: int, rule_code: str, 
                  message: str, severity: str = 'warning'):
        """Add a style issue"""
        self.issues.append({
            'path': file_path,
            'line': line_num,
            'column': 1,
            'type': 'google-style',
            'message': message,
            'symbol': rule_code,
            'severity': severity
        })
    
    def check_line_style(self, file_path: str, line_num: int, line: str):
        """Check line-level style issues"""
        
        # Check line length (Google recommends 80, allows 100)
        if len(line) > 100:
            self.add_issue(file_path, line_num, 'line-too-long',
                         f"Line too long ({len(line)} > 100 characters)")
        
        # Check for trailing whitespace
        if line.rstrip() != line and line.strip():
            self.add_issue(file_path, line_num, 'trailing-whitespace',
                         "Trailing whitespace found")
        
        # Check for tabs (Google style uses spaces)
        if '\t' in line:
            self.add_issue(file_path, line_num, 'tab-character',
                         "Tab character found, use spaces for indentation")
        
        # Check for multiple statements on one line
        if ';' in line and not line.strip().startswith('#'):
            # Don't flag semicolons in strings or comments
            if not self._is_in_string_or_comment(line):
                self.add_issue(file_path, line_num, 'multiple-statements',
                             "Multiple statements on one line")
        
        # Check for TODO/FIXME without issue numbers (Google style prefers issue tracking)
        todo_pattern = r'\b(TODO|FIXME|XXX)\b'
        if re.search(todo_pattern, line, re.IGNORECASE):
            if not re.search(r'\b(TODO|FIXME|XXX)\s*\([^)]+\)', line, re.IGNORECASE):
                self.add_issue(file_path, line_num, 'todo-format',
                             "TODO/FIXME should include author or issue reference: TODO(username): description")
    
    def _is_in_string_or_comment(self, line: str) -> bool:
        """Check if semicolon is inside a string literal or comment"""
        # Simple heuristic - check if semicolon appears after # or inside quotes
        comment_pos = line.find('#')
        if comment_pos != -1 and ';' in line[comment_pos:]:
            return True
        
        # Check for semicolon in strings (basic detection)
        in_string = False
        quote_char = None
        i = 0
        while i < len(line):
            char = line[i]
            if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    in_string = False
                    quote_char = None
            elif char == ';' and in_string:
                return True
            i += 1
        
        return False
    
    def check_file_structure(self, file_path: str, lines: List[str]):
        """Check overall file structure"""
        
        # Check for module docstring
        if not self.has_module_docstring(lines):
            self.add_issue(file_path, 1, 'missing-module-docstring',
                         "Module should have a docstring")
        
        # Check encoding declaration for non-ASCII files
        content = '\n'.join(lines)
        if not content.isascii() and not self.has_encoding_declaration(lines):
            self.add_issue(file_path, 1, 'missing-encoding',
                         "Non-ASCII file should have encoding declaration")
        
        # Check for proper import organization
        self.check_import_organization(file_path, lines)
        
        # Check for excessive blank lines
        self.check_blank_lines(file_path, lines)
    
    def has_module_docstring(self, lines: List[str]) -> bool:
        """Check if file has a module docstring"""
        # Skip shebang and encoding lines
        start_line = 0
        for i, line in enumerate(lines[:3]):
            stripped = line.strip()
            if stripped.startswith('#!') or 'coding' in stripped:
                continue
            start_line = i
            break
        
        # Look for docstring in first few non-comment lines
        in_docstring = False
        quote_count = 0
        
        for line in lines[start_line:start_line + 10]:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            if '"""' in stripped or "'''" in stripped:
                quote_count += stripped.count('"""') + stripped.count("'''")
                if quote_count >= 2:
                    return True
                in_docstring = True
            elif in_docstring:
                continue
            else:
                # Found non-comment, non-docstring code
                return False
        
        return quote_count >= 2
    
    def has_encoding_declaration(self, lines: List[str]) -> bool:
        """Check if file has encoding declaration in first two lines"""
        for line in lines[:2]:
            if re.search(r'coding[=:]\s*([-\w.]+)', line):
                return True
        return False
    
    def check_import_organization(self, file_path: str, lines: List[str]):
        """Check import organization according to Google style"""
        import_sections = {
            'future': [],
            'standard': [],
            'third_party': [],
            'local': []
        }
        
        current_section = None
        last_import_line = -1
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith(('import ', 'from ')) and not stripped.startswith('#'):
                last_import_line = line_num
                
                # Categorize import
                if 'from __future__' in stripped:
                    current_section = 'future'
                elif self._is_standard_library_import(stripped):
                    current_section = 'standard'
                elif self._is_local_import(stripped):
                    current_section = 'local'
                else:
                    current_section = 'third_party'
                
                import_sections[current_section].append((line_num, stripped))
        
        # Check if imports are properly separated
        if last_import_line > 0:
            self._check_import_section_separation(file_path, import_sections)
    
    def _is_standard_library_import(self, import_line: str) -> bool:
        """Check if import is from standard library"""
        standard_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing',
            'collections', 'itertools', 'functools', 're', 'math', 'random',
            'subprocess', 'threading', 'multiprocessing', 'asyncio', 'sqlite3',
            'logging', 'argparse', 'configparser', 'urllib', 'http', 'email',
            'xml', 'html', 'csv', 'pickle', 'base64', 'hashlib', 'hmac',
            'uuid', 'tempfile', 'shutil', 'glob', 'fnmatch', 'unittest'
        }
        
        # Extract module name from import statement
        if import_line.startswith('from '):
            module = import_line.split()[1].split('.')[0]
        else:  # import statement
            module = import_line.split()[1].split('.')[0].split(',')[0]
        
        return module in standard_modules
    
    def _is_local_import(self, import_line: str) -> bool:
        """Check if import is local to the project"""
        local_indicators = ['scripts.', 'local.', 'remote.', '.utils', '.common']
        return any(indicator in import_line for indicator in local_indicators)
    
    def _check_import_section_separation(self, file_path: str, import_sections: Dict[str, List[Tuple[int, str]]]):
        """Check if import sections are properly separated"""
        sections_with_imports = {k: v for k, v in import_sections.items() if v}
        
        if len(sections_with_imports) <= 1:
            return  # No separation needed
        
        # Check if sections are in correct order
        expected_order = ['future', 'standard', 'third_party', 'local']
        actual_sections = list(sections_with_imports.keys())
        
        # Filter expected order to only include sections that exist
        expected_filtered = [s for s in expected_order if s in actual_sections]
        
        if actual_sections != expected_filtered:
            first_import_line = min(imports[0][0] for imports in sections_with_imports.values())
            self.add_issue(file_path, first_import_line, 'import-order',
                         f"Imports should be in order: {', '.join(expected_filtered)}")
    
    def check_blank_lines(self, file_path: str, lines: List[str]):
        """Check for excessive blank lines"""
        consecutive_blank = 0
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                consecutive_blank += 1
            else:
                if consecutive_blank > 2:
                    self.add_issue(file_path, line_num - consecutive_blank, 'excessive-blank-lines',
                                 f"Too many consecutive blank lines ({consecutive_blank})")
                consecutive_blank = 0
    
    def check_ast_structure(self, tree: ast.AST, file_path: str):
        """Check AST structure for Google style compliance"""
        
        for node in ast.walk(tree):
            # Check function definitions
            if isinstance(node, ast.FunctionDef):
                self.check_function_style(node, file_path)
            
            # Check class definitions
            elif isinstance(node, ast.ClassDef):
                self.check_class_style(node, file_path)
            
            # Check import statements
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self.check_import_style(node, file_path)
            
            # Check variable naming
            elif isinstance(node, ast.Assign):
                self.check_variable_naming(node, file_path)
    
    def check_function_style(self, node: ast.FunctionDef, file_path: str):
        """Check function definition style"""
        
        # Check function naming (snake_case)
        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('__'):
            self.add_issue(file_path, node.lineno, 'function-naming',
                         f"Function '{node.name}' should use snake_case naming")
        
        # Check for function docstring
        if not ast.get_docstring(node) and not node.name.startswith('_'):
            # Skip if function is very short (less than 3 lines)
            if hasattr(node, 'end_lineno') and node.end_lineno:
                func_length = node.end_lineno - node.lineno
                if func_length > 3:
                    self.add_issue(file_path, node.lineno, 'missing-function-docstring',
                                 f"Public function '{node.name}' should have a docstring")
        
        # Check function length (Google recommends functions fit on screen)
        if hasattr(node, 'end_lineno') and node.end_lineno:
            func_length = node.end_lineno - node.lineno
            if func_length > 50:  # Configurable threshold
                self.add_issue(file_path, node.lineno, 'function-too-long',
                             f"Function '{node.name}' is {func_length} lines long, consider breaking it down")
        
        # Check for too many arguments
        total_args = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
        if node.args.vararg:
            total_args += 1
        if node.args.kwarg:
            total_args += 1
        
        if total_args > 7:  # Google style recommends <= 7 arguments
            self.add_issue(file_path, node.lineno, 'too-many-arguments',
                         f"Function '{node.name}' has {total_args} arguments, consider reducing")
    
    def check_class_style(self, node: ast.ClassDef, file_path: str):
        """Check class definition style"""
        
        # Check class naming (PascalCase)
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
            self.add_issue(file_path, node.lineno, 'class-naming',
                         f"Class '{node.name}' should use PascalCase naming")
        
        # Check for class docstring
        if not ast.get_docstring(node):
            self.add_issue(file_path, node.lineno, 'missing-class-docstring',
                         f"Class '{node.name}' should have a docstring")
        
        # Check for proper method organization
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if methods:
            self._check_method_organization(node, methods, file_path)
    
    def _check_method_organization(self, class_node: ast.ClassDef, methods: List[ast.FunctionDef], file_path: str):
        """Check if methods are properly organized (public before private)"""
        public_methods = [m for m in methods if not m.name.startswith('_')]
        private_methods = [m for m in methods if m.name.startswith('_') and not m.name.startswith('__')]
        magic_methods = [m for m in methods if m.name.startswith('__') and m.name.endswith('__')]
        
        # Check if private methods come after public methods
        if public_methods and private_methods:
            last_public_line = max(m.lineno for m in public_methods)
            first_private_line = min(m.lineno for m in private_methods)
            
            if first_private_line < last_public_line:
                self.add_issue(file_path, first_private_line, 'method-organization',
                             f"Private methods should come after public methods in class '{class_node.name}'")
    
    def check_import_style(self, node: ast.AST, file_path: str):
        """Check import statement style"""
        
        if isinstance(node, ast.ImportFrom):
            # Check for relative imports
            if node.level > 0:
                self.add_issue(file_path, node.lineno, 'relative-import',
                             "Avoid relative imports, use absolute imports")
            
            # Check for wildcard imports
            for alias in node.names:
                if alias.name == '*':
                    self.add_issue(file_path, node.lineno, 'wildcard-import',
                                 "Avoid wildcard imports (from module import *)")
        
        elif isinstance(node, ast.Import):
            # Check for multiple imports on one line
            if len(node.names) > 1:
                names = [alias.name for alias in node.names]
                self.add_issue(file_path, node.lineno, 'multiple-imports',
                             f"Import statements should be on separate lines: {', '.join(names)}")
    
    def check_variable_naming(self, node: ast.Assign, file_path: str):
        """Check variable naming conventions"""
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                
                # Check for constant naming (ALL_CAPS)
                if var_name.isupper() and len(var_name) > 1:
                    # This looks like a constant, which is good
                    continue
                
                # Check for regular variable naming (snake_case)
                if not re.match(r'^[a-z_][a-z0-9_]*$', var_name):
                    # Allow single letter variables in certain contexts
                    if len(var_name) == 1 and var_name in 'ijklmnxyz':
                        continue
                    
                    self.add_issue(file_path, node.lineno, 'variable-naming',
                                 f"Variable '{var_name}' should use snake_case naming")

def main():
    """Test the Google style validator"""
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not Path(file_path).exists():
            print(f"Error: File {file_path} does not exist")
            return 1
        
        validator = GoogleStyleValidator()
        issues = validator.validate_file(file_path)
        
        print(f"Google Style Validation for {file_path}:")
        print(f"Found {len(issues)} issues:")
        
        if issues:
            # Group issues by severity
            by_severity = {}
            for issue in issues:
                severity = issue['severity']
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            # Print issues by severity
            for severity in ['error', 'warning', 'info']:
                if severity in by_severity:
                    print(f"\n{severity.upper()} ({len(by_severity[severity])}):")
                    for issue in by_severity[severity]:
                        print(f"  Line {issue['line']}: {issue['message']} ({issue['symbol']})")
        else:
            print("  No issues found! Code follows Google Python Style Guide.")
        
        return len([i for i in issues if i['severity'] == 'error'])
    else:
        print("Usage: python google_style_validator.py <file_path>")
        print("Example: python google_style_validator.py local/log_processor/app.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())