import { render, screen } from "@testing-library/react";
import { FindingCard, SeverityBadge, UsageMeter, usagePercent } from "./ui";

describe("usagePercent", () => {
  it("caps at 100 and handles zero limits", () => {
    expect(usagePercent(2, 5)).toBe(40);
    expect(usagePercent(9, 5)).toBe(100);
    expect(usagePercent(0, 0)).toBe(100);
  });
});

describe("UsageMeter", () => {
  it("shows usage against the plan limit", () => {
    render(<UsageMeter used={3} limit={5} plan="free" />);
    expect(screen.getByText("3 / 5 reviews this month")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "3");
  });

  it("flags a reached limit", () => {
    render(<UsageMeter used={5} limit={5} plan="free" />);
    expect(screen.getByText("5 / 5 reviews this month")).toHaveClass("text-red-600");
  });
});

describe("findings", () => {
  it("renders severity, line and suggestion", () => {
    render(
      <ul>
        <FindingCard
          finding={{ severity: "critical", line: 7, title: "eval on input", suggestion: "Use a parser" }}
        />
      </ul>,
    );
    expect(screen.getByText("critical")).toBeInTheDocument();
    expect(screen.getByText("line 7")).toBeInTheDocument();
    expect(screen.getByText("Use a parser")).toBeInTheDocument();
  });

  it("badge renders its label", () => {
    render(<SeverityBadge severity="low" />);
    expect(screen.getByText("low")).toBeInTheDocument();
  });
});
