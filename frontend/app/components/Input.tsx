interface InputProps {
  label: string;
  name: string;
  value: string;
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => void;
  placeholder?: string;
  type?: string;
  error?: string;
  multiline?: boolean;
  rows?: number;
}

export default function Input({
  label,
  name,
  value,
  onChange,
  placeholder,
  type = "text",
  error,
  multiline = false,
  rows = 3,
}: InputProps) {
  const sharedClass =
    "bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-surface placeholder:text-muted focus:outline-none focus:border-white/30 transition-colors";

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={name} className="text-muted text-sm font-medium">
        {label}
      </label>
      {multiline ? (
        <textarea
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          rows={rows}
          className={`${sharedClass} resize-none`}
        />
      ) : (
        <input
          id={name}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={sharedClass}
        />
      )}
      {error && <p className="text-red-400 text-xs">{error}</p>}
    </div>
  );
}
