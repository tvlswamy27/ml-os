# Plugin Development and Discovery

Details the manifest-based plugin architecture.

## Manifest Format
Every plugin must declare a `PLUGIN_INFO` dictionary:
```python
PLUGIN_INFO = {
    "name": "CustomPlanningAlgorithm",
    "version": "1.0.0",
    "type": "PLANNING",
    "author": "Core Team",
    "mlos_version": "2.1.0",
    "entry_point": "CustomPlanner"
}
```

## Discovery Registry
The registry automatically registers entry point classes, validating version matches before execution.
