# MCP Inventory

## Why

Capture the available MCP servers/resources/templates so planning and implementation can use the right tools without guesswork.

## Checklist

- [ ] List MCP servers
- [ ] List resource templates per server
- [ ] List resources per server (if available)
- [ ] Record any auth/permission constraints
- [ ] Record “best tool for job” notes

## Inventory (paste outputs)

### Servers

- Output of `list_mcp_resources` (no `server` param):
  - `resources: []` (no MCP servers configured in this Codex run)

### Resource Templates

- Output of `list_mcp_resource_templates` (no `server` param):
  - `resourceTemplates: []`

### Resources

- N/A (no servers)

## Notes

- This run has no MCP servers available; use local repo analysis + `tavily` web search for research.
