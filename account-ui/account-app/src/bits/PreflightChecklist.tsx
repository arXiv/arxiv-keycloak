import React from "react";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Avatar from "@mui/material/Avatar";
import NotificationIcon from '@mui/icons-material/NotificationImportant';
import RecommendIcon from '@mui/icons-material/Recommend';
import SecurityIcon from '@mui/icons-material/Security';

const NofiticationPoint: React.FC = () => (
    <ListItemAvatar>
    <Avatar>
        <NotificationIcon />
    </Avatar>
    </ListItemAvatar>);

const RecommendPoint = () => (
    <ListItemAvatar>
        <Avatar>
            <RecommendIcon />
        </Avatar>
    </ListItemAvatar>);

const SecurityPoint = () => (
    <ListItemAvatar>
        <Avatar>
            <SecurityIcon />
        </Avatar>
    </ListItemAvatar>);


const PreflightChecklist = () => {
    return (
        <Card sx={{ mb: 3, mt: 3, width: "90vw", maxWidth: "800px" }}>
            <CardContent>
                <Typography variant="h5" gutterBottom>
                    Preflight Checklist for New Submissions
                </Typography>
                <List>
                    <ListItem >
                        <NofiticationPoint />
                        <Typography variant="body1">
                            If your submission is written in TeX you must upload your source. PDFs produced from TeX may be declined.
                            <Link href="https://info.arxiv.org/help/faq/whytex.html" target="_blank"> Learn more about why TeX source is required.</Link>
                        </Typography>
                    </ListItem>
                    <ListItem>
                        <RecommendPoint />
                        <Typography variant="body1">
                            Experienced authors recommend putting all the files you will upload into one folder before starting.
                            <Link href="https://trevorcampbell.me/html/arxiv.html" target="_blank"> Read how one author prepares a clean upload.</Link>
                        </Typography>
                    </ListItem>
                    <ListItem>
                        <NofiticationPoint />
                        <Typography variant="body1">
                            Common errors that slow down announcement include missing files or references. Double check for missing content before uploading.
                            <Link href="https://info.arxiv.org/help/faq/mistakes.html" target="_blank"> Learn more about common mistakes.</Link>
                        </Typography>
                    </ListItem>
                    <ListItem>
                        <SecurityPoint />
                        <Typography variant="body1">
                            All announced content is archival and cannot be removed. Ensure that sensitive data is not part of your upload.
                            <Link href="https://www.ianhuston.net/2011/03/checklist-for-arxiv-submission/" target="_blank"> Read more tips from an arXiv author.</Link>
                        </Typography>
                    </ListItem>
                </List>
            </CardContent>
        </Card>
    );
};

export default PreflightChecklist;
