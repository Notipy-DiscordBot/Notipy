# Security Policy

This document outlines how to report security vulnerabilities and the project’s response procedures.

## Supported Versions

We provide security updates for the following branches and releases:

- **master** (latest release)

## Reporting a Vulnerability

Please report security issues **privately** via Discord to out admins

https://discord.gg/HzAnBSCN7t


Include the following information:

- Detailed description of the vulnerability and its potential impact  
- Steps to reproduce the issue  
- Proof-of-Concept (PoC) code or logs, if available  
- A contact email or other means for follow-up  

⚠️ **Do not** report vulnerabilities via public GitHub issues. All security reports must be submitted privately.

## Our Response

1. **Acknowledgment**  
   We will confirm receipt within **48 hours**.  
2. **Initial Assessment & Prioritization**  
   We will evaluate severity and provide a response timeline within **72 hours**.  
3. **Patch Development**  
   We aim to deliver a major patch or mitigation within **7 days**.  
4. **Public Disclosure**  
   After release, we will publish an advisory and assign a CVE if necessary.

## Credential Management

- Store all secrets (Discord bot tokens, Notion API tokens, etc.) in environment variables.  
- **Do not** hard-code credentials in code or documentation.  
- If a secret is compromised, rotate the token immediately and notify the project team.

## Additional Resources

- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)  
- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)  
- [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)






