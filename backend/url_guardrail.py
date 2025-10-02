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
URL Guardrail System
Author: Emad Noorizadeh

This module provides comprehensive protection against unauthorized external URL calls.
It intercepts and blocks all network requests except for explicitly allowed APIs.
"""

import os
import sys
import socket
import urllib.request
import urllib.parse
import urllib.error
import requests
import threading
import time
from typing import List, Set, Optional, Callable
from functools import wraps
import logging

class URLGuardrail:
    """
    Comprehensive URL guardrail system that blocks all external calls
    except for explicitly allowed APIs.
    """
    
    def __init__(self):
        self.allowed_domains: Set[str] = {
            # Essential APIs only
            "api.openai.com",
            "api.langgraph.com", 
            "api.chroma.ai",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1"  # IPv6 localhost
        }
        
        self.allowed_paths: Set[str] = {
            # OpenAI API paths
            "/v1/chat/completions",
            "/v1/embeddings",
            "/v1/models",
            "/v1/completions",
            
            # LangGraph API paths (if any)
            "/api/v1/",
            
            # ChromaDB API paths (if any)
            "/api/v1/",
            
            # Local paths
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/sessions",
            "/chat",
            "/documents",
            "/upload",
            "/delete",
            "/search",
            "/status"
        }
        
        self.blocked_domains: Set[str] = {
            # Telemetry and analytics
            "api.openai.com/v1/telemetry",
            "api.anthropic.com",
            "api.langchain.com",
            "api.llamaindex.ai",
            "api.huggingface.co",
            "api.spacy.io",
            "api.chroma.ai/telemetry",
            "analytics.google.com",
            "www.google-analytics.com",
            "telemetry.mozilla.org",
            "telemetry.microsoft.com",
            "api.segment.io",
            "api.mixpanel.com",
            "api.amplitude.com",
            "api.hotjar.com",
            "api.fullstory.com",
            "api.logrocket.com",
            "api.sentry.io",
            "api.bugsnag.com",
            "api.rollbar.com",
            "api.newrelic.com",
            "api.datadoghq.com",
            "api.splunk.com",
            "api.elastic.co",
            "api.logstash.com",
            "api.kibana.com",
            "api.grafana.com",
            "api.prometheus.io",
            "api.influxdata.com",
            "api.timescale.com",
            "api.cockroachlabs.com",
            "api.mongodb.com",
            "api.redis.com",
            "api.postgresql.org",
            "api.mysql.com",
            "api.oracle.com",
            "api.microsoft.com",
            "api.amazon.com",
            "api.google.com",
            "api.facebook.com",
            "api.twitter.com",
            "api.linkedin.com",
            "api.github.com",
            "api.gitlab.com",
            "api.bitbucket.org",
            "api.docker.com",
            "api.kubernetes.io",
            "api.helm.sh",
            "api.terraform.io",
            "api.ansible.com",
            "api.puppet.com",
            "api.chef.io",
            "api.saltstack.com",
            "api.consul.io",
            "api.vault.io",
            "api.nomad.io",
            "api.terraform.io",
            "api.packer.io",
            "api.vagrantup.com",
            "api.virtualbox.org",
            "api.vmware.com",
            "api.citrix.com",
            "api.parallels.com",
            "api.qemu.org",
            "api.kvm.org",
            "api.xen.org",
            "api.hyperv.com",
            "api.docker.com",
            "api.podman.io",
            "api.containerd.io",
            "api.crio.io",
            "api.runc.io",
            "api.gvisor.io",
            "api.kata-containers.io",
            "api.firecracker.com",
            "api.nabla.com",
            "api.unikraft.io",
            "api.osv.io",
            "api.gvisor.io",
            "api.kata-containers.io",
            "api.firecracker.com",
            "api.nabla.com",
            "api.unikraft.io",
            "api.osv.io"
        }
        
        self.blocked_keywords: Set[str] = {
            "telemetry", "analytics", "tracking", "metrics", "stats",
            "logging", "monitoring", "debugging", "profiling",
            "crash", "error", "exception", "trace", "span",
            "event", "click", "view", "impression", "conversion",
            "ab_test", "experiment", "feature_flag", "toggle",
            "config", "settings", "preferences", "user_data",
            "session", "cookie", "token", "auth", "login",
            "signup", "register", "password", "reset", "verify",
            "email", "sms", "notification", "alert", "reminder",
            "backup", "sync", "replicate", "mirror", "clone",
            "update", "upgrade", "patch", "hotfix", "release",
            "deploy", "rollout", "rollback", "migration", "schema",
            "index", "search", "query", "filter", "sort", "paginate",
            "cache", "redis", "memcached", "elasticsearch", "solr",
            "database", "db", "sql", "nosql", "mongodb", "postgres",
            "mysql", "oracle", "sqlite", "cassandra", "dynamodb",
            "s3", "gcs", "azure", "blob", "storage", "bucket",
            "cdn", "cloudfront", "cloudflare", "fastly", "maxcdn",
            "dns", "domain", "subdomain", "wildcard", "certificate",
            "ssl", "tls", "https", "http", "ftp", "sftp", "scp",
            "ssh", "telnet", "rsh", "rlogin", "rexec", "rcp",
            "nfs", "cifs", "smb", "afp", "webdav", "caldav",
            "carddav", "ldap", "ad", "kerberos", "oauth", "saml",
            "jwt", "jwe", "jws", "jwk", "jwa", "jose", "jose4j",
            "jose4j", "jose4j", "jose4j", "jose4j", "jose4j"
        }
        
        self.request_log: List[dict] = []
        self.blocked_requests: List[dict] = []
        self.monitoring_active = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)
        
        # Create log file
        os.makedirs("./logs", exist_ok=True)
        file_handler = logging.FileHandler("./logs/url_guardrail.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        print("🛡️  URL Guardrail initialized")
    
    def is_url_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed based on domain and path.
        
        Args:
            url: The URL to check
            
        Returns:
            True if allowed, False if blocked
        """
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            # Remove port numbers from domain for localhost
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Check if domain is explicitly blocked
            if domain in self.blocked_domains:
                self.logger.warning(f"Blocked domain: {domain}")
                return False
            
            # Check if domain contains blocked keywords
            for keyword in self.blocked_keywords:
                if keyword in domain or keyword in path:
                    self.logger.warning(f"Blocked keyword '{keyword}' in URL: {url}")
                    return False
            
            # Check if domain is in allowed list
            if domain in self.allowed_domains:
                # For localhost, be more permissive
                if domain in ["localhost", "127.0.0.1", "0.0.0.0", "::1"]:
                    return True
                # For external APIs, check specific paths
                elif path in self.allowed_paths or path.startswith(tuple(self.allowed_paths)):
                    return True
                else:
                    self.logger.warning(f"Blocked path '{path}' for allowed domain '{domain}'")
                    return False
            
            # Block all other domains
            self.logger.warning(f"Blocked unknown domain: {domain}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error parsing URL {url}: {e}")
            return False
    
    def log_request(self, url: str, method: str = "GET", allowed: bool = True):
        """Log a request attempt"""
        request_info = {
            "timestamp": time.time(),
            "url": url,
            "method": method,
            "allowed": allowed
        }
        
        self.request_log.append(request_info)
        
        if not allowed:
            self.blocked_requests.append(request_info)
            self.logger.warning(f"BLOCKED {method} {url}")
        else:
            self.logger.info(f"ALLOWED {method} {url}")
    
    def get_blocked_requests(self) -> List[dict]:
        """Get list of blocked requests"""
        return self.blocked_requests.copy()
    
    def get_request_stats(self) -> dict:
        """Get request statistics"""
        total_requests = len(self.request_log)
        blocked_requests = len(self.blocked_requests)
        allowed_requests = total_requests - blocked_requests
        
        return {
            "total_requests": total_requests,
            "allowed_requests": allowed_requests,
            "blocked_requests": blocked_requests,
            "block_rate": blocked_requests / total_requests if total_requests > 0 else 0
        }

