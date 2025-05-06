import React from "react";
import Card from "@mui/material/Card";
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
 */

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

export default CardWithTitle;
