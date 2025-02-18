import React, {useCallback, useEffect, useState} from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import {DataGrid, GridColDef, GridRowParams, GridFilterModel, GridPaginationModel} from '@mui/x-data-grid';
import {RuntimeProps} from "../RuntimeContext.tsx";
// import SubmissionStatusName from "./SubmissionStatusName.tsx";
// import categoryChooser from "./CategoryChooser.tsx";
import { paths as adminApi } from "../types/admin-api";

type SubmissionType = adminApi['/v1/submissions/{id}']['get']['responses']['200']['content']['application/json'];
type SubmissionsType = adminApi['/v1/submissions/']['get']['responses']['200']['content']['application/json'];

const PAGE_SIZES = [5, 20, 100];

// type SubmissionStatus = "all" | "current" | "accepted" | "processing" | "invalid" | "expired" | "published";

const columns: GridColDef<SubmissionType>[] = [
    { field: 'id', headerName: 'Submission Id', width: 100 },
    {
        field: 'type',
        headerName: 'Type',
        width: 80,
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
    },
    {
        field: 'expires',
        headerName: 'Expires',
        type: 'date',
        width: 110,
    },
];


const SubmissionsTable: React.FC<{runtimeProps: RuntimeProps}> = ({runtimeProps}) => {
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

    // Pagination state
    const [totalCount, setTotalCount] = useState<number>(0);

    const fetchSubmissions = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        const start = paginationModel.page * paginationModel.pageSize;
        const end = start + paginationModel.pageSize;
        const query = new URLSearchParams();

        query.append("submitter_id", runtimeProps.currentUser.id);
        query.append("_start", start.toString());
        query.append("_end", end.toString());

        filterModel.items.forEach((filter) => {
            console.log("filter " + JSON.stringify(filter));
            if (filter.value) {
                query.append("filter", JSON.stringify(filter));
            }
        });

        try {
            const response = await fetch(runtimeProps.UP_API_URL  + `/submissions/?${query.toString()}`);
            const data: SubmissionType[] = await response.json();
            const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);
            console.log("total count " + total);
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
    }, [paginationModel, filterModel]);

    useEffect(() => {
        fetchSubmissions();
    }, [fetchSubmissions]);

    useEffect(() => {
        console.log("n subs " + submissions.length);
    }, [submissions]);


    return (
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

                getDetailPanelContent={({ row }: GridRowParams<SubmissionType>) => (
                    <Box sx={{ padding: 2, backgroundColor: "#f9f9f9" }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                            Abstract:
                        </Typography>
                        <Typography variant="body2">{row.abstract}</Typography>
                    </Box>
                )}

            />
        </Box>
    );
};

export default SubmissionsTable;
