import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import ChangePasswordIcon from '@mui/icons-material/Password';
import ChangeEmailIcon from '@mui/icons-material/AlternateEmailOutlined';
import ResendVerificationIcon from '@mui/icons-material/Send';
import LogoutIcon from '@mui/icons-material/Logout';
import Typography from '@mui/material/Typography';
import { useNavigate } from "react-router-dom";
import {useContext, useState} from "react"; // Ensure this is correct
import {RuntimeContext} from "../RuntimeContext";
import Link from "@mui/material/Link";
import {useMediaQuery, useTheme} from "@mui/material";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from '@mui/material/ListItemIcon';
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";

const ownershipOptions = [
    { label: "Your Articles", link: "/user-account/owned-documents" },
    { label: "Claim Ownership", link: "/user-account/claim-paper-ownership" },
    { label: "Request Ownership", link: "/user-account/request-document-ownership" },
];


const ArxivAppBar = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const navigate = useNavigate(); // Hook for programmatic navigation
    const fullName = `${user?.first_name} ${user?.last_name}`;
    // const userText = `If you are logged in as ${user?.first_name} ${user?.last_name}.`;
    // const accountName = `Account of ${user?.first_name}`
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm')); // Use the theme properly

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [accountMenuAnchorEl, setAccountMenuAnchorEL] = React.useState<null | HTMLElement>(null);

    const handleOwnershipClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleOwnershipClose = (link: string | null) => {
        setAnchorEl(null);
        if (link) navigate(link);
    };

    const email_verified = user === undefined || user === null || user.email_verified === true;

    const accountMenuItems = [
        { id: "change_user_info", name: "Change User Information", icon: <AccountCircleIcon />, disabled: false, navigate: "/user-account/update-profile" },
        { id: "change_password", name: "Change Password", icon: <ChangePasswordIcon />, disabled: false, navigate: "/user-account/change-password" },
        { id: "change_email", name: "Change Email", icon: <ChangeEmailIcon />, disabled: false, navigate: "/user-account/change-email"},
        { id: "resend_verification", name: "Resend Email Verification", icon: <ResendVerificationIcon />, disabled: email_verified, navigate: "/user-account/change-email" },
        { id: "logout", name: "Logout", icon: <LogoutIcon />, disabled: !user, navigate: "/logout" },
    ];

    const handleAccountMenu = (event: React.MouseEvent<HTMLElement>) => {
        setAccountMenuAnchorEL(event.currentTarget);
    };

    const handleAccountMenuClose = (action: string | null) => {
        if (action) {
            const selected: typeof accountMenuItems = accountMenuItems.filter((item) => item.id === action);
            if (selected.length > 0) {
                const accountAction = selected[0];
                if (accountAction.navigate.startsWith("/user-account")) {
                    navigate(accountAction.navigate);
                }
                else {
                    window.location.replace(accountAction.navigate);
                }
            }
        }
        setAccountMenuAnchorEL(null);
    };

    const commonPages = [
        {label: 'Account', link: '/user-account/'},
        {label: 'Articles', link: '/user-account/articles'},
        {label: 'Endorsements', link: '/user-account/endorse'},
    ];

    const modPages = runtimeProps.isMod ? [{label: 'Moderation', link: '/user-account/moderation'}] : [];
    const adminPages = runtimeProps.isAdmin ? [{label: 'Administration', link: '/admin-console/'}] : [];
    const pages = commonPages.concat(modPages, adminPages);


    const in_or_out = user ? (
            <div>
                <IconButton
                    size="large"
                    aria-label="account of current user"
                    aria-controls="menu-appbar"
                    aria-haspopup="true"
                    onClick={handleAccountMenu}
                    color="inherit"
                    sx={{
                        "&:focus": { outline: "none" },
                        "&:hover": { backgroundColor: "transparent" },
                        "&:active": { backgroundColor: "transparent" },
                    }}
                >
                    <Box display="flex" alignItems="center" gap={1}>
                        <AccountCircleIcon />
                        <Typography variant="body1">{fullName}</Typography>
                    </Box>
                </IconButton>
                <Menu
                    id="menu-appbar"
                    anchorEl={accountMenuAnchorEl}
                    anchorOrigin={{
                        vertical: 'bottom',
                        horizontal: 'right',
                    }}
                    keepMounted
                    transformOrigin={{
                        vertical: 'top',
                        horizontal: 'right',
                    }}
                    open={Boolean(accountMenuAnchorEl)}
                    onClose={() => handleAccountMenuClose(null)}
                >
                    {accountMenuItems.map((item) => (
                        <MenuItem key={item.id} onClick={() => handleAccountMenuClose(item.id)} disabled={item.disabled}>
                            <ListItemIcon children={item.icon} />
                            {item.name}
                        </MenuItem>

                    ))}
                </Menu>
            </div>
    ) : (
        <Tooltip title="If you are not logged in.">
            <Button sx={{p: 0}} color={"inherit"} onClick={() => {window.location.replace("/login")}}>
                Login
            </Button>
        </Tooltip>
    );

    const handleCloseNavMenu = (page: typeof pages[0]) => {
        if (page.link.startsWith('/user-account'))
            navigate(page.link);
        else
            window.location.href = page.link;
    };

    return (
        <AppBar position="sticky" sx={{backgroundColor: '#B31B1B'}}>
            <Toolbar disableGutters>
                <Box sx={{width: isSmallScreen ? 4 : 16}}/>

                <Link href={runtimeProps.URLS.arXiv}>
                    <img src="/user-account/static/images/arxiv-logo-one-color-white.svg?react" width="85"
                         alt="arXiv Logo" aria-label="arxiv-logo" />
                </Link>
                <Box sx={{width: isSmallScreen ? 0 : 20}}/>
                <Box sx={{
                    flexGrow: 0,
                    display:  isSmallScreen ? 'grid' : 'flex',
                    gap: isSmallScreen ? 1 : 0,
                    gridTemplateColumns: isSmallScreen ? 'repeat(3, 1fr)' : 'auto',
                    m: 0, p: 0, width: isSmallScreen ? "20rem" : null,
                }}>
                    {pages.map((page) => (
                        page.link === "/user-account/articles" ? (
                            <Box key={page.label} sx={{ display: "flex", alignItems: "center" }}>
                                <Button
                                    color="inherit"
                                    sx={{ my: 1, color: "white",
                                        "&:focus": { outline: "none" },
                                        "&:hover": { backgroundColor: "transparent" },
                                        "&:active": { backgroundColor: "transparent" },
                                    }}
                                    onClick={handleOwnershipClick}
                                    endIcon={<ArrowDropDownIcon />}
                                >
                                    {page.label}
                                </Button>
                                <Menu
                                    anchorEl={anchorEl}
                                    open={Boolean(anchorEl)}
                                    onClose={() => handleOwnershipClose(null)}
                                >
                                    {ownershipOptions.map((option) => (
                                        <MenuItem key={option.label} onClick={() => handleOwnershipClose(option.link)}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Menu>
                            </Box>
                        ) :(
                        <Button
                            key={page.label}
                            onClick={() => handleCloseNavMenu(page)}
                            sx={{ my: 1, color: 'white', display: 'block',}}
                        >
                            {page.label}
                        </Button>
                        )
                    ))}
                </Box>

                <Box sx={{flexGrow: 1}}/>
                <Box sx={{flexGrow: 0}}>
                    {in_or_out}
                </Box>
            </Toolbar>
        </AppBar>);
}

export default ArxivAppBar;
