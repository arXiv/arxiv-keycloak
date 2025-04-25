import React from 'react';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import { useLocation, Link as RouterLink } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';

const breadcrumbNameMap: Record<string, string> = {
    'user-account': 'Account',
    'login': 'Login',
    'logout': 'Logout',
    'register': 'Register',
    'request-document-ownership': 'Request Document Ownership',
    'change-author-status': 'Change Author Status',
    'update-profile': 'Update Profile',
    'change-password': 'Change Password',
    'change-email': 'Change Email',
    'endorse': 'Enter Endorsement Code',
    'owned-documents': 'Your Documents',
    'claim-paper-ownership': 'Claim Paper Ownership',
    'reset-password': 'Reset Password',
};

const RouteBreadcrumbs: React.FC = () => {
    const location = useLocation();
    const pathnames = location.pathname.split('/').filter((x) => x);

    return (
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb" sx={{ px: 2, py: 1 }}>
            <Link
                component={RouterLink}
                to="/"
                underline="hover"
                color="inherit"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
            >
                <HomeIcon sx={{color: "white"}} />
                <Typography component="div" color={"white"}>
                    Home
                </Typography>
            </Link>

            {pathnames.map((value, index) => {
                const to = `/${pathnames.slice(0, index + 1).join('/')}`;
                const isLast = index === pathnames.length - 1;
                const label = breadcrumbNameMap[value] || value;

                return isLast ? (
                    <Typography color="white" key={to}>
                        {label}
                    </Typography>
                ) : (
                    <Link
                        component={RouterLink}
                        to={to}
                        underline="hover"
                        color="white"
                        key={to}
                    >
                        {label}
                    </Link>
                );
            })}
        </Breadcrumbs>
    );
};

export default RouteBreadcrumbs;
