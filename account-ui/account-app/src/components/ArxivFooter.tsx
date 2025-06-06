import React, {useContext} from 'react';
import {RuntimeContext} from "../RuntimeContext";
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import EmailIcon from "@mui/icons-material/Email";
import SubscriptionsIcon from "@mui/icons-material/Subscriptions";
import HoverLink from "../bits/HoverLink";
import SlackIcon from "../assets/SlackIcon";


const ArxivFooter: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const urls = runtimeProps.URLS;

    const emailTitle = (title: string) => (<Box sx={{
        display: "flex",
        alignItems: "center", // Align everything vertically
        px: 1,
    }}><EmailIcon sx={{fontSize: 12, mr: 1}}/>{title}</Box>);

    const subscribeTitle = (<Box sx={{
        display: "flex",
        alignItems: "center", // Align everything vertically
        px: 1,
    }}><SubscriptionsIcon sx={{fontSize: 12, mr: 1}}/>Subscribe</Box>);

    const slackTitle = (<Box sx={{
        display: "flex",
        alignItems: "center", // Align everything vertically
        px: 1,
    }}><SlackIcon style={{fill: "red", width: "16px", height: "16px"}}/>Slack</Box>);

    return (
        <Box
            component="footer"
            sx={{
                width: "100%",
                backgroundColor: "#eeeeee",
                mt: "auto",
                display: "flex",
            }}
        >
            <Box
                sx={{
                    width: "100%",
                    textAlign: "left",
                    display: "flex",
                    justifyContent: "space-between",
                    py: 2
                }}>

                <Box sx={{flex: 1}}/>

                <Box sx={{flex: 4,}}>
                    <HoverLink label={"About"} href={urls.about} />
                    <Box sx={{flex: 1}}/>
                    <HoverLink label={"Help"} href={urls.help} />
                </Box>

                <Box sx={{flex: 4}}>
                    <HoverLink label={emailTitle("Contact")} href={urls.contact}/>
                    <Box sx={{flex: 1}}/>
                    <HoverLink label={subscribeTitle} href={urls.subscribe}/>
                </Box>

                <Box sx={{flex: 4}}>
                    <HoverLink label={"Copyright"} href={urls.license}/>
                    <Box sx={{flex: 1}}/>
                    <HoverLink label={"Privacy Policy"} href={urls.privacyPolicy}/>
                </Box>
                <Box sx={{flex: 6}}>
                    <Box sx={{display: "flex", width: "100%"}}>
                        {/* Left side: Two HoverLinks stacked in a column */}
                        <Box sx={{flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-between"}}>
                            <HoverLink label={"Web Accessibility Assistance"} href={urls.webAccessibility}/>
                            <HoverLink label={"arXiv Operation Status"} href={urls.arxivStatus}/>
                        </Box>

                        {/* Right side: Status notifications */}
                        <Box sx={{flex: 1, display: "flex", flexDirection: "column", justifyContent: "center"}}>
                            <Typography sx={{fontSize: "9px", display: "inline", color: "black"}}>
                                {"Get status notifications via >"}
                            </Typography>
                            <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                                <HoverLink label={emailTitle("email")}
                                           href={urls.arxivStatusEmail}/>
                                <HoverLink label={slackTitle} href={urls.arxivSlack}/>
                            </Box>
                        </Box>
                    </Box>
                </Box>
                <Box sx={{flex: 1}}/>
            </Box>
        </Box>
    );
}

export default ArxivFooter;
