export interface SSEEvent {
  event: string;
  data: any;
}

/** Incremental Server-Sent Events parser: feed it arbitrary text chunks. */
export class SSEParser {
  private buffer = "";

  feed(chunk: string): SSEEvent[] {
    this.buffer += chunk.replace(/\r\n/g, "\n");
    const blocks = this.buffer.split("\n\n");
    this.buffer = blocks.pop() ?? "";
    const events: SSEEvent[] = [];
    for (const block of blocks) {
      let event = "message";
      const data: string[] = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
      }
      if (!data.length) continue;
      try {
        events.push({ event, data: JSON.parse(data.join("\n")) });
      } catch {
        // ignore malformed frames
      }
    }
    return events;
  }
}
