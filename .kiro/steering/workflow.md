---
inclusion: always
---

# Development Workflow Guidelines

## Code Before Creation Principle

**ALWAYS check existing resources before creating new code:**

1. **Check existing files first**
   - Use `listDirectory`, `fileSearch`, or `grepSearch` to find similar functionality
   - Read existing implementations to understand patterns
   - Reuse or extend existing code rather than duplicating

2. **Check existing data/resources**
   - Look for existing data files, configs, or outputs
   - Check if data has already been collected or processed
   - Verify what's in databases (Neo4j, etc.) before querying

3. **Check existing scripts**
   - Look in `scripts/` directory for similar utilities
   - Check if a script already does what you need
   - Extend existing scripts rather than creating new ones

4. **Check existing documentation**
   - Read `docs/` files to understand what's already documented
   - Check README and other guides for existing patterns
   - Look for existing examples or templates

## Workflow Steps

When asked to implement something:

1. **Explore** - Search for existing implementations
2. **Analyze** - Understand what exists and what's missing
3. **Plan** - Decide whether to reuse, extend, or create new
4. **Implement** - Write minimal code that builds on existing work
5. **Verify** - Test that it works with existing systems

## Anti-Patterns to Avoid

❌ Immediately writing new code without checking existing files
❌ Creating duplicate functionality that already exists
❌ Ignoring existing patterns and conventions
❌ Re-collecting data that's already available
❌ Creating new files when existing ones could be extended

## Examples

**Good:**
```
User: "Create a script to analyze Neo4j data"
Agent: 
1. Check scripts/ directory for existing Neo4j scripts
2. Read existing scripts to understand patterns
3. Extend or create based on what exists
```

**Bad:**
```
User: "Create a script to analyze Neo4j data"
Agent: Immediately creates new script without checking
```

## Remember

- **Exploration is not wasted time** - it prevents duplication
- **Reading existing code teaches patterns** - maintain consistency
- **Reusing code is faster** - less to write and test
- **Users appreciate efficiency** - don't reinvent the wheel
