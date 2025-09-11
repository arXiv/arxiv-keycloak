import {forwardRef, useCallback, useEffect, useImperativeHandle, useState} from "react";
import {
    DataGrid,
    GridColDef,
    GridRowParams,
    GridFilterModel,
    GridPaginationModel,
    GridRenderCellParams,
} from '@mui/x-data-grid';
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Box from "@mui/material/Box";

import DeleteIcon from "@mui/icons-material/Delete";
import UndoIcon from "@mui/icons-material/Undo";
import {RuntimeProps} from "../RuntimeContext.tsx";
import DatagridPaginationMaker from "../bits/DataGridPagination.tsx";
import {paths as adminApi} from "../types/admin-api";
import {
    ADMIN_SUBMISSIONS_ID_URL,
    ADMIN_SUBMISSIONS_URL,
    ADMIN_SUBMISSIONS_METADATA_STATUS_LIST_URL
} from "../types/admin-url.ts";
import IconButton from "@mui/material/IconButton";
import EditIcon from "@mui/icons-material/Edit";
import NoEditIcon from "@mui/icons-material/EditOff";

type SubmissionType = adminApi[typeof ADMIN_SUBMISSIONS_ID_URL]['get']['responses']['200']['content']['application/json'];
// type SubmissionsType = adminApi[typeof ADMIN_SUBMISSIONS_URL]['get']['responses']['200']['content']['application/json'];
type SubmissionsStatusListType = adminApi[typeof ADMIN_SUBMISSIONS_METADATA_STATUS_LIST_URL]['get']['responses']['200']['content']['application/json'];
type SubmissionsStatusType = SubmissionsStatusListType[number];
type SubmissionStatusIdType = SubmissionsStatusType['id'];
type SubmissionStatusRecordType = Record<SubmissionStatusIdType, SubmissionsStatusType>;



const PAGE_SIZES = [5, 20, 100];
const EMPTY_SUBMISSION_STATUS_RECORD: SubmissionStatusRecordType = {};

interface SubmissionDatagridProps {
    runtimeProps: RuntimeProps;
    submissionStatusGroup: string;
    onDataChange?: () => void;
}

export interface SubmissionDatagridRef {
    refresh: () => void;
}

type SubmissionWithActionType = SubmissionType & {
    editable: boolean;
    deletable: boolean;
    undoable: boolean;
}

