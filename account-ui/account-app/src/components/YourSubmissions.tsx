import React, {useCallback, useEffect, useState} from "react";
import {
    DataGrid,
    GridColDef,
    GridRowParams,
    GridFilterModel,
    GridPaginationModel,
    GridRowSelectionModel, GridRenderCellParams
} from '@mui/x-data-grid';
import {RuntimeProps} from "../RuntimeContext.tsx";
import {paths as adminApi} from "../types/admin-api";
import DeleteIcon from "@mui/icons-material/Delete";
import UndoIcon from "@mui/icons-material/Undo";
// import Container from '@mui/material/Container'
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
import OpenIcon from "@mui/icons-material/OpenWith";
import EditIcon from "@mui/icons-material/Edit";


type SubmissionType = adminApi['/v1/submissions/{id}']['get']['responses']['200']['content']['application/json'];

type SubmissionsType = adminApi['/v1/submissions/']['get']['responses']['200']['content']['application/json'];


type SubmissionsStatusListType = adminApi['/v1/submissions/metadata/status-list']['get']['responses']['200']['content']['application/json'];
type SubmissionsStatusType = SubmissionsStatusListType[number];
type SubmissionStatusIdType = SubmissionsStatusType['id'];
type SubmissionStatusRecordType = Record<SubmissionStatusIdType, SubmissionsStatusType>;

const PAGE_SIZES = [5, 20, 100];

