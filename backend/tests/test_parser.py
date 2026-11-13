from app.services.parser import FindingStreamParser, dedupe, parse_finding_line, sort_findings


def test_parses_valid_line():
    f = parse_finding_line('{"severity":"HIGH","line":3,"title":"x","suggestion":"fix"}')
    assert (f.severity, f.line, f.title, f.suggestion) == ("high", 3, "x", "fix")


def test_normalizes_bad_values():
    f = parse_finding_line('{"severity":"weird","line":"abc","title":"t"}')
    assert f.severity == "info" and f.line is None
    assert parse_finding_line('{"severity":"error","line":0,"title":"t"}').severity == "high"


def test_rejects_garbage():
    assert parse_finding_line("```json") is None
    assert parse_finding_line("Here are the findings:") is None
    assert parse_finding_line('{"title": ""}') is None
    assert parse_finding_line("{not json}") is None


def test_stream_parser_handles_split_chunks_and_fences():
    p = FindingStreamParser()
    chunks = [
        '```json\n{"severity":"low",',
        '"line":1,"title":"a"}\n{"sev',
        'erity":"info","title":"b"}',
    ]
    out = []
    for chunk in chunks:
        out += p.feed(chunk)
    assert [f.title for f in out] == ["a"]  # second object is still incomplete
    out += p.flush()
    assert [f.title for f in out] == ["a", "b"]


def test_summary_line_captured():
    p = FindingStreamParser()
    p.feed('{"summary": "looks risky"}\n')
    assert p.summary == "looks risky"


def test_dedupe_and_sort():
    a = parse_finding_line('{"severity":"low","line":5,"title":"Same  thing"}')
    b = parse_finding_line('{"severity":"low","line":5,"title":"same thing"}')
    c = parse_finding_line('{"severity":"critical","line":9,"title":"bad"}')
    assert len(dedupe([a, b, c])) == 2
    assert sort_findings([a, c])[0].severity == "critical"
