# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Guardrail Test Script
Author: Emad Noorizadeh

This script tests the URL guardrail system to ensure it's working correctly.
"""

import sys
import os
import time
import requests
import urllib.request
import urllib.error

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from url_guardrail import guardrail, block_external_requests

def test_url_guardrail():
    """Test the URL guardrail system"""
    print("🧪 Testing URL Guardrail System")
    print("=" * 50)
    
    # Test URLs that should be ALLOWED
    allowed_urls = [
        "https://api.openai.com/v1/chat/completions",
        "https://api.openai.com/v1/embeddings", 
        "https://api.openai.com/v1/models",
        "https://api.langgraph.com/api/v1/",
        "https://api.chroma.ai/api/v1/",
        "http://localhost:9000/health",
        "http://127.0.0.1:9000/docs"
    ]
    
    # Test URLs that should be BLOCKED
    blocked_urls = [
        "https://api.openai.com/v1/telemetry",
        "https://api.langchain.com/telemetry",
        "https://api.llamaindex.ai/telemetry",
        "https://api.huggingface.co/telemetry",
        "https://analytics.google.com/track",
        "https://www.google-analytics.com/collect",
        "https://api.segment.io/track",
        "https://api.mixpanel.com/track",
        "https://api.sentry.io/api/",
        "https://api.datadoghq.com/api/",
        "https://api.newrelic.com/v2/",
        "https://api.rollbar.com/api/",
        "https://api.bugsnag.com/api/",
        "https://api.logrocket.com/api/",
        "https://api.fullstory.com/api/",
        "https://api.hotjar.com/api/",
        "https://api.amplitude.com/api/",
        "https://api.mixpanel.com/api/",
        "https://api.segment.io/api/",
        "https://api.intercom.io/api/",
        "https://api.zendesk.com/api/",
        "https://api.salesforce.com/api/",
        "https://api.hubspot.com/api/",
        "https://api.marketo.com/api/",
        "https://api.pardot.com/api/",
        "https://api.constantcontact.com/api/",
        "https://api.mailchimp.com/api/",
        "https://api.campaignmonitor.com/api/",
        "https://api.aweber.com/api/",
        "https://api.getresponse.com/api/",
        "https://api.activecampaign.com/api/",
        "https://api.klaviyo.com/api/",
        "https://api.drip.com/api/",
        "https://api.convertkit.com/api/",
        "https://api.leadpages.com/api/",
        "https://api.unbounce.com/api/",
        "https://api.optimizely.com/api/",
        "https://api.vwo.com/api/",
        "https://api.abtasty.com/api/",
        "https://api.kameleoon.com/api/",
        "https://api.dynamic-yield.com/api/",
        "https://api.personyze.com/api/",
        "https://api.evergage.com/api/",
        "https://api.blueconic.com/api/",
        "https://api.qualtrics.com/api/",
        "https://api.surveymonkey.com/api/",
        "https://api.typeform.com/api/",
        "https://api.google.com/api/",
        "https://api.facebook.com/api/",
        "https://api.twitter.com/api/",
        "https://api.linkedin.com/api/",
        "https://api.github.com/api/",
        "https://api.gitlab.com/api/",
        "https://api.bitbucket.org/api/",
        "https://api.docker.com/api/",
        "https://api.kubernetes.io/api/",
        "https://api.terraform.io/api/",
        "https://api.ansible.com/api/",
        "https://api.puppet.com/api/",
        "https://api.chef.io/api/",
        "https://api.saltstack.com/api/",
        "https://api.consul.io/api/",
        "https://api.vault.io/api/",
        "https://api.nomad.io/api/",
        "https://api.packer.io/api/",
        "https://api.vagrantup.com/api/",
        "https://api.virtualbox.org/api/",
        "https://api.vmware.com/api/",
        "https://api.citrix.com/api/",
        "https://api.parallels.com/api/",
        "https://api.qemu.org/api/",
        "https://api.kvm.org/api/",
        "https://api.xen.org/api/",
        "https://api.hyperv.com/api/",
        "https://api.podman.io/api/",
        "https://api.containerd.io/api/",
        "https://api.crio.io/api/",
        "https://api.runc.io/api/",
        "https://api.gvisor.io/api/",
        "https://api.kata-containers.io/api/",
        "https://api.firecracker.com/api/",
        "https://api.nabla.com/api/",
        "https://api.unikraft.io/api/",
        "https://api.osv.io/api/"
    ]
    
    print("\n🔍 Testing ALLOWED URLs:")
    allowed_passed = 0
    for url in allowed_urls:
        is_allowed = guardrail.is_url_allowed(url)
        status = "✅ PASS" if is_allowed else "❌ FAIL"
        print(f"  {status}: {url}")
        if is_allowed:
            allowed_passed += 1
    
    print(f"\n📊 Allowed URLs: {allowed_passed}/{len(allowed_urls)} passed")
    
    print("\n🔍 Testing BLOCKED URLs:")
    blocked_passed = 0
    for url in blocked_urls:
        is_allowed = guardrail.is_url_allowed(url)
        status = "✅ PASS" if not is_allowed else "❌ FAIL"
        print(f"  {status}: {url}")
        if not is_allowed:
            blocked_passed += 1
    
    print(f"\n📊 Blocked URLs: {blocked_passed}/{len(blocked_urls)} passed")
    
    # Test actual network requests
    print("\n🌐 Testing actual network requests...")
    
    # Enable the guardrail
    block_external_requests()
    
    # Test allowed request (this should work)
    try:
        print("  Testing allowed request to localhost...")
        response = requests.get("http://localhost:9000/health", timeout=1)
        print(f"  ✅ Localhost request succeeded: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Localhost request failed (expected if server not running): {e}")
    
    # Test blocked request (this should fail)
    try:
        print("  Testing blocked request to analytics...")
        response = requests.get("https://analytics.google.com/track", timeout=1)
        print(f"  ❌ Blocked request succeeded (this should not happen!): {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ✅ Blocked request failed as expected: {e}")
    
    # Test blocked request with urllib
    try:
        print("  Testing blocked urllib request...")
        response = urllib.request.urlopen("https://api.segment.io/track", timeout=1)
        print(f"  ❌ Blocked urllib request succeeded (this should not happen!): {response.status}")
    except urllib.error.URLError as e:
        print(f"  ✅ Blocked urllib request failed as expected: {e}")
    except Exception as e:
        print(f"  ✅ Blocked urllib request failed as expected: {e}")
    
    # Get final stats
    stats = guardrail.get_request_stats()
    print(f"\n📊 Final Stats: {stats}")
    
    # Calculate overall success rate
    total_tests = len(allowed_urls) + len(blocked_urls)
    total_passed = allowed_passed + blocked_passed
    success_rate = (total_passed / total_tests) * 100
    
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests})")
    
    if success_rate >= 95:
        print("🎉 Guardrail system is working excellently!")
        return True
    elif success_rate >= 80:
        print("⚠️  Guardrail system is working well but needs improvement.")
        return True
    else:
        print("❌ Guardrail system has significant issues.")
        return False

if __name__ == "__main__":
    success = test_url_guardrail()
    sys.exit(0 if success else 1)
