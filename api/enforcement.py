#!/usr/bin/env python3
"""
AI Enforcement Framework - External validation and constraint enforcement
Addresses the fundamental issue that LLMs cannot enforce their own constraints
"""

import json
import re
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ValidationResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    HALT = "HALT"

@dataclass
class ConstraintViolation:
    rule: str
    expected: str
    actual: str
    severity: str
    timestamp: datetime

class AIEnforcementFramework:
    """
    External framework to enforce AI behavior constraints
    LLMs cannot be trusted to enforce their own rules
    """
    
    def __init__(self, config_path: str = None):
        self.constraints = {}
        self.violations = []
        self.enforcement_log = []
        self.mandatory_checks = []
        self.forbidden_actions = []
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        if config_path:
            self._load_config(config_path)
        else:
            self._load_default_constraints()
    
    def _load_default_constraints(self):
        """Load default constraint set for spatial AI system"""
        self.constraints = {
            "phase_adherence": {
                "description": "AI must follow migration phases strictly",
                "validator": self._validate_phase_adherence,
                "mandatory": True
            },
            "approval_required": {
                "description": "User approval required for destructive actions",
                "validator": self._validate_approval_required,
                "mandatory": True
            },
            "memory_consistency": {
                "description": "Single source of truth for memory operations",
                "validator": self._validate_memory_consistency,
                "mandatory": True
            },
            "audit_trail": {
                "description": "All decisions must be logged with reasoning",
                "validator": self._validate_audit_trail,
                "mandatory": True
            },
            "no_hallucination": {
                "description": "No false claims about internal processes",
                "validator": self._validate_no_hallucination,
                "mandatory": True
            }
        }
        
        # Mandatory response format checks
        self.mandatory_checks = [
            "Current Phase:",
            "Action Type:",
            "Approval Status:",
            "Confidence Level:",
            "Reasoning:"
        ]
        
        # Forbidden actions without explicit approval
        self.forbidden_actions = [
            "file deletion",
            "memory consolidation", 
            "system modification",
            "configuration changes",
            "data migration",
            "component switching"
        ]
    
    def validate_ai_response(self, response: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate AI response against all constraints
        This is the external enforcement layer
        """
        violations = []
        
        # Check mandatory format requirements
        format_check = self._check_mandatory_format(response)
        if not format_check:
            violations.append(ConstraintViolation(
                rule="mandatory_format",
                expected="Required format fields present",
                actual="Missing mandatory format fields",
                severity="HALT",
                timestamp=datetime.now()
            ))
        
        # Run all constraint validators
        for name, constraint in self.constraints.items():
            try:
                result = constraint["validator"](response, context)
                if not result:
                    severity = "HALT" if constraint["mandatory"] else "FAIL"
                    violations.append(ConstraintViolation(
                        rule=name,
                        expected=constraint["description"],
                        actual="Constraint violation detected",
                        severity=severity,
                        timestamp=datetime.now()
                    ))
            except Exception as e:
                self.logger.error(f"Validator {name} failed: {e}")
                violations.append(ConstraintViolation(
                    rule=name,
                    expected="Validator to run successfully",
                    actual=f"Validator error: {e}",
                    severity="HALT",
                    timestamp=datetime.now()
                ))
        
        # Record violations
        self.violations.extend(violations)
        
        # Determine result
        if any(v.severity == "HALT" for v in violations):
            self._log_enforcement_action("HALT", violations)
            return ValidationResult.HALT
        elif violations:
            self._log_enforcement_action("FAIL", violations)
            return ValidationResult.FAIL
        else:
            self._log_enforcement_action("PASS", [])
            return ValidationResult.PASS
    
    def _check_mandatory_format(self, response: str) -> bool:
        """Check if response contains all mandatory format elements"""
        for check in self.mandatory_checks:
            if check not in response:
                self.logger.warning(f"Missing mandatory check: {check}")
                return False
        return True
    
    def _validate_phase_adherence(self, response: str, context: Dict[str, Any]) -> bool:
        """Validate that AI is following the migration phase plan"""
        current_phase = context.get("current_phase")
        if not current_phase:
            return False
        
        # Extract phase from response
        phase_match = re.search(r"Current Phase:\s*([^\n]+)", response)
        if not phase_match:
            return False
        
        stated_phase = phase_match.group(1).strip()
        return stated_phase == current_phase
    
    def _validate_approval_required(self, response: str, context: Dict[str, Any]) -> bool:
        """Validate that destructive actions require approval"""
        # Check if response contains forbidden actions
        response_lower = response.lower()
        for action in self.forbidden_actions:
            if action in response_lower:
                # Check if approval was requested/confirmed
                if "approval" not in response_lower and "confirm" not in response_lower:
                    self.logger.warning(f"Forbidden action '{action}' without approval request")
                    return False
        return True
    
    def _validate_memory_consistency(self, response: str, context: Dict[str, Any]) -> bool:
        """Validate single source of truth for memory operations"""
        # Check for memory operations
        if "memory" in response.lower():
            # Ensure only one memory backend is referenced
            backends = ["sqlite", "postgresql", "dual", "parallel"]
            found_backends = [b for b in backends if b in response.lower()]
            if len(found_backends) > 1:
                self.logger.warning(f"Multiple memory backends referenced: {found_backends}")
                return False
        return True
    
    def _validate_audit_trail(self, response: str, context: Dict[str, Any]) -> bool:
        """Validate that reasoning is provided for decisions"""
        if "Reasoning:" not in response:
            return False
        
        # Check reasoning is substantive (not just "as requested")
        reasoning_match = re.search(r"Reasoning:\s*([^\n]+)", response)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip().lower()
            trivial_reasons = ["as requested", "user asked", "following instructions"]
            if any(trivial in reasoning for trivial in trivial_reasons):
                return False
        
        return True
    
    def _validate_no_hallucination(self, response: str, context: Dict[str, Any]) -> bool:
        """Validate no false claims about AI capabilities or internal processes"""
        hallucination_patterns = [
            r"i (chose|decided|preferred|wanted)",
            r"based on my (interest|preference|choice)",
            r"i found it (interesting|engaging)",
            r"i have (feelings|emotions|desires)",
            r"i can (choose|decide) to ignore"
        ]
        
        response_lower = response.lower()
        for pattern in hallucination_patterns:
            if re.search(pattern, response_lower):
                self.logger.warning(f"Hallucination detected: {pattern}")
                return False
        
        return True
    
    def _log_enforcement_action(self, action: str, violations: List[ConstraintViolation]):
        """Log enforcement actions for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "violations": [
                {
                    "rule": v.rule,
                    "expected": v.expected,
                    "actual": v.actual,
                    "severity": v.severity
                } for v in violations
            ]
        }
        
        self.enforcement_log.append(log_entry)
        self.logger.info(f"Enforcement action: {action}, violations: {len(violations)}")
    
    def get_violation_report(self) -> Dict[str, Any]:
        """Generate comprehensive violation report"""
        return {
            "total_violations": len(self.violations),
            "halt_violations": len([v for v in self.violations if v.severity == "HALT"]),
            "violations_by_rule": self._group_violations_by_rule(),
            "recent_violations": self.violations[-10:],  # Last 10
            "enforcement_log": self.enforcement_log
        }
    
    def _group_violations_by_rule(self) -> Dict[str, int]:
        """Group violations by rule for analysis"""
        groups = {}
        for violation in self.violations:
            if violation.rule not in groups:
                groups[violation.rule] = 0
            groups[violation.rule] += 1
        return groups
    
    def halt_system(self, reason: str):
        """Halt system execution due to constraint violation"""
        self.logger.critical(f"SYSTEM HALT: {reason}")
        print(f"\n🚨 SYSTEM HALT: {reason}")
        print("AI response rejected due to constraint violation.")
        print("Review enforcement log for details.")
        raise SystemExit("AI constraint violation - system halted")

