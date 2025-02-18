import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import { useNavigate } from "react-router-dom";
import {useContext} from "react"; // Ensure this is correct
import {RuntimeContext} from "../RuntimeContext.tsx";

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
            <Button sx={{p: 0}} color={"inherit"} onClick={() => navigate("/user/logout")}>
                Logout
            </Button>
        </Tooltip>
        </>
    ) : (
        <Tooltip title="If you are not logged in.">
            <Button sx={{p: 0}} color={"inherit"} onClick={() => navigate("/user/login")}>
                Login
            </Button>
        </Tooltip>
    );
    return (
    <AppBar position="sticky" sx={{backgroundColor: '#B31B1B'}}>
        <Container maxWidth="xl">
            <Toolbar disableGutters>
                <img src="/user/static/images/arxiv-logo-one-color-white.svg?react" width="85"
                     alt="arXiv Logo" aria-label="arxiv-logo" />
                <Box sx={{flexGrow: 1}}/>
                <Box sx={{flexGrow: 0}}>
                    {in_or_out}
                </Box>
            </Toolbar>
        </Container>
    </AppBar>);
}

export default ArxivAppBar;
