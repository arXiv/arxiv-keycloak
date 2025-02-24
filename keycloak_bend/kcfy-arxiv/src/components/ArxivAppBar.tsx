import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import arXivLogo from '../assets/images/arxiv-logo-one-color-white.svg';


const ArxivAppBar = () => {

    return (
    <AppBar position="sticky" sx={{backgroundColor: '#B31B1B'}}>
        <Container maxWidth="xl">
            <Toolbar disableGutters>
                <img src={arXivLogo} width="85"
                     alt="arXiv Logo" aria-label="arxiv-logo" />
                <Box sx={{width: 20}}/>

                <Box sx={{flexGrow: 1}}/>
                <Box sx={{flexGrow: 0}}>
                </Box>
            </Toolbar>
        </Container>
    </AppBar>);
}

export default ArxivAppBar;
