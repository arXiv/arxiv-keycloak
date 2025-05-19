import React, {useCallback, useEffect, useState} from "react";
import {
    DataGrid,
    GridColDef,
    GridFilterModel,
    GridPaginationModel,
    GridRowSelectionModel, GridRenderCellParams
} from '@mui/x-data-grid';
import {RuntimeProps} from "../RuntimeContext.tsx";
import {paths as adminApi} from "../types/admin-api";
import DeleteIcon from "@mui/icons-material/Delete";
import UndoIcon from "@mui/icons-material/Undo";
// import Container from '@mui/material/Container'
import RefreshIcon from '@mui/icons-material/Refresh';
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
// import EditIcon from "@mui/icons-material/Edit";
import Link from "@mui/material/Link";
import DatagridPaginationMaker from "../bits/DataGridPagination.tsx";
import {fetchPlus} from "../fetchPlus.ts";
import {utcToNnewYorkDatePrinter} from "../bits/printer.ts";
import IconButton from '@mui/material/IconButton';
import CardWithTitle from "../bits/CardWithTitle.tsx";

type OwnershipRequestType = adminApi['/v1/ownership_requests/{id}']['get']['responses']['200']['content']['application/json'];
type OwnershipRequestsType = adminApi['/v1/ownership_requests/']['get']['responses']['200']['content']['application/json'];

const PAGE_SIZES = [5, 20, 100];

type OwnershipRequestStatusType = "pending" | "accepted" | "rejected";
const OwnershipRequestStatusMetadata : { // @ts-ignore
    [name: OwnershipRequestStatusType]: string } = {
    pending: "Pending",
    accepted: "Accepted",
    rejected: "Rejected"
}

const DocumentLink: React.FC<{ runtimeProps: RuntimeProps, paper_id: string }> = ({runtimeProps, paper_id}) =>
{
    return (<Link href={`${runtimeProps.URLS.arXiv}/pdf/${paper_id}`} children={paper_id} />);
}

const YourOwnershipRequests: React.FC<{ runtimeProps: RuntimeProps }> = ({runtimeProps}) => {
    const [isLoading, setIsLoading] = useState(false);
    const [ownershipRequests, setOwnershipRequests] = useState<OwnershipRequestsType>([]);
    const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
        page: 0, // starts at page 0
        pageSize: PAGE_SIZES[0],
    });
    const [filterModel, setFilterModel] = useState<GridFilterModel>({items: [],});
    const [totalCount, setTotalCount] = useState<number>(0);

    const fetchOwnershipRequests = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        // const interestedIds = Object.values(submissinStatusList).filter(status => status.group === "current" || status.group === "processing");

        const start = paginationModel.page * paginationModel.pageSize;
        const end = start + paginationModel.pageSize;
        const query = new URLSearchParams();

        query.append("user_id", runtimeProps.currentUser.id);
        query.append("_start", start.toString());
        query.append("_end", end.toString());

        filterModel.items.forEach((filter) => {
            if (filter.value) {
                query.append("filter", JSON.stringify(filter));
            }
        });

        try {
            setIsLoading(true);
            const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/ownership_requests/?${query.toString()}`);
            const data: OwnershipRequestsType = await response.json();
            const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);
            setTotalCount(total);
            setOwnershipRequests(data);
        } catch (err) {
            console.error("Error fetching ownershipRequests:", err);
        }
        finally {
            setIsLoading(false);
        }
    }, [paginationModel, filterModel]);

    useEffect(() => {
        fetchOwnershipRequests();
    }, [fetchOwnershipRequests]);

    useEffect(() => {
        console.log("n subs " + ownershipRequests.length);
    }, [ownershipRequests]);

    const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);

    const handleDelete = () => {
        console.log("Deleting rows:", selectedRows);
        // Implement delete logic here
    };

    const handleUnsubmit = () => {
        console.log("Unsubmitting rows:", selectedRows);
        // Implement unsubmit logic here
    };


    const columns: GridColDef<OwnershipRequestType>[] = [
        {
            field: 'id', headerName: 'Identifier', width: 100,
            renderCell: (cell: GridRenderCellParams) => {
                return cell.value;
            }
        },
        {
            field: 'date', headerName: 'Date', width: 100,
            renderCell: (cell: GridRenderCellParams) => { return utcToNnewYorkDatePrinter(cell.value); }
        },
        {
            field: 'workflow_status',
            headerName: 'Status',
            width: 80,
            renderCell: (cell: GridRenderCellParams) => {
                // @ts-ignore
                return <>{cell?.value ? OwnershipRequestStatusMetadata[cell.value] : "Unknown"}</>;
            }
        },
        {
            field: 'paper_ids',
            headerName: 'Articles',
            flex: 1,
            renderCell: (cell: GridRenderCellParams) =>
                {
                    const paperIds = cell?.value || [];
                    return (
                        <Box sx={{ display: 'flex', flexDirection: 'row', gap: "1rem" }}>
                            {
                                paperIds.map((paper_id: string) => (
                                    <DocumentLink key={paper_id} runtimeProps={runtimeProps} paper_id={paper_id} />
                                ))
                            }
                        </Box>
                    );
                }
        },
    ];

    const CustomPagination = DatagridPaginationMaker(
        () => totalCount,
        () => paginationModel,
        setPaginationModel,
        () => PAGE_SIZES
    );


    return (
        <CardWithTitle title={"Your Ownership Requests"}>
            <Box display="flex" gap={2} justifyContent="flex-start" mb={1}>
                <Box flexGrow={1}/>
                <IconButton onClick={fetchOwnershipRequests} title="Refresh" disabled={isLoading} >
                    <RefreshIcon />
                </IconButton>
                <Button
                    variant="contained"
                    color="error"
                    startIcon={<DeleteIcon/>}
                    onClick={handleDelete}
                    disabled={selectedRows.length === 0} // Disable when no rows are selected
                    aria-label="Delete OwnershipRequests"
                >
                    Delete
                </Button>

                <Button
                    variant="contained"
                    color="warning"
                    startIcon={<UndoIcon/>}
                    onClick={handleUnsubmit}
                    disabled={selectedRows.length === 0} // Disable when no rows are selected
                    aria-label="Unsubmit OwnershipRequests"
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
                    rows={ownershipRequests}
                    rowCount={totalCount}

                    checkboxSelection
                    disableRowSelectionOnClick
                    onRowSelectionModelChange={(newSelection) => setSelectedRows(newSelection)}

                    slots={{pagination: CustomPagination}}
                />
            </Box>
        </CardWithTitle>
    );
}

export default YourOwnershipRequests;
