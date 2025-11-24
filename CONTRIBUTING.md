# Contributing to Tulip Compliance Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Guidelines](#commit-guidelines)

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm 9+
- **Python** 3.11+
- **MongoDB** 7+ (or use Docker)
- **Git**
- **Docker** and Docker Compose (optional but recommended)

### Initial Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/tulip-compliance-test-1115.git
cd tulip-compliance-test-1115
```

2. **Install dependencies**

```bash
# Install all project dependencies
npm run install:all

# Or install individually
cd frontend && npm install --legacy-peer-deps
cd ../backend && pip install -r requirements.txt
```

3. **Set up pre-commit hooks**

```bash
pip install pre-commit
pre-commit install
```

4. **Configure environment variables**

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration

# E2E Tests
cp .env.test.example .env.test
# Edit .env.test with test credentials
```

5. **Start development servers**

```bash
# Terminal 1 - Backend
npm run dev:backend

# Terminal 2 - Frontend
npm run dev:frontend
```

## Development Workflow

### Creating a Feature Branch

```bash
# Update your main branch
git checkout main
git pull origin main

# Create a feature branch
git checkout -b feat/your-feature-name
# or
git checkout -b fix/bug-description
```

### Making Changes

1. **Write your code** following our [code standards](#code-standards)
2. **Add tests** for new features or bug fixes
3. **Run tests locally** to ensure nothing breaks
4. **Commit your changes** using [conventional commits](#commit-guidelines)

### Running Tests

```bash
# Run all quality checks
npm run quality:check

# Run frontend tests
npm run test:frontend

# Run backend tests
npm run test:backend

# Run E2E tests
npm run test:e2e

# Run all tests
npm run test:all
```

## Code Standards

### Frontend (JavaScript/React)

**Style Guide**: Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

**Key Principles**:
- Use functional components with hooks
- Keep components small and focused
- Use meaningful variable and function names
- Avoid prop drilling - use Context or state management
- Write self-documenting code

**Formatting**:
- 2 spaces for indentation
- Use semicolons
- Single quotes for strings (Prettier will handle this)
- Max line length: 100 characters

**Example**:

```javascript
// Good
const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser(userId).then(setUser).finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <LoadingSpinner />;
  if (!user) return <ErrorMessage />;

  return <div className="user-profile">{user.name}</div>;
};

// Bad
const UserProfile = (props) => {
  const [user, setUser] = useState(null)
  useEffect(() => {
    fetch('/api/users/' + props.userId).then(r => r.json()).then(data => setUser(data))
  }, [])
  return <div>{user?.name}</div>
}
```

**Linting and Formatting**:

```bash
# Check linting
npm run lint:frontend

# Auto-fix linting issues
cd frontend && npm run lint:fix

# Format code
npm run format:frontend
```

### Backend (Python)

**Style Guide**: Follow [PEP 8](https://peps.python.org/pep-0008/) and [PEP 257](https://peps.python.org/pep-0257/)

**Key Principles**:
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use descriptive variable names
- Handle errors explicitly

**Formatting**:
- 4 spaces for indentation (enforced by Black)
- Max line length: 100 characters
- Use Black for automatic formatting
- Use isort for import sorting

**Example**:

```python
# Good
from typing import List, Optional
from datetime import datetime

def process_user_data(
    user_id: str,
    include_metadata: bool = False
) -> Optional[dict]:
    """
    Process and retrieve user data.

    Args:
        user_id: The unique identifier for the user
        include_metadata: Whether to include metadata in response

    Returns:
        User data dictionary or None if user not found

    Raises:
        ValueError: If user_id is invalid
    """
    if not user_id:
        raise ValueError("user_id cannot be empty")

    user = db.users.find_one({"_id": user_id})
    if not user:
        return None

    if include_metadata:
        user["metadata"] = get_user_metadata(user_id)

    return user

# Bad
def process(id, meta=False):
    u = db.users.find_one({"_id": id})
    if meta:
        u["m"] = get_meta(id)
    return u
```

**Linting and Formatting**:

```bash
# Format code
npm run format:backend

# Check linting
npm run lint:backend

# Type checking
cd backend && python -m mypy . --ignore-missing-imports
```

### Testing Standards

#### Frontend Tests

- Write tests for all new components
- Aim for >80% code coverage
- Test user interactions, not implementation details
- Mock external dependencies

```javascript
// Good test
test('submits form with user data', async () => {
  const onSubmit = jest.fn();
  render(<UserForm onSubmit={onSubmit} />);

  await userEvent.type(screen.getByLabelText(/name/i), 'John Doe');
  await userEvent.click(screen.getByRole('button', { name: /submit/i }));

  expect(onSubmit).toHaveBeenCalledWith({ name: 'John Doe' });
});
```

#### Backend Tests

- Write tests for all API endpoints
- Test both success and error cases
- Use fixtures for test data
- Aim for >80% code coverage

```python
def test_create_user_success():
    """Test successful user creation."""
    response = client.post("/api/users", json={
        "email": "test@example.com",
        "password": "secure_password"
    })

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_create_user_duplicate_email():
    """Test user creation with duplicate email."""
    # Create first user
    client.post("/api/users", json={
        "email": "test@example.com",
        "password": "password1"
    })

    # Attempt to create duplicate
    response = client.post("/api/users", json={
        "email": "test@example.com",
        "password": "password2"
    })

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
```

#### E2E Tests

- Test critical user flows end-to-end
- Test across multiple browsers when relevant
- Keep tests independent and idempotent
- Use Page Object Model for complex flows

```javascript
// Good E2E test
test('user can complete registration flow', async ({ page }) => {
  await page.goto('/register');

  // Fill registration form
  await page.fill('[name="email"]', 'newuser@example.com');
  await page.fill('[name="password"]', 'SecurePass123!');
  await page.click('button[type="submit"]');

  // Verify success
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.locator('text=Welcome')).toBeVisible();
});
```

## Pull Request Process

### Before Submitting

1. **Run all tests and quality checks**

```bash
npm run quality:check
npm run test:all
```

2. **Update documentation** if needed
3. **Add tests** for new features
4. **Ensure commits follow** [conventional commits](#commit-guidelines)

### Submitting a Pull Request

1. **Push your branch** to your fork

```bash
git push origin feat/your-feature-name
```

2. **Create a Pull Request** on GitHub
   - Use a clear, descriptive title
   - Reference any related issues
   - Provide a detailed description of changes
   - Include screenshots for UI changes

3. **PR Description Template**:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Frontend unit tests added/updated
- [ ] Backend unit tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Pre-commit hooks pass
```

### Review Process

1. **Automated checks** will run (CI/CD, linting, tests)
2. **Code review** by maintainers
3. **Address feedback** and push updates
4. **Approval and merge** by maintainers

### After Merge

- Delete your feature branch
- Pull the latest main branch
- Celebrate! 🎉

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) for clear and consistent commit history.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Other changes (dependencies, etc.)

### Examples

```bash
# Feature
feat(auth): add two-factor authentication

# Bug fix
fix(upload): resolve file size validation bug

# Documentation
docs(readme): update installation instructions

# Test
test(e2e): add dashboard navigation tests

# Breaking change
feat(api)!: change authentication endpoint structure

BREAKING CHANGE: The /auth endpoint now requires a different payload format
```

### Scope

Use scope to identify which part of the codebase is affected:
- `auth`: Authentication/authorization
- `upload`: File upload functionality
- `dashboard`: Dashboard UI
- `api`: Backend API
- `db`: Database changes
- `e2e`: E2E tests
- `ci`: CI/CD pipeline

## Code Review Guidelines

### For Contributors

- Respond to feedback promptly and professionally
- Ask questions if feedback is unclear
- Make requested changes or explain why you disagree
- Keep PRs focused and reasonably sized

### For Reviewers

- Be respectful and constructive
- Explain the reasoning behind suggestions
- Approve when ready, request changes if needed
- Focus on:
  - Code correctness and logic
  - Test coverage
  - Security implications
  - Performance concerns
  - Code readability and maintainability

## Getting Help

- **Documentation**: Check `CI_CD_SETUP.md` for technical details
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Code Comments**: Add inline comments for complex logic

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Tulip Compliance Platform! 🚀
