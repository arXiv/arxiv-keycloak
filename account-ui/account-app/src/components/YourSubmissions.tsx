import React, {useCallback, useRef} from "react";
import {RuntimeProps} from "../RuntimeContext.tsx";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import EditIcon from "@mui/icons-material/Edit";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import SubmissionDatagrid from "./SubmissionDatagrid.tsx";


const YourSubmissions: React.FC<{ runtimeProps: RuntimeProps, vetoed: boolean }> = ({runtimeProps, vetoed}) => {
    const workingDatagridRef = useRef<{ refresh: () => void }>(null);
    const currentDatagridRef = useRef<{ refresh: () => void }>(null);

    const handleRefreshAll = useCallback(() => {
        workingDatagridRef.current?.refresh();
        currentDatagridRef.current?.refresh();
    }, []);

    return (
        <CardWithTitle title={"Your Submissions"}>
            <SubmissionDatagrid
                ref={workingDatagridRef}
                runtimeProps={runtimeProps}
                submissionStatusGroup={"working"}
                onDataChange={handleRefreshAll}
            />

            <Box display="flex" gap={1} justifyContent="flex-start" mt={1}>
                <Box flexGrow={1}> {/* vetoedOrNot */} </Box>
                <Button
                    disabled={vetoed || runtimeProps.currentUser === null}
                    variant="contained"
                    startIcon={<EditIcon/>}
                    href={runtimeProps.URLS.newSubmissionURL}
                    sx={{
                        minWidth: "fit-content",
                        color: "white",
                        "&:hover": {
                            color: "white",
                        },
                    }}
                    aria-label="Start New Submissions"
                >
                    Start New Submission
                </Button>
            </Box>

            <SubmissionDatagrid
                ref={currentDatagridRef}
                runtimeProps={runtimeProps}
                submissionStatusGroup={"current"}
                onDataChange={handleRefreshAll}
            />

        </CardWithTitle>
    );
}

export default YourSubmissions;
