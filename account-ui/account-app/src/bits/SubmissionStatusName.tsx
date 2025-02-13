import React from 'react';
import {Typography, TypographyProps} from "@mui/material";

interface SubmissionStatusFieldProps extends TypographyProps {
    status: number;
}

export const submissionStatusOptions = [
    {"id": 0, "name": "Working" },
    {"id": 1, "name": "Submitted"},
    {"id": 2, "name": "On hold"},
    {"id": 3, "name": "Unused"},
    {"id": 4, "name": "Next"},
    {"id": 5, "name": "Processing"},
    {"id": 6, "name": "Needs_email"},
    {"id": 7, "name": "Published"},
    {"id": 8, "name": "Processing(submitting)"},
    {"id": 9, "name": "Removed"},
    {"id": 10, "name": "User deleted"},
    {"id": 19, "name": "Error state"},
    {"id": 20, "name": 'Deleted(working)'},
    {"id": 22, "name": 'Deleted(on hold)'},
    {"id": 25, "name": 'Deleted(processing)'},
    {"id": 27, "name": 'Deleted(published)'},
    {"id": 29, "name": "Deleted(removed)"},
    {"id": 30, "name": 'Deleted(user deleted)'},
];

const SubmissionStatusName: React.FC<SubmissionStatusFieldProps> = ({status, ...props}) => {
    return (
        <Typography {...props} >
            {submissionStatusOptions.filter((elem) => elem.id === status)[0].name}
        </Typography>
    );
};

export default SubmissionStatusName;
