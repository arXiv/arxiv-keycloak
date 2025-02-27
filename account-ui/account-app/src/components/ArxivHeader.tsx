import React, {useContext, useEffect, useState} from 'react';
import {RuntimeContext} from "../RuntimeContext";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Button  from "@mui/material/Button";
import {
    useTheme, useMediaQuery,
} from '@mui/material';
import ArxivAppBar from "./ArxivAppBar.tsx";



const ArxivBanner = () => {
    const runtimeProps = useContext(RuntimeContext);
    const [ackText, setAckText] = useState<string>("We gratefully acknowledge support from the Simons Foundation, " +
        "<a href=\"https://info.arxiv.org/about/ourmembers.html\" color=\"inherit\"> " +
        "member institutions </a>, and all contributors.");

    useEffect(() => {
        // Load the external script dynamically
        const script = document.createElement("script");
        script.src = "/static/js/member_acknowledgement.js";
        script.async = true;
        script.onload = () => {
            // Wait for script execution, then fetch the text
            setTimeout(() => {
                const supportElem = document.getElementById("support-ack-url");
                if (supportElem) {
                    setAckText(supportElem.innerHTML);
                }
            }, 500); // Give it some time to execute
        };

        document.body.appendChild(script);

        return () => {
            document.body.removeChild(script);
        };
    }, []);


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
                <img src="/user-account/static/images/cornell-reduced-white-SMALL.svg" alt="Cornell logo"
                     width="180"/>
            </Link>
        </Box>

        <Box sx={{flex: 1, display: "flex", justifyContent: "center", alignItems: "center"}}>
        </Box>

        <Box
            sx={{
                flex: 3,
                display: "flex",
                justifyContent: "space-between", // Text on left, Button on right
                alignItems: "center", // Align everything vertically
                px: 2, // Add some padding
            }}
        >

            <Typography variant={"caption"} sx={{textAlign: "right", flex: 1, fontSize: "12px", fontWeight: "bold"}}
                        dangerouslySetInnerHTML={{ __html: ackText }}
            />

            {/* Right-aligned button */}
            <Button
                variant={"outlined"}
                href={runtimeProps.URLS.donate}
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
