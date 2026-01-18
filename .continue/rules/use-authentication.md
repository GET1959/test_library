---
globs: '["app/**/*.py"]'
description: Ensure that all protected routes use the authentication system and
  that user_id is properly linked to related models like Borrow.
alwaysApply: false
---

Always use JWT authentication for protected routes and include user_id in related models