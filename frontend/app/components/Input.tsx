interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement & HTMLTextAreaElement> {
  label: string;
  error?: string;
  multiline?: boolean;
  rows?: number;
  ref?: React.Ref<HTMLInputElement | HTMLTextAreaElement>;
}

export default function Input({
  label,
  name,
  error,
  type = "text",
  multiline = false,
  rows,
  ref,
  ...rest
}: InputProps) {
  const sharedClass =
    "bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-surface placeholder:text-muted focus:outline-none focus:border-white/30 transition-colors";
  const sharedProps = {
    id: name,
    name,
    "aria-describedby": error ? `${name}-error` : undefined,
    className: sharedClass,
  };

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={name} className="text-muted text-sm font-medium">
        {label}
      </label>
      {multiline ? (
        <textarea
          {...sharedProps}
          rows={rows}
          ref={ref as React.Ref<HTMLTextAreaElement>}
          {...rest}
        />
      ) : (
        <input
          {...sharedProps}
          type={type}
          ref={ref as React.Ref<HTMLInputElement>}
          {...rest}
        />
      )}
      {error && (
        <p id={`${name}-error`} className="text-red-400 text-xs">
          {error}
        </p>
      )}
    </div>
  );
}
