// Single basketball glyph used as the wordmark accent — abstract, minimal,
// stroke-only. Stays consistent with Lucide visual weight.

type Props = React.SVGProps<SVGSVGElement>;

export function BasketballMark(props: Props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M2 12h20M12 2c-3.5 3-3.5 17 0 20M12 2c3.5 3 3.5 17 0 20"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        opacity="0.85"
      />
    </svg>
  );
}