# Global guardrail instance
guardrail = URLGuardrail()

def block_external_requests():
    """
    Monkey patch urllib and requests to block external requests.
    This is a nuclear option that blocks ALL external requests.
    """
    
    # Store original functions
    original_urlopen = urllib.request.urlopen
    original_request = requests.request
    original_get = requests.get
    original_post = requests.post
    original_put = requests.put
    original_delete = requests.delete
    original_patch = requests.patch
    original_head = requests.head
    original_options = requests.options
    
    def guarded_urlopen(url, *args, **kwargs):
        """Guarded version of urllib.request.urlopen"""
        if not guardrail.is_url_allowed(str(url)):
            guardrail.log_request(str(url), "URLOPEN", False)
            raise urllib.error.URLError(f"External URL blocked by guardrail: {url}")
        
        guardrail.log_request(str(url), "URLOPEN", True)
        return original_urlopen(url, *args, **kwargs)
    
    def guarded_request(method, url, *args, **kwargs):
        """Guarded version of requests.request"""
        if not guardrail.is_url_allowed(url):
            guardrail.log_request(url, method.upper(), False)
            raise requests.exceptions.RequestException(f"External URL blocked by guardrail: {url}")
        
        guardrail.log_request(url, method.upper(), True)
        return original_request(method, url, *args, **kwargs)
    
    def guarded_get(url, *args, **kwargs):
        """Guarded version of requests.get"""
        return guarded_request("GET", url, *args, **kwargs)
    
    def guarded_post(url, *args, **kwargs):
        """Guarded version of requests.post"""
        return guarded_request("POST", url, *args, **kwargs)
    
    def guarded_put(url, *args, **kwargs):
        """Guarded version of requests.put"""
        return guarded_request("PUT", url, *args, **kwargs)
    
    def guarded_delete(url, *args, **kwargs):
        """Guarded version of requests.delete"""
        return guarded_request("DELETE", url, *args, **kwargs)
    
    def guarded_patch(url, *args, **kwargs):
        """Guarded version of requests.patch"""
        return guarded_request("PATCH", url, *args, **kwargs)
    
    def guarded_head(url, *args, **kwargs):
        """Guarded version of requests.head"""
        return guarded_request("HEAD", url, *args, **kwargs)
    
    def guarded_options(url, *args, **kwargs):
        """Guarded version of requests.options"""
        return guarded_request("OPTIONS", url, *args, **kwargs)
    
    # Apply patches
    urllib.request.urlopen = guarded_urlopen
    requests.request = guarded_request
    requests.get = guarded_get
    requests.post = guarded_post
    requests.put = guarded_put
    requests.delete = guarded_delete
    requests.patch = guarded_patch
    requests.head = guarded_head
    requests.options = guarded_options
    
    print("🛡️  External request blocking activated")

