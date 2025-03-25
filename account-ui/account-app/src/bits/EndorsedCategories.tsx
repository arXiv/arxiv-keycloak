import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { styled } from '@mui/material/styles';

import {RuntimeProps, } from "../RuntimeContext.tsx";
import { paths as adminApi } from "../types/admin-api";
import PublicUser from "./PublicUser.tsx";

type EndorsementListType = adminApi["/v1/endorsements/"]["get"]['responses']["200"]['content']['application/json'];
type EndorsementType = adminApi["/v1/endorsements/{id}"]["get"]['responses']["200"]['content']['application/json'];

type EndorsedCategoriesProps = {
    runtimeProps: RuntimeProps,
    endorsements: EndorsementListType;
};

type Grouped = Record<string, number[]>;

const groupByArchiveSubject = (endorsements: EndorsementListType): Grouped => {
    const grouped: Grouped = {};

    endorsements.forEach((endorsement: EndorsementType) => {
        const key: string = `${endorsement.archive}.${endorsement.subject_class}`;
        if (!grouped[key]) {
            grouped[key] = [];
        }
        if (endorsement.endorser_id)
            grouped[key].push(endorsement.endorser_id);
    });

    return grouped;
};


const CompactAccordion = styled(Accordion)(() => ({
    display: 'inline-block',
    verticalAlign: 'top',
    margin: 0,
    padding: 0,
    flexGrow: 0,
    boxShadow: 'none',
    backgroundColor: "transparent",
    width: 'fit-content',
    '&::before': {
        display: 'none', // Remove default divider line
    },
    border: '1px solid gray',
}));

const CompactAccordionSummary = styled(AccordionSummary)(({ theme }) => ({
    minHeight: 'unset !important',
    padding: theme.spacing(0.5, 1),
    width: 'fit-content',
    height: 24,
    '& .MuiAccordionSummary-content': {
        margin: 0,
        flexGrow: 0,
        width: 'fit-content',
    },
    '&.Mui-expanded': {
        minHeight: 24,
        flexGrow: 0,
        height: 24,
},
}));

const CompactAccordionDetails = styled(AccordionDetails)(({ theme }) => ({
    padding: theme.spacing(0.5, 1),
    flexGrow: 0,
    width: 'fit-content',
}));

const EndorsedCategories: React.FC<EndorsedCategoriesProps> = ({ runtimeProps, endorsements }) => {
    const grouped = groupByArchiveSubject(endorsements);

    return (
        <Box display="flex" flexWrap="wrap" gap={1} alignItems="flex-start">
            {Object.entries(grouped).map(([key, endorserId]) => (
                <CompactAccordion  key={key} >
                    <CompactAccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="subtitle2">{key}</Typography>
                    </CompactAccordionSummary>
                    <CompactAccordionDetails>
                            {endorserId.map((id) => (
                                    <PublicUser key={id} user_id={id} runtimeProps={runtimeProps} />
                            ))}
                    </CompactAccordionDetails>
                </CompactAccordion>
            ))}
        </Box>
    );
};

export default EndorsedCategories;