const YourSubmissions: React.FC<{ runtimeProps: RuntimeProps }> = ({runtimeProps}) => {
    const [submissions, setSubmissions] = useState<SubmissionsType>([]);
    const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
        page: 0, // starts at page 0
        pageSize: PAGE_SIZES[0],
    });
    const [filterModel, setFilterModel] = useState<GridFilterModel>(
        {
            items: [],
        }
    );

    const noSSRT:SubmissionStatusRecordType = {};
    const [submissinStatusList, setSubmissinStatusList] = useState<SubmissionStatusRecordType>(noSSRT);

    useEffect(() => {
        async function doSubmissionStatusList() {
            if (submissinStatusList === noSSRT) {
                try {
                    const response = await fetch(runtimeProps.UP_API_URL + "/submissions/metadata/status-list");
                    const data: SubmissionsStatusListType = await response.json();
                    const record: SubmissionStatusRecordType =
                        data.reduce((acc: SubmissionStatusRecordType,
                                     item) => {
                            acc[item.id] = item;
                            return acc;
                        }, {});
                    console.log(JSON.stringify(record));
                    setSubmissinStatusList(record);
                } catch (e) {
                    console.error("doSubmissionStatusList: " + e);
                }
            }
        }
        doSubmissionStatusList();

    }, [submissinStatusList, runtimeProps]);

    // Pagination state
    const [totalCount, setTotalCount] = useState<number>(0);

    const fetchSubmissions = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        if (!submissinStatusList)
            return;

        // const interestedIds = Object.values(submissinStatusList).filter(status => status.group === "current" || status.group === "processing");

        const start = paginationModel.page * paginationModel.pageSize;
        const end = start + paginationModel.pageSize;
        const query = new URLSearchParams();

        query.append("submitter_id", runtimeProps.currentUser.id);
        query.append("status", "current");
        query.append("status", "processing");
        query.append("_start", start.toString());
        query.append("_end", end.toString());

        filterModel.items.forEach((filter) => {
            console.log("filter " + JSON.stringify(filter));
            if (filter.value) {
                query.append("filter", JSON.stringify(filter));
            }
        });

        try {
            const response = await fetch(runtimeProps.UP_API_URL + `/submissions/?${query.toString()}`);
            const data: SubmissionType[] = await response.json();
            const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);
            setTotalCount(total);

            setSubmissions(
                data.map((submission) => ({
                    ...submission,
                    identifier: Number(submission.id),
                    expires: Number(submission.created),
                }))
            );
        } catch (err) {
            console.error("Error fetching submissions:", err);
        }
    }, [paginationModel, filterModel, submissinStatusList]);

    useEffect(() => {
        fetchSubmissions();
    }, [fetchSubmissions]);

    useEffect(() => {
        console.log("n subs " + submissions.length);
    }, [submissions]);

    const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);

    const handleDelete = () => {
        console.log("Deleting rows:", selectedRows);
        // Implement delete logic here
    };

    const handleUnsubmit = () => {
        console.log("Unsubmitting rows:", selectedRows);
        // Implement unsubmit logic here
    };

    /* [ cross | jref | new | rep | wdr ]*/
    const submittionTypeList: Record<string, string> = {
        "corss": "Cross",
        "jref": "Jref",
        "new": "New",
        "rep": "Replace",
        "wdr": "Withdrawn",
    };

    const columns: GridColDef<SubmissionType>[] = [
        {field: 'id', headerName: 'Identifier', width: 100,
            renderCell: (cell: GridRenderCellParams) => {
                return <Link href={`https://arxiv.org/submit/${cell.value}/resume`}>submit/{cell.value}</Link>;
            }
        },
        {
            field: 'type',
            headerName: 'Type',
            width: 80,
            renderCell: (cell: GridRenderCellParams) => {
                return <>{cell?.value ? submittionTypeList[cell.value] : "Unknown"}</>;
            }
        },
        {
            field: 'title',
            headerName: 'Title',
            flex: 1,
            sortable: false,
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 100,
            renderCell: (cell: GridRenderCellParams) => {
                return <>{submissinStatusList[cell?.value || "0"].name}</>;
            }
        },
        {
            field: 'expires',
            headerName: 'Expires',
            type: 'date',
            width: 110,
        },
    ];

    return (
        <Paper elevation={3} sx={{p: 3, mt: 4, width: "95%"}}>
            <Box display="flex" gap={2} justifyContent="flex-start" mb={1}>
                <Typography variant="h5" gutterBottom>
                    Your Submissions
                </Typography>
                <Box flexGrow={1}/>
                <Button
                    variant="contained"
                    color="error"
                    startIcon={<DeleteIcon/>}
                    onClick={handleDelete}
                    disabled={selectedRows.length === 0} // Disable when no rows are selected
                    aria-label="Delete Submissions"
                >
                    Delete
                </Button>

                <Button
                    variant="contained"
                    color="warning"
                    startIcon={<UndoIcon/>}
                    onClick={handleUnsubmit}
                    disabled={selectedRows.length === 0} // Disable when no rows are selected
                    aria-label="Unsubmit Submissions"
                >
                    Unsubmit
                </Button>
            </Box>

            <Box display="flex" gap={0} mb={0}>

                <DataGrid
                    filterModel={filterModel}
                    filterMode="server"
                    filterDebounceMs={1000}
                    onFilterModelChange={setFilterModel}

                    initialState={{pagination: {paginationModel: {pageSize: PAGE_SIZES[0]}}}}
                    pageSizeOptions={PAGE_SIZES}
                    paginationMode="server"
                    onPaginationModelChange={setPaginationModel}

                    columns={columns}
                    rows={submissions}
                    rowCount={totalCount}

                    checkboxSelection
                    disableRowSelectionOnClick
                    onRowSelectionModelChange={(newSelection) => setSelectedRows(newSelection)}

                    getDetailPanelContent={({row}: GridRowParams<SubmissionType>) => (
                        <Box sx={{padding: 2, backgroundColor: "#f9f9f9"}}>
                            <Typography variant="subtitle1" fontWeight="bold">
                                Abstract:
                            </Typography>
                            <Typography variant="body2">{row.abstract}</Typography>
                        </Box>
                    )}

                />
            </Box>

            <Box display="flex" gap={2} justifyContent="flex-start" mt={1}>
                <Button
                    disabled={runtimeProps.currentUser === null}
                    variant="contained"
                    startIcon={<OpenIcon/>}
                    href={runtimeProps.URLS.submissionManagementURL}
                    sx={{
                        color: "white", // Default text color
                        "&:hover": {
                            color: "white", // Keep text white on hover
                        },
                    }}
                    aria-label="Open Submissions"
                >
                    Open Submission management
                </Button>
                <Box flexGrow={1}/>

                            <Button
                    disabled={runtimeProps.currentUser === null}
                    variant="contained"
                    startIcon={<EditIcon/>}
                    href={runtimeProps.URLS.newSubmissionURL}
                    sx={{
                        color: "white", // Default text color
                        "&:hover": {
                            color: "white", // Keep text white on hover
                        },
                    }}
                    aria-label="Start New Submissions"
                >
                    Start New Submission
                </Button>
            </Box>
        </Paper>
    );
}

export default YourSubmissions;
