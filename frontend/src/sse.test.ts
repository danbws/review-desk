import { SSEParser } from "./sse";

describe("SSEParser", () => {
  it("parses complete events", () => {
    const p = new SSEParser();
    const out = p.feed('event: token\ndata: {"text":"hi"}\n\nevent: done\ndata: {"id":1}\n\n');
    expect(out).toEqual([
      { event: "token", data: { text: "hi" } },
      { event: "done", data: { id: 1 } },
    ]);
  });

  it("handles events split across chunks and CRLF", () => {
    const p = new SSEParser();
    expect(p.feed('event: draft\r\ndata: {"a"')).toEqual([]);
    expect(p.feed(":1}\r\n\r\n")).toEqual([{ event: "draft", data: { a: 1 } }]);
  });

  it("skips malformed frames without throwing", () => {
    const p = new SSEParser();
    expect(p.feed("event: x\ndata: {oops\n\nevent: ok\ndata: {}\n\n")).toEqual([
      { event: "ok", data: {} },
    ]);
  });
});