const SubmissionDatagrid = forwardRef<SubmissionDatagridRef, SubmissionDatagridProps>((
    {
        runtimeProps,
        submissionStatusGroup,
        onDataChange,
    },
    ref
) => {
    const [isLoading, setIsLoading] = useState(false);
    const [submissions, setSubmissions] = useState<SubmissionWithActionType[]>([]);
    const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
        page: 0,
        pageSize: PAGE_SIZES[0],
    });
    const [filterModel, setFilterModel] = useState<GridFilterModel>({
        items: [],
    });
    const [totalCount, setTotalCount] = useState<number>(0);
    const [submissionStatusList, setSubmissionStatusList] = useState<SubmissionStatusRecordType>(EMPTY_SUBMISSION_STATUS_RECORD);

    useEffect(() => {
        async function doSubmissionStatusList() {
            if (submissionStatusList === EMPTY_SUBMISSION_STATUS_RECORD) {
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
                    setSubmissionStatusList(record);
                } catch (e) {
                    console.error("doSubmissionStatusList: " + e);
                }
                finally {
                    setIsLoading(false);
                }
            }
        }
        doSubmissionStatusList();
    }, [submissionStatusList, runtimeProps]);

    const fetchSubmissions = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        if (!submissionStatusList || submissionStatusList === EMPTY_SUBMISSION_STATUS_RECORD)
            return;

        const start = paginationModel.page * paginationModel.pageSize;
        const end = start + paginationModel.pageSize;

        try {
            setIsLoading(true);
            const getSubmissions = runtimeProps.adminFetcher.path(ADMIN_SUBMISSIONS_URL).method('get').create();
            const response = await getSubmissions({
                submitter_id: Number(runtimeProps.currentUser.id),
                submission_status_group: submissionStatusGroup,
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
                    editable: submission.status === 0,
                    deletable: true,
                    undoable: submission.status !== 0,
                }))
            );
        } catch (err) {
            console.error("Error fetching submissions:", err);
        }
        finally {
            setIsLoading(false);
        }
    }, [paginationModel, filterModel, submissionStatusList, runtimeProps.currentUser]);

    useEffect(() => {
        fetchSubmissions();
    }, [fetchSubmissions]);

    useImperativeHandle(ref, () => ({
        refresh: fetchSubmissions
    }), [fetchSubmissions]);

    const handleEdit = async (row: SubmissionWithActionType, isExpired: boolean) => {
        console.log("Edit row:", JSON.stringify(row.id));
        if (isExpired) {
            console.log("Edit row: Expired");
            return;
        }
        // Implement delete logic here
    };


    const handleDelete = async (row: SubmissionWithActionType, _isSubmitted: boolean) => {
        console.log("Deleting row:", JSON.stringify(row.id));
        // Implement delete logic here
        const deleteSubmission = runtimeProps.adminFetcher.path(ADMIN_SUBMISSIONS_ID_URL).method('delete').create();
        try {
            const response = await deleteSubmission({
                id: Number(row.id)
            });
            if (response.ok) {
                if (onDataChange) {
                    onDataChange();
                } else {
                    fetchSubmissions();
                }
            }
        } catch (error) {
            console.error("Error deleting submission:", error);
        }
    };

    const handleUnsubmit = async (row: SubmissionWithActionType) => {
        console.log("Unsubmitting row:", JSON.stringify(row.id));
        // Implement unsubmit logic here
        const updateSubmission = runtimeProps.adminFetcher.path(ADMIN_SUBMISSIONS_ID_URL).method('patch').create();

        try {
            const response = await updateSubmission({
                id: Number(row.id),
                status: "0", // ???
            });
            if (response.ok) {
                if (onDataChange) {
                    onDataChange();
                } else {
                    fetchSubmissions();
                }
            }
        } catch (error) {
            console.error("Error deleting submission:", error);
        }
    };


    const CustomPagination = DatagridPaginationMaker(
        () => totalCount,
        () => paginationModel,
        setPaginationModel,
        () => PAGE_SIZES
    );

    const columns: GridColDef<SubmissionWithActionType>[] = [
        {field: 'id', headerName: 'Identifier', width: 100,
            renderCell: (cell: GridRenderCellParams) => {
                return <Link href={`https://arxiv.org/submit/${cell.value}/resume`}>{cell.value}</Link>;
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
                return <>{submissionStatusList[cell?.value || "0"]?.name || "Unknown"}</>;
            }
        },
    ];

    // Hardcoding this is stupid.
    const fourteenDaysInMs = 14 * 24 * 60 * 60 * 1000;
    const currentTime = new Date().getTime();


    if (submissionStatusGroup === 'working')
        columns.push({
            field: 'submit_time',
            headerName: 'Expires',
            type: 'date',
            width: 110,
            valueGetter: (value, _row) => {
                const submitDate = new Date(value);
                return new Date(submitDate.getTime() + fourteenDaysInMs);
                },
        });

        columns.push({
            field: 'editable',
            headerName: '',
            width: 32,
            renderCell: (cell: GridRenderCellParams<SubmissionWithActionType>) => {
                // @ts-ignore
                const submitDate = new Date(cell.row.submit_time);
                const expiresOn = submitDate.getTime() + fourteenDaysInMs;
                const isExpired = currentTime > expiresOn;
                return <IconButton sx={{visibility: cell.row.editable ? 'visible' : 'hidden'}} onClick={() => handleEdit(cell.row, isExpired)}>
                    {isExpired ? <NoEditIcon /> : <EditIcon color={"primary"}/>}
                </IconButton>;
            }});

    if (submissionStatusGroup === 'current')
        columns.push({
            field: 'undoable',
            headerName: '',
            width: 32,
            renderCell: (cell: GridRenderCellParams<SubmissionWithActionType>) => {
                return <IconButton sx={{visibility: cell.row.undoable ? 'visible' : 'hidden'}} onClick={() => handleUnsubmit(cell.row)}><UndoIcon color={"warning"} /></IconButton>;
            }});

    columns.push({
        field: 'deletable',
        headerName: '',
        width: 32,
        renderCell: (cell: GridRenderCellParams<SubmissionWithActionType>) => {
            return <IconButton onClick={() => handleDelete(cell.row, submissionStatusGroup === "current")}><DeleteIcon color={"error"} /></IconButton>;
        }});


    return (
        <Box sx={{pt: 2}}>
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
            rowHeight={32}

            columnHeaderHeight={32}

            getDetailPanelContent={({row}: GridRowParams<SubmissionWithActionType>) => (
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
    );
});

SubmissionDatagrid.displayName = 'SubmissionDatagrid';

export default SubmissionDatagrid;