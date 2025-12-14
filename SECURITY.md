# Security Guidelines for EcoFlow API Integration

## 🔐 Security Best Practices

### 🚫 **NEVER Commit to Git**
- Real API credentials (username, password, tokens)
- Device serial numbers
- Private keys and certificates
- Environment files with real values
- Configuration files with secrets

### ✅ **Safe Practices**

#### 1. **Use Environment Variables**
```bash
# Copy example file
cp .env.example .env.local

# Edit with your values (NEVER commit .env.local)
ECOFLOW_USERNAME=your_username
ECOFLOW_PASSWORD=your_password
ECOFLOW_DEVICE_SN=your_device_sn
```

#### 2. **Use Configuration Templates**
```json
// Copy example config
cp config.example.json config.local.json

// Edit with your values (NEVER commit config.local.json)
```

#### 3. **Secure Credential Storage**
- Use system keyring for storing credentials
- Consider using Home Assistant's built-in credential storage
- Use encrypted configuration files when possible

#### 4. **Development Environment**
- Use mock data for testing when possible
- Never use production credentials in development
- Rotate credentials regularly

### 🛡️ **Protected Files (.gitignore)**

The following files are automatically excluded from version control:

#### **Configuration Files**
- `.env.local` - Local environment variables
- `config.local.json` - Local configuration
- `secrets.json` - Secret storage
- `credentials.json` - Credential file

#### **Security Files**
- `*.key` - Private keys
- `*.pem` - PEM certificates
- `*.p12` - PKCS#12 certificates
- `*.pfx` - PFX certificates

#### **Development Files**
- `test_*.py` - Test files with credentials
- `debug_*.py` - Debug scripts
- `api_response_*.json` - API responses with sensitive data

#### **Cache and Temporary**
- `.ruff_cache/` - Linting cache
- `.mypy_cache/` - Type checking cache
- `*.log` - Log files
- `*.tmp` - Temporary files

### 🔍 **Security Checklist**

#### Before Committing:
- [ ] No real credentials in code
- [ ] No API keys in configuration files
- [ ] No device serial numbers in documentation
- [ ] No passwords in comments
- [ ] Environment files are in .gitignore
- [ ] Test files with credentials are excluded

#### In Development:
- [ ] Use mock data when possible
- [ ] Validate input from API responses
- [ ] Implement proper error handling
- [ ] Use secure HTTP connections (HTTPS)
- [ ] Implement session timeout

#### For Production:
- [ ] Use environment variables for secrets
- [ ] Implement proper logging (no sensitive data)
- [ ] Use secure credential storage
- [ ] Regular security audits
- [ ] Keep dependencies updated

### 🚨 **Incident Response**

If you accidentally commit sensitive data:

1. **Immediate Action**
   ```bash
   # Remove the file from git history
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch filename' --prune-empty --tag-name-filter cat -- --all

   # Force push to remove from remote
   git push origin --force --all
   ```

2. **Rotate Credentials**
   - Change EcoFlow password immediately
   - Generate new API tokens if applicable
   - Update any stored credentials

3. **Review Access**
   - Check repository access logs
   - Review who has access to the repository
   - Consider making repository private temporarily

### 📚 **Additional Resources**

- [Home Assistant Security Guidelines](https://www.home-assistant.io/docs/security/)
- [Python Security Best Practices](https://docs.python.org/3/library/security.html)
- [Git Security Best Practices](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)

### ⚠️ **Important Notes**

- This integration handles sensitive EcoFlow API credentials
- Always assume that committed code can be accessed by others
- Use the principle of least privilege for API access
- Regular security reviews are recommended

---

**Remember: Security is everyone's responsibility!** 🛡️
