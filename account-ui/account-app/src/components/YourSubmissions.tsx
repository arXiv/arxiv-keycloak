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
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
import EditIcon from "@mui/icons-material/Edit";
import DatagridPaginationMaker from "../bits/DataGridPagination.tsx";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import {
    ADMIN_SUBMISSIONS_METADATA_STATUS_LIST_URL,
    ADMIN_SUBMISSIONS_URL,
    ADMIN_SUBMISSIONS_ID_URL
} from "../types/admin-url.ts";


type SubmissionType = adminApi[typeof ADMIN_SUBMISSIONS_ID_URL]['get']['responses']['200']['content']['application/json'];
type SubmissionsType = adminApi[typeof ADMIN_SUBMISSIONS_URL]['get']['responses']['200']['content']['application/json'];

type SubmissionsStatusListType = adminApi[typeof ADMIN_SUBMISSIONS_METADATA_STATUS_LIST_URL]['get']['responses']['200']['content']['application/json'];
type SubmissionsStatusType = SubmissionsStatusListType[number];
type SubmissionStatusIdType = SubmissionsStatusType['id'];
type SubmissionStatusRecordType = Record<SubmissionStatusIdType, SubmissionsStatusType>;

const PAGE_SIZES = [5, 20, 100];

const YourSubmissions: React.FC<{ runtimeProps: RuntimeProps, vetoed: boolean }> = ({runtimeProps, vetoed}) => {
    const [isLoading, setIsLoading] = useState(false);
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
                    setIsLoading(true);
                    const getSubmissionStatusList = runtimeProps.adminFetcher.path(ADMIN_SUBMISSIONS_METADATA_STATUS_LIST_URL).method('get').create();
                    const response = await getSubmissionStatusList({});
                    const data: SubmissionsStatusListType = response.data;
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
                finally {
                    setIsLoading(false);
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

        try {
            setIsLoading(true);
            const getSubmissions = runtimeProps.adminFetcher.path(ADMIN_SUBMISSIONS_URL).method('get').create();
            const response = await getSubmissions({
                submitter_id: Number(runtimeProps.currentUser.id),
                submission_status_group: "current",
                _start: start,
                _end: end,
                ...(filterModel.items.length > 0 && { filter: JSON.stringify(filterModel.items[0]) })
            });
            const data: SubmissionType[] = response.data;
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
        finally {
            setIsLoading(false);
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

    const CustomPagination = DatagridPaginationMaker(
        () => totalCount,
        () => paginationModel,
        setPaginationModel,
        () => PAGE_SIZES
    );

    /* No veto status shown
    const vetoedOrNot = null;
    */

    return (
        <CardWithTitle title={"Your Submissions"} >
            <Box display="flex" gap={2} justifyContent="flex-start" mb={1}>
                <Typography variant="h5" gutterBottom>

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
                    loading={isLoading}
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

                    slots={{pagination: CustomPagination}}
                />
            </Box>

            <Box display="flex" gap={2} justifyContent="flex-start" mt={1}>
                <Box flexGrow={1} > {/* vetoedOrNot */} </Box>
                <Button
                    disabled={vetoed || runtimeProps.currentUser === null}
                    variant="contained"
                    startIcon={<EditIcon/>}
                    href={runtimeProps.URLS.newSubmissionURL}
                    sx={{
                        minWidth: "fit-content",
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
        </CardWithTitle>
    );
}

export default YourSubmissions;