def create_network_monitor():
    """
    Create a network monitoring thread that watches for unauthorized connections.
    """
    def monitor_network():
        """Monitor network connections"""
        while True:
            try:
                # Check for new blocked requests
                if guardrail.blocked_requests:
                    print(f"🚨 {len(guardrail.blocked_requests)} blocked requests detected")
                
                # Get stats
                stats = guardrail.get_request_stats()
                if stats["total_requests"] > 0:
                    print(f"📊 Network stats: {stats['allowed_requests']} allowed, {stats['blocked_requests']} blocked")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"⚠️ Network monitor error: {e}")
                time.sleep(60)  # Wait longer on error
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_network, daemon=True)
    monitor_thread.start()
    print("🔍 Network monitoring started")

def test_guardrail():
    """Test the guardrail system"""
    print("🧪 Testing URL guardrail...")
    
    test_urls = [
        "https://api.openai.com/v1/chat/completions",  # Should be allowed
        "https://api.openai.com/v1/telemetry",  # Should be blocked
        "https://api.langchain.com/telemetry",  # Should be blocked
        "https://analytics.google.com/track",  # Should be blocked
        "https://localhost:9000/health",  # Should be allowed
        "https://api.huggingface.co/models",  # Should be blocked
    ]
    
    for url in test_urls:
        allowed = guardrail.is_url_allowed(url)
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"  {status}: {url}")

if __name__ == "__main__":
    # Test the guardrail
    test_guardrail()
    
    # Show stats
    stats = guardrail.get_request_stats()
    print(f"\n📊 Guardrail Stats: {stats}")
