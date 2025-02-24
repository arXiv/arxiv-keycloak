import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Container from '@mui/material/Container';
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


const pages = [
    {label: 'Account', link: '/user/'},
    {label: 'Endorsements', link: '/user/endorsements'},
    {label: 'Ownership', link: '/user/ownership-request'},
    {label: 'Moderation', link: '/user/moderation'},
    {label: 'Administration', link: '/admin-console/'},
];

const ArxivAppBar = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const navigate = useNavigate(); // Hook for programmatic navigation
    const userText = `If you are logged in as ${user?.first_name} ${user?.last_name}.`;
    const accountName = `Account of ${user?.username}`

    const in_or_out = user ? (
        <>
            <Tooltip title={userText}>
                <Button sx={{p: 0}} color={"inherit"} onClick={() => navigate("/user/")}>
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
        if (page.link.startsWith('/user'))
            navigate(page.link);
        else
            window.location.href = page.link;
    };

    return (
    <AppBar position="sticky" sx={{backgroundColor: '#B31B1B'}}>
        <Container maxWidth="xl">
            <Toolbar disableGutters>
                <img src="/user/static/images/arxiv-logo-one-color-white.svg?react" width="85"
                     alt="arXiv Logo" aria-label="arxiv-logo" />
                <Box sx={{width: 20}}/>
                <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
                    {pages.map((page) => (
                        <Button
                            key={page.label}
                            onClick={() => handleCloseNavMenu(page)}
                            sx={{ my: 2, color: 'white', display: 'block' }}
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
        </Container>
    </AppBar>);
}

export default ArxivAppBar;
