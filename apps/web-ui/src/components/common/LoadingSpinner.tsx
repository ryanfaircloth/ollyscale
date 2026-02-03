interface LoadingSpinnerProps {
  message?: string;
}

export function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center p-5">
      <img
        src="/logo.svg"
        alt="Loading..."
        style={{
          height: "48px",
          width: "48px",
          animation: "spin 1.5s linear infinite",
        }}
      />
      {message && <p className="text-muted mt-3">{message}</p>}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
