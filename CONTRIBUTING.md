# Contributing to VM Tool

## Code Organization

VM Tool follows a modular architecture with clear separation of concerns:

- `vm_tool/core/` - Core infrastructure (config, state, history)
- `vm_tool/strategies/` - Deployment strategies (blue-green, canary, A/B)
- `vm_tool/operations/` - Operations (metrics, alerting, reporting)
- `vm_tool/enterprise/` - Enterprise features (RBAC, audit, policy)
- `vm_tool/integrations/` - External integrations (webhooks, notifications)

## Adding Features

1. Determine the appropriate module directory
2. Create module with clear, focused responsibility
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

See `docs/code_organization.md` for detailed guidelines.

## Testing

```bash
# Run all tests
pytest -v

# Run specific module tests
pytest tests/unit/test_<module>.py -v

# Run integration tests
pytest tests/integration/ -v
```

## Documentation

- Update API docs in `docs/api/`
- Add usage examples in `docs/guides/`
- Update `CHANGELOG.md`
