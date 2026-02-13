"""
 Autonomous Response Playbook Engine
=======================================
Zero-touch incident response with predefined playbooks.
Automatically executes response actions when threats are detected.

Playbooks:
- Ransomware: Isolate → Snapshot → Alert → Block C2
- Brute Force: Block IP → Rate limit → Notify
- Data Exfil: Kill connection → Quarantine → Forensics
"""

from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import os

class PlaybookStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class ActionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class PlaybookAction:
    """Single action within a playbook."""
    name: str
    description: str
    action_type: str  # isolate, block, alert, snapshot, quarantine, etc.
    target: Optional[str] = None
    parameters: Dict = field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[str] = None
    executed_at: Optional[datetime] = None

@dataclass
class Playbook:
    """Complete response playbook."""
    id: str
    name: str
    description: str
    trigger_conditions: List[str]
    severity: str  # critical, high, medium, low
    actions: List[PlaybookAction]
    auto_execute: bool = False
    status: PlaybookStatus = PlaybookStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class PlaybookEngine:
    """
    Manages and executes security response playbooks.
    """
    
    def __init__(self):
        self.playbooks: Dict[str, Playbook] = {}
        self.execution_log: List[Dict] = []
        self._initialize_default_playbooks()
    
    def _initialize_default_playbooks(self):
        """Create default security playbooks."""
        
        # Ransomware Response Playbook
        self.playbooks["ransomware"] = Playbook(
            id="PB-001",
            name="Ransomware Response",
            description="Immediate containment and recovery for ransomware detection",
            trigger_conditions=["ransomware_detected", "encryption_activity", "known_ransomware_hash"],
            severity="critical",
            auto_execute=True,
            actions=[
                PlaybookAction(
                    name="Isolate Host",
                    description="Disconnect affected host from network",
                    action_type="isolate",
                    parameters={"method": "firewall_block"}
                ),
                PlaybookAction(
                    name="Create Snapshot",
                    description="Capture memory and disk state for forensics",
                    action_type="snapshot",
                    parameters={"include_memory": True}
                ),
                PlaybookAction(
                    name="Block C2 Communication",
                    description="Block known command & control servers",
                    action_type="block",
                    parameters={"block_type": "domain_and_ip"}
                ),
                PlaybookAction(
                    name="Alert SOC Team",
                    description="Send critical alert to security team",
                    action_type="alert",
                    parameters={"priority": "critical", "channel": "all"}
                ),
                PlaybookAction(
                    name="Initiate Backup Recovery",
                    description="Begin recovery from last clean backup",
                    action_type="recover",
                    parameters={"recovery_point": "last_clean"}
                )
            ]
        )
        
        # Brute Force Response Playbook
        self.playbooks["brute_force"] = Playbook(
            id="PB-002",
            name="Brute Force Mitigation",
            description="Block and prevent credential stuffing attacks",
            trigger_conditions=["failed_login_threshold", "password_spray", "credential_stuffing"],
            severity="high",
            auto_execute=True,
            actions=[
                PlaybookAction(
                    name="Block Attacker IP",
                    description="Add source IP to firewall blocklist",
                    action_type="block",
                    parameters={"duration_hours": 24}
                ),
                PlaybookAction(
                    name="Enable Rate Limiting",
                    description="Apply stricter rate limits on authentication endpoints",
                    action_type="rate_limit",
                    parameters={"requests_per_minute": 5}
                ),
                PlaybookAction(
                    name="Lock Targeted Accounts",
                    description="Temporarily lock accounts under attack",
                    action_type="account_lock",
                    parameters={"duration_minutes": 30}
                ),
                PlaybookAction(
                    name="Notify Admin",
                    description="Alert system administrators",
                    action_type="alert",
                    parameters={"priority": "high"}
                ),
                PlaybookAction(
                    name="Enable CAPTCHA",
                    description="Require CAPTCHA for affected endpoints",
                    action_type="captcha",
                    parameters={"endpoints": ["login", "password_reset"]}
                )
            ]
        )
        
        # Data Exfiltration Response Playbook
        self.playbooks["data_exfiltration"] = Playbook(
            id="PB-003",
            name="Data Exfiltration Response",
            description="Contain and investigate potential data theft",
            trigger_conditions=["large_data_transfer", "unusual_upload", "dlp_alert"],
            severity="critical",
            auto_execute=False,  # Requires confirmation due to potential business impact
            actions=[
                PlaybookAction(
                    name="Kill Active Connections",
                    description="Terminate suspicious outbound connections",
                    action_type="kill_connection",
                    parameters={"preserve_logs": True}
                ),
                PlaybookAction(
                    name="Quarantine User Session",
                    description="Isolate user session for investigation",
                    action_type="quarantine",
                    parameters={"revoke_tokens": True}
                ),
                PlaybookAction(
                    name="Capture Network Forensics",
                    description="Begin packet capture for analysis",
                    action_type="forensics",
                    parameters={"duration_minutes": 60}
                ),
                PlaybookAction(
                    name="Alert Security Team",
                    description="Immediate escalation to security team",
                    action_type="alert",
                    parameters={"priority": "critical", "include_evidence": True}
                ),
                PlaybookAction(
                    name="Preserve Evidence",
                    description="Secure logs and artifacts for investigation",
                    action_type="preserve",
                    parameters={"retention_days": 90}
                )
            ]
        )
        
        # Insider Threat Response Playbook
        self.playbooks["insider_threat"] = Playbook(
            id="PB-004",
            name="Insider Threat Response",
            description="Investigate and contain suspicious insider activity",
            trigger_conditions=["anomalous_behavior", "policy_violation", "access_anomaly"],
            severity="high",
            auto_execute=False,
            actions=[
                PlaybookAction(
                    name="Enable Enhanced Monitoring",
                    description="Increase logging and monitoring for user",
                    action_type="monitor",
                    parameters={"level": "verbose"}
                ),
                PlaybookAction(
                    name="Capture Session Recording",
                    description="Begin recording user activity",
                    action_type="record",
                    parameters={"include_screenshots": True}
                ),
                PlaybookAction(
                    name="Review Access Permissions",
                    description="Audit user's current access rights",
                    action_type="audit",
                    parameters={"scope": "full"}
                ),
                PlaybookAction(
                    name="Alert HR and Legal",
                    description="Notify appropriate stakeholders",
                    action_type="alert",
                    parameters={"recipients": ["hr", "legal", "security"]}
                )
            ]
        )
        
        # DDoS Response Playbook
        self.playbooks["ddos"] = Playbook(
            id="PB-005",
            name="DDoS Mitigation",
            description="Absorb and mitigate distributed denial of service attacks",
            trigger_conditions=["traffic_spike", "syn_flood", "amplification_attack"],
            severity="high",
            auto_execute=True,
            actions=[
                PlaybookAction(
                    name="Enable DDoS Protection",
                    description="Activate cloud DDoS mitigation service",
                    action_type="ddos_protect",
                    parameters={"mode": "under_attack"}
                ),
                PlaybookAction(
                    name="Scale Resources",
                    description="Auto-scale infrastructure to absorb traffic",
                    action_type="scale",
                    parameters={"factor": 3}
                ),
                PlaybookAction(
                    name="Enable Rate Limiting",
                    description="Apply aggressive rate limiting",
                    action_type="rate_limit",
                    parameters={"requests_per_second": 100}
                ),
                PlaybookAction(
                    name="Block Attack Sources",
                    description="Block identified attack source IPs/ranges",
                    action_type="block",
                    parameters={"block_type": "ip_range"}
                ),
                PlaybookAction(
                    name="Alert NOC",
                    description="Notify network operations center",
                    action_type="alert",
                    parameters={"priority": "high"}
                )
            ]
        )
    
    def execute_playbook(self, playbook_id: str, target: Optional[str] = None) -> Dict:
        """
        Execute a playbook.
        
        Args:
            playbook_id: ID of the playbook to execute
            target: Optional target (IP, hostname, user, etc.)
        
        Returns:
            Execution result dictionary
        """
        if playbook_id not in self.playbooks:
            return {"success": False, "error": f"Playbook '{playbook_id}' not found"}
        
        playbook = self.playbooks[playbook_id]
        playbook.status = PlaybookStatus.RUNNING
        playbook.started_at = datetime.now()
        
        results = []
        
        for action in playbook.actions:
            action.status = ActionStatus.RUNNING
            action.executed_at = datetime.now()
            
            # Simulate action execution
            try:
                result = self._execute_action(action, target)
                action.status = ActionStatus.SUCCESS
                action.result = result
                results.append({
                    "action": action.name,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                action.status = ActionStatus.FAILED
                action.result = str(e)
                results.append({
                    "action": action.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        playbook.status = PlaybookStatus.COMPLETED
        playbook.completed_at = datetime.now()
        
        # Log execution
        self.execution_log.append({
            "playbook_id": playbook_id,
            "playbook_name": playbook.name,
            "target": target,
            "started_at": playbook.started_at.isoformat(),
            "completed_at": playbook.completed_at.isoformat(),
            "results": results
        })
        
        return {
            "success": True,
            "playbook": playbook.name,
            "actions_executed": len(results),
            "results": results
        }
    
    def _execute_action(self, action: PlaybookAction, target: Optional[str]) -> str:
        """Execute a single playbook action (simulated)."""
        action_handlers = {
            "isolate": lambda: f"Host {target or 'target'} isolated from network",
            "block": lambda: f"Blocked {target or 'attacker'} on firewall",
            "alert": lambda: f"Alert sent to {action.parameters.get('channel', 'security team')}",
            "snapshot": lambda: f"Snapshot captured: SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "quarantine": lambda: f"Session quarantined: {target or 'user'}",
            "rate_limit": lambda: f"Rate limiting enabled: {action.parameters.get('requests_per_minute', 10)} req/min",
            "account_lock": lambda: f"Account locked for {action.parameters.get('duration_minutes', 30)} minutes",
            "kill_connection": lambda: f"Terminated {target or 'suspicious'} connections",
            "forensics": lambda: f"Forensic capture initiated: CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "recover": lambda: f"Recovery initiated from {action.parameters.get('recovery_point', 'latest')} backup",
            "ddos_protect": lambda: f"DDoS protection enabled: {action.parameters.get('mode', 'standard')} mode",
            "scale": lambda: f"Resources scaled by factor of {action.parameters.get('factor', 2)}",
            "monitor": lambda: f"Enhanced monitoring enabled for {target or 'entity'}",
            "record": lambda: f"Session recording started for {target or 'user'}",
            "audit": lambda: f"Access audit initiated for {target or 'user'}",
            "preserve": lambda: f"Evidence preserved for {action.parameters.get('retention_days', 30)} days",
            "captcha": lambda: f"CAPTCHA enabled for {action.parameters.get('endpoints', ['all'])}"
        }
        
        handler = action_handlers.get(action.action_type, lambda: f"Action {action.action_type} completed")
        return handler()
    
    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get a specific playbook."""
        return self.playbooks.get(playbook_id)
    
    def list_playbooks(self) -> List[Dict]:
        """List all available playbooks."""
        return [
            {
                "id": p.id,
                "key": key,
                "name": p.name,
                "description": p.description,
                "severity": p.severity,
                "auto_execute": p.auto_execute,
                "action_count": len(p.actions),
                "triggers": p.trigger_conditions
            }
            for key, p in self.playbooks.items()
        ]
    
    def get_execution_log(self, limit: int = 10) -> List[Dict]:
        """Get recent playbook executions."""
        return self.execution_log[-limit:]


# Singleton instance
playbook_engine = PlaybookEngine()


def execute_playbook(playbook_id: str, target: str = None) -> Dict:
    """Execute a response playbook."""
    return playbook_engine.execute_playbook(playbook_id, target)


def list_playbooks() -> List[Dict]:
    """List all available playbooks."""
    return playbook_engine.list_playbooks()


def get_playbook_details(playbook_id: str) -> Optional[Dict]:
    """Get detailed playbook information."""
    pb = playbook_engine.get_playbook(playbook_id)
    if not pb:
        return None
    
    return {
        "id": pb.id,
        "name": pb.name,
        "description": pb.description,
        "severity": pb.severity,
        "auto_execute": pb.auto_execute,
        "trigger_conditions": pb.trigger_conditions,
        "actions": [
            {
                "name": a.name,
                "description": a.description,
                "type": a.action_type,
                "parameters": a.parameters
            }
            for a in pb.actions
        ]
    }
