---
name: notion-api
description: >
  This skill provides comprehensive instructions for interacting with the Notion API via REST calls.
  This skill should be used whenever the user asks to interact with Notion, including reading, creating,
  updating, or deleting pages, databases, blocks, comments, or any other Notion content. The skill
  covers authentication, all available endpoints, pagination, error handling, and best practices.
---

# Notion API Skill

This skill enables interaction with Notion workspaces through the Notion REST API. Use `curl` and `jq` for direct REST calls, or write ad-hoc scripts as appropriate for the task.

## Authentication

### API Key Handling

1. **Environment Variable**: Check if `NOTION_API_TOKEN` is available in the environment
2. **User-Provided Key**: If the user provides an API key in context, use that instead
3. **No Key Available**: If neither is available, use AskUserQuestion (or equivalent) to request the API key from the user

**IMPORTANT**: Never display, log, or send `NOTION_API_TOKEN` anywhere except in the `Authorization` header. Confirm its existence, ask if missing, use it in requests—but never echo or expose it.

### Request Headers

All requests require these headers:

```bash
-H "Authorization: Bearer $NOTION_API_TOKEN" \
-H "Notion-Version: 2025-09-03" \
-H "Content-Type: application/json"
```

### Verifying Authentication

Test the API key by retrieving the bot user:

```bash
curl -s "https://api.notion.com/v1/users/me" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

## Base URL and Conventions

- **Base URL**: `https://api.notion.com`
- **API Version**: `2025-09-03` (required header)
- **Data Format**: JSON for all request/response bodies
- **IDs**: UUIDv4 format (dashes optional in requests)
- **Timestamps**: ISO 8601 format (`2020-08-12T02:12:33.231Z`)
- **Property Names**: `snake_case`
- **Empty Values**: Use `null` instead of empty strings

## Rate Limits

- **Average**: 3 requests per second per integration
- **Bursts**: Brief bursts above this limit are allowed
- **Rate Limited Response**: HTTP 429 with `Retry-After` header
- **Strategy**: Implement exponential backoff when receiving 429 responses

## Request Size Limits

| Type | Limit |
|------|-------|
| Maximum block elements per payload | 1000 |
| Maximum payload size | 500KB |
| Rich text content | 2000 characters |
| URLs | 2000 characters |
| Equations | 1000 characters |
| Email addresses | 200 characters |
| Phone numbers | 200 characters |
| Multi-select options | 100 items |
| Relations | 100 related pages |
| People mentions | 100 users |
| Block arrays per request | 100 elements |

## Confirmation for Destructive Operations

**IMPORTANT**: Before executing any operation that modifies or deletes data, ask the user for confirmation. This includes:
- Updating pages or blocks
- Deleting/archiving pages or blocks
- Modifying database schemas
- Creating pages (if multiple or in batch)
- Any bulk operations

For a logical group of related operations, a single confirmation is sufficient.

## Core API Endpoints

### Search

Search across all accessible pages and databases:

```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search term",
    "filter": {"property": "object", "value": "page"},
    "sort": {"direction": "descending", "timestamp": "last_edited_time"},
    "page_size": 100
  }' | jq
```

Filter values: `"page"` or `"data_source"` (or omit for both)

### Pages

#### Retrieve a Page

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

**Note**: This returns page properties, not content. For content, use "Retrieve block children" with the page ID.

#### Create a Page

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "parent-page-id"},
    "properties": {
      "title": {
        "title": [{"text": {"content": "Page Title"}}]
      }
    },
    "children": [
      {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [{"type": "text", "text": {"content": "Paragraph content"}}]
        }
      }
    ]
  }' | jq
```

Parent options:
- `{"page_id": "..."}` - Create under a page
- `{"database_id": "..."}` - Create in a database (legacy)
- `{"data_source_id": "..."}` - Create in a data source (API v2025-09-03+)

#### Update a Page

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "title": {"title": [{"text": {"content": "Updated Title"}}]}
    },
    "icon": {"type": "emoji", "emoji": "📝"},
    "archived": false
  }' | jq
```

Additional update options: `cover`, `is_locked`, `in_trash`

#### Archive (Delete) a Page

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"archived": true}' | jq
```

#### Retrieve a Page Property Item

For properties with more than 25 references:

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/properties/{property_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

### Blocks (Page Content)

#### Retrieve Block Children

```bash
curl -s "https://api.notion.com/v1/blocks/{block_id}/children?page_size=100" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

Use the page ID as `block_id` to get page content. Check `has_children` on each block for nested content.

#### Append Block Children

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{block_id}/children" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
          "rich_text": [{"type": "text", "text": {"content": "New Section"}}]
        }
      },
      {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [{"type": "text", "text": {"content": "Content here"}}]
        }
      }
    ]
  }' | jq
```

Maximum 100 blocks per request, up to 2 levels of nesting.

Position options in request body:
- Default: appends to end
- `"position": {"type": "start"}` - Insert at beginning
- `"position": {"type": "after_block", "after_block": {"id": "block-id"}}` - Insert after specific block

#### Retrieve a Block

```bash
curl -s "https://api.notion.com/v1/blocks/{block_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

#### Update a Block

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{block_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "paragraph": {
      "rich_text": [{"type": "text", "text": {"content": "Updated content"}}]
    }
  }' | jq
