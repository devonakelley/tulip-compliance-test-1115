# CI/CD and Testing Setup Documentation

This document describes the production-grade CI/CD pipeline and testing infrastructure for the Tulip Compliance Platform.

## Table of Contents

- [Overview](#overview)
- [Pre-commit Hooks](#pre-commit-hooks)
- [End-to-End Testing](#end-to-end-testing)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Local Development](#local-development)
- [Deployment](#deployment)

## Overview

The project uses a comprehensive testing and CI/CD strategy:

- **Pre-commit hooks** for code quality enforcement
- **Playwright** for E2E testing across multiple browsers
- **GitHub Actions** for automated testing and deployment
- **Docker** for consistent build and deployment environments

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Optionally run on all files
pre-commit run --all-files
```

### Hooks Configured

1. **General**
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON validation
   - Large file detection (>1MB)
   - Private key detection
   - Merge conflict detection

2. **Python** (Backend)
   - Black (code formatting)
   - isort (import sorting)
   - flake8 (linting)
   - mypy (type checking)

3. **JavaScript/React** (Frontend)
   - ESLint (linting)
   - Prettier (code formatting)

4. **Security**
   - detect-secrets (credential scanning)

### Manual Execution

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run eslint --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

## End-to-End Testing

E2E tests use Playwright to test critical user flows across multiple browsers.

### Installation

```bash
# Install Playwright
npm install --legacy-peer-deps

# Install browsers
npx playwright install --with-deps
```

### Running E2E Tests

```bash
# Run all tests (headless)
npm run test:e2e

# Run with UI mode (recommended for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
cd frontend && npm run e2e:headed

# Run specific test file
npx playwright test e2e/auth.spec.js

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Debug mode
npx playwright test --debug
```

### Test Structure

```
e2e/
├── auth.spec.js          # Authentication flow tests
├── dashboard.spec.js     # Dashboard functionality tests
├── landing.spec.js       # Landing page tests
├── qsp-upload.spec.js    # QSP upload workflow tests
├── performance.spec.js   # Performance and load tests
└── helpers/
    └── auth.js           # Test helper functions
```

### Writing Tests

See the [Playwright documentation](https://playwright.dev/docs/writing-tests) for detailed guidance.

Example test:

```javascript
const { test, expect } = require('@playwright/test');

test('should login successfully', async ({ page }) => {
  await page.goto('/');
  await page.fill('input[type="email"]', 'test@example.com');
  await page.fill('input[type="password"]', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
});
```

### Test Configuration

Test configuration is in `playwright.config.js`:

- **Base URL**: `http://localhost:3000` (configurable via `PLAYWRIGHT_BASE_URL`)
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Retries**: 2 retries on CI, 0 locally
- **Reporters**: HTML, JSON, JUnit

### Test Credentials

Set test credentials in `.env.test`:

```bash
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=testpassword
```

## GitHub Actions CI/CD

### Workflows

The project includes four GitHub Actions workflows:

#### 1. CI Pipeline (`ci.yml`)

**Triggers**: Push to main/develop branches, all PRs

**Jobs**:
- **frontend-test**: ESLint, build, unit tests, coverage
- **backend-test**: Black, isort, flake8, mypy, pytest, coverage
- **security-scan**: Trivy, npm audit, pip audit
- **docker-build**: Build and test Docker images

**Artifacts**:
- Frontend build output
- Test coverage reports (uploaded to Codecov)

#### 2. E2E Tests (`e2e.yml`)

**Triggers**: Push to main/develop, PRs, manual dispatch

**Jobs**:
- **e2e-tests**: Full E2E test suite with all browsers
- **e2e-matrix**: Parallel E2E tests across browsers

**Services**:
- MongoDB for backend testing

**Artifacts**:
- Playwright HTML reports
- Test results (JSON/JUnit)
- Screenshots and videos of failures

#### 3. Code Quality (`code-quality.yml`)

**Triggers**: Push to main/develop, all PRs

**Jobs**:
- **pre-commit**: Run all pre-commit hooks
- **prettier**: Code formatting check
- **eslint**: JavaScript linting
- **python-linters**: Python linting (Black, isort, flake8, mypy)
- **dependency-review**: Scan for vulnerable dependencies (PRs only)
- **commit-lint**: Validate commit message format (PRs only)

#### 4. Deploy (`deploy.yml`)

**Triggers**: Push to main/master, manual dispatch

**Jobs**:
- Build frontend and backend
- Run all tests
- Build and push Docker images
- Deploy to production/staging

**Required Secrets**:
- `DOCKER_REGISTRY`: Docker registry URL
- `DOCKER_USERNAME`: Docker username
- `DOCKER_PASSWORD`: Docker password
- `SERVER_HOST`: Deployment server (if using SSH)
- `SERVER_USER`: Server username
- `SSH_PRIVATE_KEY`: SSH key for deployment

### Status Badges

Add these to your README.md:

```markdown
[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
[![E2E Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/e2e.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/e2e.yml)
[![Code Quality](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/code-quality.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/code-quality.yml)
```

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

**Examples**:
```
feat(auth): add two-factor authentication
fix(upload): resolve file size validation issue
docs(readme): update installation instructions
test(e2e): add dashboard navigation tests
```

## Local Development

### Quick Start

```bash
# Install all dependencies
npm run install:all

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Start development servers
npm run dev:frontend   # Start frontend on :3000
npm run dev:backend    # Start backend on :5000
```

### Running Tests Locally

```bash
# Frontend tests
npm run test:frontend

# Backend tests
npm run test:backend

# E2E tests (requires both servers running)
npm run test:e2e

# All tests
npm run test:all
```

### Code Quality Checks

```bash
# Check code quality
npm run quality:check

# Auto-fix code quality issues
npm run quality:fix

# Run pre-commit on all files
npm run pre-commit
```

### Docker Development

```bash
# Build images
npm run docker:build

# Start services
npm run docker:up

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

## Deployment

### Production Deployment

The deployment workflow (`deploy.yml`) automatically deploys to production when:
- Code is pushed to `main` or `master` branch
- Manual workflow dispatch is triggered

### Manual Deployment

```bash
# Trigger deployment manually via GitHub Actions
# Go to: Actions → Deploy to Production → Run workflow

# Or deploy locally
cd frontend && npm run build
cd backend && docker build -t backend .
# Deploy to your infrastructure
```

### Environment Variables

Required environment variables for production:

**Frontend**:
- `REACT_APP_API_URL`: Backend API URL

**Backend**:
- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `ALLOWED_ORIGINS`: CORS allowed origins
- (See `backend/.env.example` for full list)

### Monitoring

After deployment:
1. Check GitHub Actions workflow status
2. Verify deployment in production environment
3. Monitor application logs
4. Check error tracking (if configured)

## Troubleshooting

### Pre-commit Hooks Failing

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Clear cache and retry
pre-commit clean
pre-commit run --all-files
```

### E2E Tests Failing Locally

```bash
# Ensure browsers are installed
npx playwright install --with-deps

# Start backend and frontend servers
npm run dev:backend
npm run dev:frontend

# Run tests in debug mode
npx playwright test --debug
```

### CI Pipeline Failing

1. Check the workflow logs in GitHub Actions
2. Run the same commands locally
3. Ensure all dependencies are up to date
4. Check for environment-specific issues

### Docker Build Issues

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

## Best Practices

1. **Always run tests locally** before pushing
2. **Use conventional commits** for clear history
3. **Keep pre-commit hooks enabled** for code quality
4. **Write E2E tests** for critical user flows
5. **Monitor CI/CD pipelines** for failures
6. **Update dependencies regularly** to avoid security issues
7. **Document breaking changes** in commit messages
8. **Review Playwright traces** for debugging test failures

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Docker Documentation](https://docs.docker.com/)

## Support

For issues or questions:
1. Check this documentation
2. Review existing GitHub Issues
3. Create a new issue with detailed information
