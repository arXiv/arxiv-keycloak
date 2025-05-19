import React from "react";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Avatar from "@mui/material/Avatar";
import NotificationIcon from '@mui/icons-material/NotificationImportant';
import RecommendIcon from '@mui/icons-material/Recommend';
import SecurityIcon from '@mui/icons-material/Security';
import {RuntimeProps} from "../RuntimeContext.tsx";
import CardWithTitle from "./CardWithTitle.tsx";

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


const PreflightChecklist: React.FC<{runtimeProps: RuntimeProps}> = ({runtimeProps}) => {
    const urls = runtimeProps.URLS;

    return (
        <CardWithTitle title={"Preflight Checklist for New Submissions"}>
            <List>
                <ListItem >
                    <NofiticationPoint />
                    <Typography variant="body1">
                        If your submission is written in TeX you must upload your source. PDFs produced from TeX may be declined.
                        <Link href={urls.whyTex} target="_blank"> Learn more about why TeX source is required.</Link>
                    </Typography>
                </ListItem>
                <ListItem>
                    <RecommendPoint />
                    <Typography variant="body1">
                        Experienced authors recommend putting all the files you will upload into one folder before starting.
                        <Link href={urls.cleanUpload} target="_blank"> Read how one author prepares a clean upload.</Link>
                    </Typography>
                </ListItem>
                <ListItem>
                    <NofiticationPoint />
                    <Typography variant="body1">
                        Common errors that slow down announcement include missing files or references. Double check for missing content before uploading.
                        <Link href={urls.commonMistakes} target="_blank"> Learn more about common mistakes.</Link>
                    </Typography>
                </ListItem>
                <ListItem>
                    <SecurityPoint />
                    <Typography variant="body1">
                        All announced content is archival and cannot be removed. Ensure that sensitive data is not part of your upload.
                        <Link href={urls.submissionChecklist} target="_blank"> Read more tips from an arXiv author.</Link>
                    </Typography>
                </ListItem>
            </List>
        </CardWithTitle>
    );
};

export default PreflightChecklist;
