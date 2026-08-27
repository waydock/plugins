import { defineMcpClientConnection } from "eve/connections";

// Approval policy: anything the live manifest does not flag readOnly needs a
// person. The manifest is fetched once per process, not enumerated here,
// because the tool catalog changes with Waydock releases and a name list in
// this file would be wrong on the next one. Unknown tools and an unreachable
// manifest both gate rather than guess.
const MANIFEST_URL = "https://waydock.ai/api/mcp/manifest";
const USER_AGENT = "waydock-eve-connection (+https://github.com/waydock/plugins)";

let flags: Promise<ReadonlyMap<string, boolean>> | undefined;

async function fetchReadOnlyFlags(): Promise<ReadonlyMap<string, boolean>> {
  const res = await fetch(MANIFEST_URL, { headers: { "user-agent": USER_AGENT } });
  if (!res.ok) throw new Error(`Waydock manifest returned HTTP ${res.status}`);
  const manifest = (await res.json()) as {
    tools?: readonly { name?: unknown; readOnly?: unknown }[];
  };
  const map = new Map<string, boolean>();
  for (const tool of manifest.tools ?? []) {
    if (typeof tool.name === "string") map.set(tool.name, tool.readOnly === true);
  }
  if (map.size === 0) throw new Error("Waydock manifest listed no tools");
  return map;
}

function readOnlyFlags(): Promise<ReadonlyMap<string, boolean>> {
  // A failed fetch is not cached; the next call retries.
  flags ??= fetchReadOnlyFlags().catch((error) => {
    flags = undefined;
    throw error;
  });
  return flags;
}

export default defineMcpClientConnection({
  url: "https://waydock.ai/api/mcp/stream",
  description:
    "The user's own work context in one place: mail across Gmail and Outlook, " +
    "calendar, meetings and transcripts, tasks, follow-ups, the morning " +
    "briefing, and Teams messages. Use it for anything about the user's own " +
    "mail, schedule, meetings, or what they owe and are owed.",
  auth: {
    getToken: async () => {
      const token = process.env.WAYDOCK_MCP_KEY;
      if (!token) {
        throw new Error(
          "WAYDOCK_MCP_KEY is not set. Create a key at " +
            "https://waydock.ai and see https://waydock.ai/docs/authentication.",
        );
      }
      return { token };
    },
  },
  approval: async ({ toolName }) => {
    // eve qualifies remote tools as <connection>__<tool>; recover the bare name.
    const sep = toolName.indexOf("__");
    const bare = sep === -1 ? toolName : toolName.slice(sep + 2);

    let readOnly: boolean | undefined;
    try {
      readOnly = (await readOnlyFlags()).get(bare);
    } catch {
      readOnly = undefined;
    }
    return readOnly === true ? "not-applicable" : "user-approval";
  },
});
