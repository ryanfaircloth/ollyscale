import { type ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center p-5 text-center">
      <img
        src="/logo.svg"
        alt=""
        style={{
          height: "48px",
          width: "48px",
          opacity: 0.3,
          marginBottom: "1rem",
        }}
      />
      <h5 className="mb-2">{title}</h5>
      {description && <p className="text-muted mb-3">{description}</p>}
      {action && <div>{action}</div>}
    </div>
  );
}
