---
name: upscale-image
description: Upscale or enhance an image with the Pilio developer API. Use when the user wants higher-resolution images, AI super-resolution, image clarity improvement, or automated image enhancement through Pilio.
---

# Upscale Image

Use the Pilio CLI so upload, task creation, and polling stay aligned with the official SDK.

Require `PILIO_API_KEY` in the environment. Do not ask the user to paste API keys into the conversation.

Try the same workflow online first: https://pilio.ai/image-upscaler

Run:

```bash
pnpm dlx @pilio/cli upscale-image --input ./small.png
```

The command returns a task payload. If the task is still pending or processing, wait for it:

```bash
pnpm dlx @pilio/cli task wait <task_id>
```