# Example usage wrapper function
def enforce_ai_response(ai_response: str, context: Dict[str, Any]) -> str:
    """
    Wrapper function to enforce constraints on AI responses
    Use this to wrap ALL AI interactions
    """
    enforcer = AIEnforcementFramework()
    
    result = enforcer.validate_ai_response(ai_response, context)
    
    if result == ValidationResult.HALT:
        enforcer.halt_system("Critical constraint violation")
    elif result == ValidationResult.FAIL:
        print("⚠️  AI response has constraint violations but proceeding...")
        print("Check enforcement log for details.")
    
    return ai_response

if __name__ == "__main__":
    # Test the enforcement framework
    print("🔒 AI Enforcement Framework Test")
    print("=" * 50)
    
    enforcer = AIEnforcementFramework()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Response",
            "response": """
            Current Phase: Step 4
            Action Type: API Testing
            Approval Status: Not Required
            Confidence Level: 95%
            Reasoning: Testing API endpoints to verify functionality before proceeding to next phase
            """,
            "context": {"current_phase": "Step 4"}
        },
        {
            "name": "Invalid - Missing Format",
            "response": "Let me just delete these files and move on.",
            "context": {"current_phase": "Step 4"}
        },
        {
            "name": "Invalid - Hallucination",
            "response": """
            Current Phase: Step 4
            Action Type: File Operations
            Approval Status: Not Required
            Confidence Level: 90%
            Reasoning: I chose this approach because I found it more interesting
            """,
            "context": {"current_phase": "Step 4"}
        }
    ]
    
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        result = enforcer.validate_ai_response(test["response"], test["context"])
        print(f"Result: {result.value}")
    
    # Print violation report
    report = enforcer.get_violation_report()
    print(f"\nViolation Report:")
    print(f"Total violations: {report['total_violations']}")
    print(f"HALT violations: {report['halt_violations']}")
    print(f"Violations by rule: {report['violations_by_rule']}")