import React, {useContext} from 'react';
import {RuntimeContext} from "../RuntimeContext";
import {
    Typography,
    Box,
    Link,
    Button, useTheme, useMediaQuery,
} from '@mui/material';
import ArxivAppBar from "./ArxivAppBar.tsx";

const ArxivBanner = () => {
    const runtimeProps = useContext(RuntimeContext);
    return (
    <Box sx={{
        width: "100vw",
        display: "flex",
        backgroundColor: "#222222",
        color: "white",
        textAlign: "center",
        py: 1,
    }}>
        <Box
            sx={{flex: 2, display: "flex", justifyContent: "left", padding: "0em 0.5em", alignItems: "center"}}>
            <Link href={runtimeProps.UNIVERSITY} className="level-item">
                <img src="/user/static/images/cornell-reduced-white-SMALL.svg" alt="Cornell logo"
                     width="180"/>
            </Link>
        </Box>

        <Box sx={{flex: 1, display: "flex", justifyContent: "center", alignItems: "center"}}>
        </Box>

        <Box
            sx={{
                flex: 2,
                display: "flex",
                justifyContent: "space-between", // Text on left, Button on right
                alignItems: "center", // Align everything vertically
                px: 2, // Add some padding
            }}
        >
            {/* Left-aligned text */}
            <Typography variant={"caption"} sx={{textAlign: "right", flex: 1, fontSize: "12px", fontWeight: "bold"}}>
                We gratefully acknowledge support from the Simons Foundation,{" "}
                <Link href="https://info.arxiv.org/about/ourmembers.html" color="inherit">
                    member institutions
                </Link>
                , and all contributors.
            </Typography>

            {/* Right-aligned button */}
            <Button
                variant={"outlined"}
                href="https://info.arxiv.org/about/donate.html"
                color="inherit"
                sx={{
                    fontSize: "12px", padding: "2px 4px", minWidth: "auto",
                    whiteSpace: "nowrap", backgroundColor: "white", color: "black",
                }}
            >
                Donate
            </Button>
        </Box>
    </Box>);
}

const ArxivHeader: React.FC = () => {
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down("sm")); // 'sm' is ~600px

    return (
        <Box sx={{display: 'flex', flexDirection: 'column'}}>
            {/* Attribution Banner */}
            {!isSmallScreen && <ArxivBanner />}
            <ArxivAppBar />
        </Box>
    );
}

export default ArxivHeader;
