import SvgIcon, { SvgIconProps } from '@mui/material/SvgIcon';

const NonAuthorIcon = (props: SvgIconProps) => (
    <SvgIcon {...props}>
        {/* Head */}
        <circle cx="12" cy="7" r="4" fill="#757575" />

        {/* Shoulders */}
        <path d="M4 20c0-3.3 2.7-6 6-6h4c3.3 0 6 2.7 6 6v1H4v-1z"  fill="#757575" />

        {/* Left Hand */}
        <path d="M7 17c-.5 0-1 .4-1 1v.5c0 .4.3.7.7.7h2.1c.6 0 .9-.7.5-1.1l-1.2-1c-.2-.2-.5-.3-.8-.3z" fill="#aaa" />

        {/* Right Hand */}
        <path d="M17 17c.5 0 1 .4 1 1v.5c0 .4-.3.7-.7.7h-2.1c-.6 0-.9-.7-.5-1.1l1.2-1c.2-.2.5-.3.8-.3z" fill="#aaa" />

        {/* Paper / Envelope */}
        <rect
            x="8.4"        // original was x=9; shift left by 0.6
            y="14.8"       // original was y=15.2; shift up by 0.4
            width="7.2"    // 6 * 1.2
            height="4.2"   // 3.5 * 1.2
            rx="0.4"
            fill="#ffffff"
            stroke="#1976d2"
            strokeWidth="0.8"
        />
        <path
            d="M8.4 14.8l3.6 2.4 3.6-2.4"
            stroke="#000000"
            strokeWidth="0.8"
            fill="none"
        />
    </SvgIcon>
);

export default NonAuthorIcon;
