interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  ref?: React.Ref<HTMLInputElement>;
}

export default function Input({
  label,
  name,
  error,
  type = "text",
  ref,
  ...rest
}: InputProps) {
  const sharedClass =
    "bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-surface placeholder:text-muted focus:outline-none focus:border-white/30 transition-colors";

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={name} className="text-muted text-sm font-medium">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        aria-describedby={error ? `${name}-error` : undefined}
        className={sharedClass}
        ref={ref}
        {...rest}
      />
      {error && (
        <p id={`${name}-error`} className="text-red-400 text-xs">
          {error}
        </p>
      )}
    </div>
  );
}
