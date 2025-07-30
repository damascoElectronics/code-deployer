# Software Bill of Materials (BoM) for SysOAMP
*Version: 1.0 | Date: July 30, 2025*

## Core Runtime Components

### Programming Languages & Runtimes
* **Python 3.x** 
  * Version: 3.9+ (recommended)
  * Source: Official Python.org
  * Purpose: Primary development language
  * CVE Tracking: [Python CVE Database](https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=python)

### Message Queue Infrastructure
* **RabbitMQ**
  * Version: Latest stable (3.12.x)
  * Source: RabbitMQ Official / Docker Hub
  * Purpose: Message queue for log processing pipeline
  * CVE Tracking: [RabbitMQ Security](https://www.rabbitmq.com/news.html)
  * Dependencies: Erlang/OTP runtime

## Python Dependencies (requirements.txt)

### Current Dependencies
* **python-dateutil**
  * Version: 2.8.2
  * Source: PyPI
  * Purpose: Date/time parsing utilities
  * CVE Tracking: [python-dateutil CVEs](https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=python-dateutil)

### Additional Python Libraries (Recommended)
* **watchdog**
  * Version: 3.0.0+
  * Source: PyPI
  * Purpose: File system monitoring for log collection
  * CVE Tracking: Monitor PyPI security advisories

* **pika** (RabbitMQ client)
  * Version: 1.3.0+
  * Source: PyPI
  * Purpose: RabbitMQ Python client
  * CVE Tracking: [Pika GitHub Security](https://github.com/pika/pika/security)

* **requests**
  * Version: 2.31.0+
  * Source: PyPI
  * Purpose: HTTP client for API communications
  * CVE Tracking: [Requests CVEs](https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=requests)

* **flask** or **fastapi**
  * Version: Flask 2.3.0+ or FastAPI 0.100.0+
  * Source: PyPI
  * Purpose: HTTP API server for log collector
  * CVE Tracking: Framework-specific security advisories

## Container Infrastructure

### Container Runtime
* **Docker Engine**
  * Version: 20.10+ (preferably 24.0+)
  * Source: Docker Inc. / Distribution packages
  * Purpose: Container orchestration
  * CVE Tracking: [Docker Security Advisories](https://docs.docker.com/engine/security/non-events/)

### Base Container Images
* **python:3.11-slim** or **python:3.11-alpine**
  * Source: Docker Hub (Official Python images)
  * Purpose: Base runtime environment
  * CVE Tracking: [Official Python Docker Security](https://github.com/docker-library/python/issues)

* **rabbitmq:3.12-management**
  * Source: Docker Hub (Official RabbitMQ)
  * Purpose: Message queue service
  * CVE Tracking: RabbitMQ + Docker Hub security feeds

## Development & CI/CD Tools

### Version Control & CI/CD
* **GitLab CE**
  * Version: Latest stable
  * Source: GitLab Inc.
  * Purpose: Source control, CI/CD pipeline
  * CVE Tracking: [GitLab Security Releases](https://about.gitlab.com/security/)

* **GitLab Runner**
  * Version: Latest compatible with GitLab CE
  * Source: GitLab Inc.
  * Purpose: CI/CD job execution
  * Executor Type: Shell executor
  * CVE Tracking: GitLab security advisories

### Operating System Components
* **Debian GNU/Linux** (VM1)
  * Version: Latest stable (Bookworm 12.x)
  * Purpose: Host OS for GitLab and log processor
  * CVE Tracking: [Debian Security Tracker](https://security-tracker.debian.org/)

* **Linux Distribution** (VM2 - Docker host)
  * Purpose: Host OS for log collector
  * CVE Tracking: Distribution-specific security feeds

## Static Analysis & Security Tools

### Code Quality & Security Analysis
* **bandit**
  * Version: 1.7.5+
  * Source: PyPI
  * Purpose: Python security linting
  * Usage: `bandit -r ./src/`
  * CVE Tracking: [Bandit GitHub](https://github.com/PyCQA/bandit)

* **safety**
  * Version: 2.3.0+
  * Source: PyPI
  * Purpose: Python dependency vulnerability scanning
  * Usage: `safety check`
  * CVE Tracking: SafetyDB integration

* **semgrep**
  * Version: 1.45.0+
  * Source: Semgrep Inc.
  * Purpose: Static application security testing (SAST)
  * Usage: `semgrep --config=auto ./src/`
  * CVE Tracking: Semgrep security rules database

### Container Security
* **trivy**
  * Version: 0.45.0+
  * Source: Aqua Security
  * Purpose: Container image vulnerability scanning
  * Usage: `trivy image python:3.11-slim`
  * CVE Tracking: [Trivy Database](https://github.com/aquasecurity/trivy-db)

* **hadolint**
  * Version: 2.12.0+
  * Source: GitHub (hadolint/hadolint)
  * Purpose: Dockerfile linting and security checks
  * Usage: `hadolint Dockerfile`
  * CVE Tracking: Docker best practices enforcement

## Testing Framework

### Python Testing
* **pytest**
  * Version: 7.4.0+
  * Source: PyPI
  * Purpose: Unit and integration testing
  * CVE Tracking: [pytest GitHub Security](https://github.com/pytest-dev/pytest/security)

* **pytest-cov**
  * Version: 4.1.0+
  * Source: PyPI
  * Purpose: Code coverage measurement
  * CVE Tracking: Monitor PyPI advisories

* **mock** / **unittest.mock**
  * Version: Built-in with Python 3.3+
  * Purpose: Test mocking and isolation
  * CVE Tracking: Python standard library tracking

### Load & Performance Testing
* **locust**
  * Version: 2.17.0+
  * Source: PyPI
  * Purpose: Load testing for APIs
  * CVE Tracking: [Locust GitHub](https://github.com/locustio/locust)

## Network & Infrastructure Components

### VPN & Networking
* **OpenVPN** or **WireGuard**
  * Purpose: Secure VM-to-VM communication
  * CVE Tracking: [OpenVPN Security](https://openvpn.net/security/) / [WireGuard Security](https://www.wireguard.com/papers/wireguard.pdf)

* **SSH/OpenSSH**
  * Version: 8.0+
  * Purpose: Secure shell access between VMs
  * Key Type: ED25519
  * CVE Tracking: [OpenSSH Security](https://www.openssh.com/security.html)

## Database Components (Future)

### Recommended Database Options
* **PostgreSQL**
  * Version: 15.0+
  * Source: PostgreSQL Global Development Group
  * Purpose: Primary data storage for processed logs
  * CVE Tracking: [PostgreSQL Security](https://www.postgresql.org/support/security/)

* **Redis** (Optional)
  * Version: 7.0+
  * Source: Redis Ltd.
  * Purpose: Caching and session storage
  * CVE Tracking: [Redis Security](https://redis.io/topics/security)

## Monitoring & Observability

### Application Monitoring
* **prometheus-client** (Python)
  * Version: 0.17.0+
  * Source: PyPI
  * Purpose: Metrics collection and exposure
  * CVE Tracking: [Prometheus Security](https://prometheus.io/docs/operating/security/)

* **structlog**
  * Version: 23.1.0+
  * Source: PyPI
  * Purpose: Structured logging
  * CVE Tracking: Monitor PyPI security advisories

## Automated CVE Tracking Strategy

### Primary CVE Sources
1. **National Vulnerability Database (NVD)**: https://nvd.nist.gov/
2. **GitHub Security Advisories**: For open-source dependencies
3. **PyPI Security Advisories**: For Python packages
4. **Docker Hub Security Scanning**: For container images
5. **Distribution Security Teams**: For OS packages

### Automation Tools for CVE Tracking
* **Dependabot** (GitHub) or **GitLab Dependency Scanning**
  * Purpose: Automated dependency vulnerability detection
  * Integration: GitLab CI/CD pipeline

* **OWASP Dependency-Check**
  * Version: 8.4.0+
  * Purpose: Identify known vulnerabilities in dependencies
  * Usage: `dependency-check --project SysOAMP --scan ./`

* **Snyk** (Optional)
  * Purpose: Commercial vulnerability scanning
  * Integration: CLI tool and GitLab integration

## Security Compliance Tools

### SSDLC Compliance
* **SonarQube Community Edition**
  * Version: 9.9+
  * Purpose: Code quality and security analysis
  * Integration: GitLab CI/CD pipeline
  * CVE Tracking: [SonarQube Security](https://www.sonarqube.org/security/)

* **OWASP ZAP**
  * Version: 2.14.0+
  * Purpose: Dynamic application security testing (DAST)
  * Usage: Automated security scanning in CI/CD
  * CVE Tracking: [OWASP ZAP Releases](https://github.com/zaproxy/zaproxy/releases)

## Build & Deployment Tools

### Container Orchestration (Future)
* **docker-compose**
  * Version: 2.20.0+
  * Source: Docker Inc.
  * Purpose: Multi-container application definition
  * CVE Tracking: Docker security advisories

### Configuration Management
* **python-dotenv**
  * Version: 1.0.0+
  * Source: PyPI
  * Purpose: Environment variable management
  * CVE Tracking: Monitor PyPI advisories

## Recommended GitLab CI/CD Integration

```yaml
# .gitlab-ci.yml security scanning stages
security_scan:
  stage: test
  script:
    - safety check
    - bandit -r ./src/
    - semgrep --config=auto ./src/
    - trivy image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

## Update & Maintenance Schedule

### Regular Updates
* **Weekly**: Python package updates (automated via Dependabot)
* **Monthly**: Container base image updates and security patches
* **Quarterly**: Major version updates after testing
* **Immediate**: Critical security vulnerabilities (CVE score 9.0+)

### CVE Monitoring Alerts
* Set up automated alerts for CVSS scores ≥ 7.0
* Monitor security mailing lists for all major components
* Integrate vulnerability scanning into CI/CD pipeline

---

**Note**: This BoM should be updated whenever new dependencies are added or versions are changed. All components should be regularly scanned for vulnerabilities using the automated tools mentioned above.