```

The update replaces the entire value for the specified field.

#### Delete a Block

```bash
curl -s -X DELETE "https://api.notion.com/v1/blocks/{block_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

Moves block to trash (can be restored).

### Databases

#### Retrieve a Database

```bash
curl -s "https://api.notion.com/v1/databases/{database_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

Returns database structure including data sources and properties.

#### Query a Database

```bash
curl -s -X POST "https://api.notion.com/v1/databases/{database_id}/query" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "property": "Status",
      "select": {"equals": "Done"}
    },
    "sorts": [
      {"property": "Created", "direction": "descending"}
    ],
    "page_size": 100
  }' | jq
```

See `references/filters-and-sorts.md` for comprehensive filter and sort documentation.

#### Create a Database

```bash
curl -s -X POST "https://api.notion.com/v1/databases" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "parent-page-id"},
    "title": [{"type": "text", "text": {"content": "My Database"}}],
    "is_inline": true,
    "initial_data_source": {
      "properties": {
        "Name": {"title": {}},
        "Status": {
          "select": {
            "options": [
              {"name": "To Do", "color": "red"},
              {"name": "In Progress", "color": "yellow"},
              {"name": "Done", "color": "green"}
            ]
          }
        },
        "Due Date": {"date": {}}
      }
    }
  }' | jq
```

#### Update a Database

```bash
curl -s -X PATCH "https://api.notion.com/v1/databases/{database_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "title": [{"text": {"content": "Updated Title"}}],
    "description": [{"text": {"content": "Database description"}}]
  }' | jq
```

### Data Sources (API v2025-09-03+)

Data sources are individual tables within a database. As of API version 2025-09-03, databases can contain multiple data sources.

#### Create a Data Source

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"type": "database_id", "database_id": "database-id"},
    "title": [{"type": "text", "text": {"content": "New Data Source"}}],
    "properties": {
      "Name": {"title": {}},
      "Description": {"rich_text": {}}
    }
  }' | jq
```

### Users

#### List All Users

```bash
curl -s "https://api.notion.com/v1/users?page_size=100" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

#### Retrieve a User

```bash
curl -s "https://api.notion.com/v1/users/{user_id}" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

#### Retrieve Bot User (Self)

```bash
curl -s "https://api.notion.com/v1/users/me" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

### Comments

#### Retrieve Comments

```bash
curl -s "https://api.notion.com/v1/comments?block_id={block_id}&page_size=100" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" | jq
```

Use a page ID as `block_id` for page-level comments.

#### Create a Comment

On a page:

```bash
curl -s -X POST "https://api.notion.com/v1/comments" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "page-id"},
    "rich_text": [{"type": "text", "text": {"content": "Comment content"}}]
  }' | jq
```

Reply to a discussion:

```bash
curl -s -X POST "https://api.notion.com/v1/comments" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "discussion_id": "discussion-id",
    "rich_text": [{"type": "text", "text": {"content": "Reply content"}}]
  }' | jq
```

**Note**: The API cannot start new inline discussion threads or edit/delete existing comments.

## Pagination

Paginated endpoints return:
- `has_more`: Boolean indicating more results exist
- `next_cursor`: Cursor for the next page
- `results`: Array of items

To iterate through all results:

1. Make the initial request (omit `start_cursor`)
2. Check `has_more` in the response
3. If `true`, extract `next_cursor` and include it as `start_cursor` in the next request
4. Repeat until `has_more` is `false`

Example request with cursor:

```json
{
  "page_size": 100,
  "start_cursor": "v1%7C..."
}
```

## Error Handling

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `invalid_json` | Request body is not valid JSON |
| 400 | `invalid_request_url` | URL is malformed |
| 400 | `invalid_request` | Request is not supported |
| 400 | `validation_error` | Request body doesn't match expected schema |
| 400 | `missing_version` | Missing Notion-Version header |
| 401 | `unauthorized` | Invalid bearer token |
| 403 | `restricted_resource` | Token lacks permission |
| 404 | `object_not_found` | Resource doesn't exist or not shared with integration |
| 409 | `conflict_error` | Data collision during transaction |
| 429 | `rate_limited` | Rate limit exceeded (check Retry-After header) |
| 500 | `internal_server_error` | Unexpected server error |
| 503 | `service_unavailable` | Notion unavailable or 60s timeout exceeded |
| 503 | `database_connection_unavailable` | Database unresponsive |
| 504 | `gateway_timeout` | Request timeout |

## Best Practices

1. **Store IDs**: When creating pages/databases, store the returned IDs for future updates
2. **Use Property IDs**: Reference properties by ID rather than name for stability
3. **Batch Operations**: Aggregate multiple small operations into fewer requests
4. **Respect Rate Limits**: Implement exponential backoff for 429 responses
5. **Check `has_more`**: Always handle pagination for list endpoints
6. **Validate Before Updates**: Retrieve current state before making updates
7. **Use Environment Variables**: Never hardcode API keys
8. **Handle Errors Gracefully**: Check response status codes and error messages
9. **Schema Size**: Keep database schemas under 50KB for optimal performance
10. **Properties Limit**: Properties with >25 page references require separate retrieval

## References

For detailed documentation on specific topics, see:
- `references/block-types.md` - All supported block types and their structures
- `references/property-types.md` - Database property types and value formats
- `references/filters-and-sorts.md` - Database query filter and sort syntax
- `references/rich-text.md` - Rich text object structure and annotations
