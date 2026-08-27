import type { ReactNode } from "react";

export function Section({
  id,
  index,
  eyebrow,
  title,
  intro,
  className = "",
  children,
}: {
  id?: string;
  index?: string;
  eyebrow: string;
  title: string;
  intro?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={`section ${className}`.trim()}>
      <header className="section-heading">
        <div className="section-kicker">
          {index ? <span aria-hidden="true">{index}</span> : null}
          <p>{eyebrow}</p>
        </div>
        <div>
          <h2>{title}</h2>
          {intro ? <p className="section-intro">{intro}</p> : null}
        </div>
      </header>
      {children}
    </section>
  );
}

export function Metric({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {note ? <small>{note}</small> : null}
    </div>
  );
}

export function MetricPair({
  label,
  before,
  after,
  unit = "",
}: {
  label: string;
  before: string | number;
  after: string | number;
  unit?: string;
}) {
  return (
    <div className="metric-pair">
      <span>{label}</span>
      <div>
        <b>{before}{unit}</b>
        <i aria-hidden="true">→</i>
        <strong>{after}{unit}</strong>
      </div>
    </div>
  );
}

export function TechnicalLabel({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "signal" | "verified" }) {
  return <span className={`technical-label ${tone}`}>{children}</span>;
}

export function FlowArrow({ label }: { label?: string }) {
  return (
    <span className="flow-arrow" aria-hidden="true">
      <i />
      {label ? <small>{label}</small> : null}
    </span>
  );
}
