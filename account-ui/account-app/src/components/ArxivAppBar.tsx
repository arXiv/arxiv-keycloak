import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
// import IconButton from '@mui/material/IconButton';
// import Menu from '@mui/material/Menu';
// import MenuItem from '@mui/material/MenuItem';
// import Typography from '@mui/material/Typography';
import { useNavigate } from "react-router-dom";
import {useContext} from "react"; // Ensure this is correct
import {RuntimeContext} from "../RuntimeContext";
import Link from "@mui/material/Link";
import {useMediaQuery, useTheme} from "@mui/material";


const pages = [
    {label: 'Account', link: '/user-account/'},
    {label: 'Endorsements', link: '/user-account/endorse'},
    {label: 'Ownership', link: '/user-account/ownership-request'},
    {label: 'Moderation', link: '/user-account/moderation'},
    {label: 'Administration', link: '/admin-console/'},
];

const ArxivAppBar = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const navigate = useNavigate(); // Hook for programmatic navigation
    const userText = `If you are logged in as ${user?.first_name} ${user?.last_name}.`;
    const accountName = `Account of ${user?.username}`
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm')); // Use the theme properly


    const in_or_out = user ? (
        <>
            <Tooltip title={userText}>
                <Button sx={{p: 0}} color={"inherit"} onClick={() => navigate("/user-account/")}>
                    {accountName}
                </Button>
            </Tooltip>

            <Tooltip title={userText}>
            <Button sx={{p: 0}} color={"inherit"} onClick={() => {window.location.replace("/logout")}}>
                Logout
            </Button>
        </Tooltip>
        </>
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
                    <Button
                        key={page.label}
                        onClick={() => handleCloseNavMenu(page)}
                        sx={{ my: 1, color: 'white', display: 'block',}}
                    >
                        {page.label}
                    </Button>
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
