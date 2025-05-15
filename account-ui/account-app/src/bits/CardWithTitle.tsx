import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

interface CardWithTitleProps {
    title: string;
    children: React.ReactNode;
}
/*
const CardWithTitle: React.FC<CardWithTitleProps> = ({ title, children }) => (
    <Card
        elevation={1}
    >
        <CardHeader title={title} />
        {children}
    </Card>
);

const CardWithTitle: React.FC<CardWithTitleProps> = ({ title, children }) => (
    <Box>
        <Box sx={{ mb: "-12px", ml: 2 }}>
            <Typography
                variant="h6"
                sx={{
                    color: "black",
                    backgroundColor: "white",
                    px: 1,
                    display: "inline-block",
                }}
            >
                {title}
            </Typography>
        </Box>

        <Card elevation={2} >
            <Box sx={{ pt: 1 }}>
                {children}
            </Box>
    </Card>
    </Box>
);
 */


interface CardWithTitleProps {
    title: string;
    children: React.ReactNode;
    borderColor?: string;
    titleBgColor?: string;
    titleColor?: string;
    textColor?: string;
}


const CardWithTitle: React.FC<CardWithTitleProps> = ({
                                                         title,
                                                         children,
                                                         borderColor = "#BBB",
                                                         titleBgColor = "white",
                                                         titleColor = "#333",
                                                         textColor = "black",
                                                     }) => (
    <Box sx={{ position: "relative", mt: 2 }}>
        {/* Title positioned on top of border */}
        <Box
            sx={{
                position: "absolute",
                top: "-12px",
                left: "16px",
                zIndex: 2,  // Higher z-index to ensure visibility
                backgroundColor: titleBgColor,
                px: 1,
            }}
        >
            <Typography
                variant="h5"
                sx={{
                    color: titleColor,
                    fontWeight: 500,
                }}
            >
                {title}
            </Typography>
        </Box>

        {/* Content box with border */}
        <Box
            sx={{
                border: `1px solid ${borderColor}`,
                borderRadius: "6px",
                p: 2,
                pt: 2.5,
                position: "relative",  // Ensure content is positioned properly
                boxShadow: "0px 3px 6px rgba(0, 0, 0, 0.16)",
            }}
        >
            <Typography sx={{color: textColor}}>
                {children}
            </Typography>
        </Box>
    </Box>
);

export default CardWithTitle;
