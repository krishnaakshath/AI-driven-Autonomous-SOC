"""
Phase 22 Verification — Multi-Feature Enhancement
===================================================
Tests: Role-based sidebar, login tracking, suspicious login detection,
       weekly report generation, UBA gate, admin persistence.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SEP = "=" * 60

def test_login_tracking():
    """Test login footprint tracking."""
    print(f"\n[1] Testing login footprint tracking...")
    from services.user_data import log_login_attempt, get_login_history
    
    # Log a few test logins
    log_login_attempt("test@verify.com", success=True, ip_address="192.168.1.50")
    log_login_attempt("test@verify.com", success=False, ip_address="10.0.0.99")
    log_login_attempt("test@verify.com", success=True, ip_address="192.168.1.50")
    
    history = get_login_history("test@verify.com")
    assert len(history) >= 3, f"Expected >= 3 login records, got {len(history)}"
    assert history[0]['success'] == True
    assert history[1]['success'] == False
    print(f"    ✓ Logged 3 login attempts, retrieved {len(history)} records")
    
    # Verify persistence (data on disk)
    from services.user_data import _get_user_dir
    user_dir = _get_user_dir("test@verify.com")
    login_file = os.path.join(user_dir, 'login_history.json')
    assert os.path.exists(login_file), "Login history file not found on disk"
    print(f"    ✓ Login history persisted to disk: {login_file}")

def test_suspicious_login_detection():
    """Test suspicious login detection algorithm."""
    print(f"\n[2] Testing suspicious login detection...")
    from services.user_data import log_login_attempt, check_suspicious_login
    
    # Build a normal login pattern
    for _ in range(5):
        log_login_attempt("suspicious_test@verify.com", success=True, ip_address="192.168.1.100")
    
    # Check from known IP — should NOT be suspicious
    result = check_suspicious_login("suspicious_test@verify.com", current_ip="192.168.1.100")
    assert not result['is_suspicious'], f"Known IP should not be suspicious, got risk={result['risk_score']}"
    print(f"    ✓ Known IP login: risk_score={result['risk_score']}, suspicious={result['is_suspicious']}")
    
    # Check from new IP — should raise risk
    result_new = check_suspicious_login("suspicious_test@verify.com", current_ip="45.33.32.156")
    assert result_new['risk_score'] > result['risk_score'], "New IP should raise risk score"
    print(f"    ✓ New IP login: risk_score={result_new['risk_score']}, reasons={result_new['reasons']}")
    
    # Simulate rapid failed attempts
    for _ in range(4):
        log_login_attempt("bruteforce_test@verify.com", success=False, ip_address="10.0.0.1")
    result_brute = check_suspicious_login("bruteforce_test@verify.com", current_ip="10.0.0.1")
    assert result_brute['is_suspicious'], "Rapid failed attempts should trigger suspicious flag"
    print(f"    ✓ Brute force detection: risk_score={result_brute['risk_score']}, reasons={result_brute['reasons']}")

def test_weekly_report_generation():
    """Test weekly report generation."""
    print(f"\n[3] Testing weekly report generation...")
    from services.weekly_reporter import generate_weekly_report, get_weekly_reports, should_generate_weekly_report, get_report_file
    
    # Should generate (first time or already due)
    result = generate_weekly_report()
    assert result is not None, "generate_weekly_report returned None"
    assert 'id' in result, "Report metadata missing 'id'"
    assert result['id'].startswith('WEEKLY-'), f"Unexpected ID format: {result['id']}"
    print(f"    ✓ Generated report: {result['id']}")
    
    # Check report log
    reports = get_weekly_reports()
    assert len(reports) >= 1, "Report log should have at least 1 entry"
    print(f"    ✓ Report log has {len(reports)} entries")
    
    # Check text file exists and is downloadable
    txt_file = result.get('txt_file')
    assert txt_file, "No text file in report metadata"
    txt_data = get_report_file(txt_file)
    assert txt_data and len(txt_data) > 100, f"Text report too small or missing: {len(txt_data) if txt_data else 0} bytes"
    print(f"    ✓ Text report: {txt_file} ({len(txt_data)} bytes)")
    
    # Stats captured
    stats = result.get('stats', {})
    print(f"    ✓ Report stats: events={stats.get('total_events')}, critical={stats.get('critical_alerts')}, anomalies={stats.get('anomalies')}")

def test_dashboard_role_navigation():
    """Test that dashboard.py defines proper role-based navigation."""
    print(f"\n[4] Testing role-based sidebar navigation...")
    
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard.py')
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Check for 3 navigation modes
    assert 'not logged_in' in content or 'not logged in' in content.lower() or 'if not logged_in' in content, \
        "Missing unauthenticated navigation block"
    assert 'user_is_admin' in content or 'is_admin()' in content, \
        "Missing admin check"
    assert '25_Admin.py' in content, "Admin page not in navigation"
    assert '12_UBA.py' in content, "UBA page not in navigation"
    
    # Verify 3 distinct st.navigation blocks
    nav_count = content.count('st.navigation(')
    assert nav_count == 3, f"Expected 3 st.navigation() blocks, got {nav_count}"
    print(f"    ✓ Found {nav_count} navigation modes (unauthenticated, admin, user)")
    
    # Verify admin pages NOT in regular user navigation
    lines = content.split('\n')
    in_user_block = False
    user_block_pages = []
    for line in lines:
        if 'Regular user' in line or '# ── Regular user' in line:
            in_user_block = True
        if in_user_block and 'st.navigation(' in line:
            break
        if in_user_block and 'st.Page(' in line:
            user_block_pages.append(line.strip())
    
    # Admin-only pages should NOT be in non-admin sidebar
    admin_only_pages = ['25_Admin.py', '12_UBA.py', '24_SIEM.py', '18_Rules.py', '17_IP_Block.py']
    # Check the third (user) navigation block doesn't have these
    # Find the user navigation block content
    parts = content.split('st.navigation(')
    if len(parts) >= 4:
        user_nav_block = parts[3]  # Third navigation call (0-indexed after split)
        for admin_page in admin_only_pages:
            assert admin_page not in user_nav_block, f"Admin page {admin_page} found in user navigation!"
        print(f"    ✓ Admin-only pages correctly excluded from regular user sidebar")
    else:
        print(f"    ⚠ Could not split navigation blocks (got {len(parts)-1} blocks)")
    
    # Verify session persistence call
    assert 'check_persistent_session' in content, "Missing check_persistent_session() call"
    print(f"    ✓ Session persistence check present in dashboard.py")

def test_uba_admin_gate():
    """Test that UBA page has admin-only access gate."""
    print(f"\n[5] Testing UBA admin-only gate...")
    
    uba_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pages', '12_UBA.py')
    with open(uba_path, 'r') as f:
        content = f.read()
    
    assert 'is_admin' in content, "Missing is_admin check in UBA page"
    assert 'Admin Access Only' in content, "Missing admin-only error message"
    assert 'is_authenticated' in content, "Missing authentication check"
    print(f"    ✓ UBA page has authentication + admin-only gate")

def test_cloud_background_weekly_trigger():
    """Test that cloud_background.py has weekly report trigger."""
    print(f"\n[6] Testing cloud_background weekly report trigger...")
    
    bg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'services', 'cloud_background.py')
    with open(bg_path, 'r') as f:
        content = f.read()
    
    assert '_run_weekly_report' in content, "Missing _run_weekly_report function"
    assert 'weekly_reporter' in content, "Missing weekly_reporter import"
    assert '_WEEKLY_REPORT_CHECK_INTERVAL' in content, "Missing weekly check interval constant"
    print(f"    ✓ Weekly report trigger configured in cloud_background.py")

def test_threat_intel_api_keys():
    """Test that Threat Intel service reads API keys from config."""
    print(f"\n[7] Testing Threat Intel API key integration...")
    
    from services.threat_intel import threat_intel
    
    # Check that keys are loaded
    has_otx = bool(threat_intel.otx_key)
    has_vt = bool(threat_intel.virustotal_key)
    has_abuse = bool(threat_intel.abuseipdb_key)
    
    print(f"    OTX key: {'✓ configured' if has_otx else '✗ not set'}")
    print(f"    VirusTotal key: {'✓ configured' if has_vt else '✗ not set'}")
    print(f"    AbuseIPDB key: {'✓ configured' if has_abuse else '✗ not set'}")
    
    # Verify get_latest_threats works (even without keys — uses public endpoint)
    threats = threat_intel.get_otx_pulses(5)
    print(f"    ✓ get_otx_pulses returned {len(threats)} pulses")

if __name__ == "__main__":
    print(SEP)
    print("PHASE 22 VERIFICATION — Multi-Feature Enhancement")
    print(SEP)
    
    results = []
    tests = [
        test_login_tracking,
        test_suspicious_login_detection,
        test_weekly_report_generation,
        test_dashboard_role_navigation,
        test_uba_admin_gate,
        test_cloud_background_weekly_trigger,
        test_threat_intel_api_keys,
    ]
    
    for test in tests:
        try:
            test()
            results.append((test.__name__, True, None))
        except Exception as e:
            results.append((test.__name__, False, str(e)))
            print(f"    ✗ FAILED: {e}")
    
    print(f"\n{SEP}")
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"RESULTS: {passed}/{len(results)} passed, {failed} failed")
    
    if failed > 0:
        print("\nFailed tests:")
        for name, ok, err in results:
            if not ok:
                print(f"  ✗ {name}: {err}")
    else:
        print("ALL TESTS PASSED ✓")
    print(SEP)
