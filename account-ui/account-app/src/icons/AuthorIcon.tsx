import SvgIcon, { SvgIconProps } from '@mui/material/SvgIcon';

const AuthorIcon = (props: SvgIconProps) => (
    <SvgIcon {...props}>
            <circle cx="12" cy="8" r="4" fill="#1980ff"/>
            <path d="M4 20c0-3.3 2.7-6 6-6h4c3.3 0 6 2.7 6 6v1H4v-1z" fill="#1980ff"/>
            <circle cx="18" cy="6" r="4" fill="#4caf50"/>
            <path d="M16.5 6l1.2 1.8 2.3-2.8" stroke="#fff" stroke-width="2" fill="none"/>
    </SvgIcon>
);

export default AuthorIcon;
