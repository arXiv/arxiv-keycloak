import React, {useCallback, useContext, useEffect, useState} from "react";
import {
    DataGrid,
    GridColDef,
    GridFilterModel,
    GridPaginationModel,
    GridRenderCellParams,
    GridSortModel, GridRowSelectionModel,
} from '@mui/x-data-grid';
// import {GridFilterOperator} from "@mui/x-data-grid/models/gridFilterOperator";
import {RuntimeContext} from "../RuntimeContext.tsx";
import UnlockIcon from "@mui/icons-material/LockOpen";
// import AuthorIcon from "@mui/icons-material/Attribution";
import AuthorIcon from '../icons/AuthorIcon.tsx';
// import NonAuthorIcon from "@mui/icons-material/LocalShipping";
// import NonAuthorIcon from "@mui/icons-material/SupervisedUserCircle";
import NonAuthorIcon from "../icons/NonAuthorIcon.tsx";
// import UndoIcon from "@mui/icons-material/Undo";
// import Container from '@mui/material/Container'
// import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
// import PaperPassword from "../bits/PaperPassword.tsx";
import IconButton from "@mui/material/IconButton";
// import Container from "@mui/material/Container";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import MoreVertIcon from "@mui/icons-material/MoreVert";
// import TablePagination, { TablePaginationProps } from "@mui/material/TablePagination";
// import DataGridDateRangeFilter from "../bits/DataGridDateRangeFilter.tsx";
import {useNotification} from "../NotificationContext";

import ReplaceIcon from "../assets/images/replace.png";
import WithdrawIcon from "../assets/images/withdraw.png";
import CrossListIcon from "../assets/images/cross.png";
import JournalReferenceIcon from "../assets/images/journalref.png";
import LinkCodeDataIcon from "../assets/images/pwc_logo.png";
import DatagridPaginationMaker from "../bits/DataGridPagination.tsx";
import Button from "@mui/material/Button";
// import CardWithTitle from "../bits/CardWithTitle.tsx";
import {paths as adminApi} from "../types/admin-api";
import {
    ADMIN_DOCUMENTS_USER_ACTION_URL,
    ADMIN_PAPER_OWNERS_AUTHORSHIP_ACTION_URL, ADMIN_PAPER_OWNERS_ID_URL,
    ADMIN_PAPER_OWNERS_URL,
    ADMIN_PAPER_PW_ID_URL
} from "../types/admin-url.ts";


// type DocumentType = adminApi['/v1/documents/{id}']['get']['responses']['200']['content']['application/json'];
// type DocumentsType = adminApi['/v1/documents/']['get']['responses']['200']['content']['application/json'];
// type DemographicType = adminApi['/v1/demographics/{id}']['get']['responses']['200']['content']['application/json'];
type PaperPasswordResponseType = adminApi[typeof ADMIN_PAPER_PW_ID_URL]['get']['responses']['200']['content']['application/json'];
type PaperAuthoredRequestType = adminApi[typeof ADMIN_PAPER_OWNERS_AUTHORSHIP_ACTION_URL]['put']['requestBody']['content']['application/json'];
// type PaperOwnerListRequestType = adminApi['/v1/paper_owners/']['get']['requestBody'];
type PaperOwnerListResponseType = adminApi[typeof ADMIN_PAPER_OWNERS_URL]['get']['responses']['200']['content']['application/json'];
type PaperOwnerType = adminApi[typeof ADMIN_PAPER_OWNERS_ID_URL]['get']['responses']['200']['content']['application/json'];


const PAGE_SIZES = [5, 20, 100];

const ImageIcon = (image: string) => (
    <Box
        component="span"
        sx={{
            width: 24,
            height: 24,
            display: "inline-block",
            backgroundImage: `url(${image})`,
            backgroundSize: "contain",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "center",
        }}
    />);

const menuActions = [
    {label: "Replace", icon: ImageIcon(ReplaceIcon), action: "replace"},
    {label: "Withdraw", icon: ImageIcon(WithdrawIcon), action: "withdraw"},
    {label: "Cross list", icon: ImageIcon(CrossListIcon), action: "cross"},
    {label: "Journal reference", icon: ImageIcon(JournalReferenceIcon), action: "jref"},
    {label: "Link code & data", icon: ImageIcon(LinkCodeDataIcon), action: "pwc_link"},
    {label: "Paper Password", icon: <UnlockIcon/>, action: "paper_password"},
];

const ActionMenu: React.FC<{
    rowId: string;
    anchorEl: null | HTMLElement;
    position: { mouseX: number, mouseY: number } | null;
    onClose: (rowId: string, action: string) => void;
}> = ({rowId, anchorEl, position, onClose}) => {
    const open = Boolean(anchorEl || position);

    const handleAction = (action: string) => {
        console.log(`Action "${action}" clicked for row ${rowId}`);
        onClose(rowId, action);
    };

    return (
        <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={onClose}
            anchorReference={position ? "anchorPosition" : "anchorEl"}
            anchorPosition={position ? {top: position.mouseY, left: position.mouseX} : undefined}
        >
            {menuActions.map((action) => (
                <MenuItem key={action.label} onClick={() => handleAction(action.action)}>
                    <ListItemIcon>
                        {action.icon}
                    </ListItemIcon>
                    <ListItemText primary={action.label}/>
                </MenuItem>
            ))}
        </Menu>
    );
};

/*
const dateFilterOperators: GridFilterOperator[] = [
    {
        label: "Between",
        value: "between",
        getApplyFilterFn: (filterItem) => {
            if (!filterItem.value || filterItem.value.length !== 2) return null;
            return ({value}) => {
                if (!value) return false;
                const [startDate, endDate] = filterItem.value;
                const rowDate = new Date(value);
                return rowDate >= new Date(startDate) && rowDate <= new Date(endDate);
            };
        },
        InputComponent: DataGridDateRangeFilter, // Use the MUI Date Picker component
    },
];

const Author: React.FC<{ yes: boolean }> = ({yes}) => {
    return yes ? <AuthorIcon sx={{scale: "2.75", pt: "3px"}}/> : <NonAuthorIcon sx={{scale: "2.75", pt: "3px"}}/>;
};
*/

const UserDocumentList: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const {showMessageDialog, showNotification} = useNotification();
    const [isLoading, setIsLoading] = useState<boolean>(false);
    // const [isDemographicLoading, setIsDemographicLoading] = useState<boolean>(false);
    // const [demographic, setDemographic] = useState<DemographicType | null>(null);
    const [papers, setPapers] = useState<PaperOwnerListResponseType>([]);
    const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
        page: 0, // starts at page 0
        pageSize: PAGE_SIZES[0],
    });
    const [filterModel, setFilterModel] = useState<GridFilterModel>(
        {
            items: [],
        }
    );
    const [sortModel, setSortModel] = useState<GridSortModel>([]);

    /*
        const [totalSubmissions, setTotalSubmissions] = useState<number>(0);
        const [allPaperCount, setAllPaperCount] = useState<number>(0);
     */

    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
    const [menuPosition, setMenuPosition] = useState<{ mouseX: number, mouseY: number } | null>(null);
    const [selectedRowId, setSelectedRowId] = useState<string | null>(null);
    const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
    const [paperCount, setPaperCount] = useState<number>(0);


    const fetchMyPapers = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        try {

            // const interestedIds = Object.values(submissinStatusList).filter(status => status.group === "current" || status.group === "processing");
            const start = paginationModel.page * paginationModel.pageSize;
            const end = start + paginationModel.pageSize;

            setIsLoading(true);
            const getPaperOwners = runtimeProps.adminFetcher.path(ADMIN_PAPER_OWNERS_URL).method('get').create();
            const response1 = await getPaperOwners({
                user_id: runtimeProps.currentUser.id,
                with_document: true,
                _start: start,
                _end: end,
                ...(sortModel.length > 0 && {_sort: sortModel[0].field}),
                ...(sortModel.length > 0 && sortModel[0].sort && {_order: sortModel[0].sort.toUpperCase()}),
                ...(filterModel.items.length > 0 && {filter: JSON.stringify(filterModel.items[0])})
            });

            if (!response1.ok) {
                if (response1.status >= 500) {
                    showNotification("Data service is not responding", "warning");
                    return;
                }
                const errorMessage = (response1.data as any)?.detail || response1.statusText || "Error fetching papers";
                showNotification(errorMessage, "warning");
                return;
            }
            const myPapers: PaperOwnerListResponseType = response1.data;
            const total = parseInt(response1.headers?.get?.("X-Total-Count") || "0", 10);
            setPaperCount(total);
            setPapers(myPapers);
        } catch (err) {
            console.error("Error fetching documents:", err);
        } finally {
            setIsLoading(false);
        }
    }, [paginationModel, filterModel, sortModel, runtimeProps.currentUser, runtimeProps.adminFetcher, showNotification]);

    useEffect(() => {
        fetchMyPapers();
    }, [fetchMyPapers]);


    const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, rowId: string) => {
        event.stopPropagation(); // Prevent right-click event from triggering
        setSelectedRowId(rowId);
        setMenuAnchor(event.currentTarget);
        setMenuPosition(null);
    };

    /*
        const handleRightClick: GridEventListener<'cellClick'> = (params , event, _details) => {
            console.log(JSON.stringify(params));
            event.preventDefault();
            if (params.field === "title") {
                setSelectedRowId(params.id as number);
                setMenuAnchor(null);
                setMenuPosition({ mouseX: event.clientX, mouseY: event.clientY });
            }
        };
    */

    const handleMenuClose = (rowId: string, action: string) => {
        setMenuAnchor(null);
        setMenuPosition(null);

        if (action === "paper_password") {
            async function showPaperPassword() {
                try {
                    setIsLoading(true);
                    const getPaperPassword = runtimeProps.adminFetcher.path(ADMIN_PAPER_PW_ID_URL).method('get').create();
                    const response = await getPaperPassword({id: rowId});
                    if (response.ok) {
                        const body: PaperPasswordResponseType = response.data;
                        showMessageDialog(body.password_enc, "Paper Password");
                    } else {
                        const errorMessage = (response.data as any)?.detail || "Paper Password Not Found";
                        showMessageDialog(errorMessage, "Paper Password Not Found");
                    }
                } catch (error) {
                    console.error("Error fetching paper password:", error);
                } finally {
                    setIsLoading(false);
                }
            }

            showPaperPassword();
        } else if (action !== "") {
            const match = rowId.match(/^user_(\d+)-doc_(\d+)$/);
            if (match) {
                const [, /*_user_id*/, doc_id] = match;
                const url = runtimeProps.ADMIN_API_BACKEND_URL + ADMIN_DOCUMENTS_USER_ACTION_URL.replace('{id}', doc_id).replace('{action}', action.toLowerCase());
                window.open(url, '_blank');
            } else {
                showMessageDialog(`Action: ${action} of document ID ${rowId}`, `${action} not implemented yet`);
            }
        }
    };

    const updateAuthored = useCallback(async (authored: boolean) => {
        if (!runtimeProps?.currentUser)
            return;
        const docIds: string[] = selectedRows.map((row) => String(row));
        console.log("docIds", docIds);
        const body: PaperAuthoredRequestType = {
            authored: authored ? docIds : [],
            not_authored: !authored ? docIds : [],
        }

        const updateAuthorship = runtimeProps.adminFetcher.path(ADMIN_PAPER_OWNERS_AUTHORSHIP_ACTION_URL).method('put').create();
        const response = await updateAuthorship({action: "update", ...body});
        if (response.ok) {
            await fetchMyPapers();
        } else {
            const errorMessage = (response.data as any)?.detail || response.statusText || "Error updating authorship";
            console.log(errorMessage);
        }
    }, [selectedRows, runtimeProps?.currentUser, runtimeProps.adminFetcher, fetchMyPapers]);


    const columns: GridColDef<PaperOwnerType>[] = [
        {
            field: 'document.paper_id',
            headerName: 'Identifier',
            width: 120,
            sortable: true,
            renderCell: (cell: GridRenderCellParams) => {
                return <Link href={`https://arxiv.org/abs/${cell.value}`} target="_">{cell.value}</Link>;
            },
            valueGetter: (_cell, row) => row.document?.paper_id || "",
        },
        {
            field: 'document.abs_categories',
            headerName: 'Primary Category',
            width: 100,
            sortable: false,
            renderCell: (cell: GridRenderCellParams) => {
                return cell.value?.split(' ')[0] ?? '';
            },
            valueGetter: (_cell, row) => row.document?.abs_categories,
        },
        {
            field: 'document.title',
            headerName: 'Title',
            flex: 1,
            sortable: false,
            valueGetter: (_cell, row) => row.document?.title || "No Title",
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 60,
            sortable: false,
            renderCell: (params) => (
                <IconButton onClick={(event) => handleMenuOpen(event, params.row.id)} size="small">
                    <MoreVertIcon/>
                </IconButton>
            )
        },
    ];

    const CustomPagination = DatagridPaginationMaker(
        () => paperCount,
        () => paginationModel,
        setPaginationModel,
        () => PAGE_SIZES
    );
    /* = (props: Partial<TablePaginationProps>) => {
        return (
            <TablePagination
                {...props}
                rowsPerPageOptions={PAGE_SIZES}
                component="div" // Required for DataGrid compatibility
                count={totalCount} // Ensure count is never undefined
                page={paginationModel.page ?? 0} // Ensure page is never undefined
                onPageChange={(_, newPage) => setPaginationModel((prev) => ({ ...prev, page: newPage }))}
                rowsPerPage={paginationModel.pageSize}
                onRowsPerPageChange={(event) => {
                    const newSize = parseInt(event.target.value, 10);
                    setPaginationModel({ page: 0, pageSize: newSize });
                }}
                showFirstButton
                showLastButton
            />
        );
    };
    */


    return (
        <>
            <Box display={"flex"} flexDirection={"row"} sx={{gap: 1, m: 1}}>
                <Box flexGrow={1}/>
                <Button id="authored_all" name="authored_all" variant="outlined"
                        disabled={selectedRows.length === 0}
                        onClick={() => updateAuthored(true)} startIcon={<AuthorIcon/>}
                >
                    I'm an author.
                </Button>
                <Button id="authored_none" name="authored_none" variant="outlined"
                        disabled={selectedRows.length === 0}
                        onClick={() => updateAuthored(false)} startIcon={<NonAuthorIcon/>}
                >
                    I am not an author.
                </Button>
            </Box>

            <Box display="flex" gap={0} mb={0}>

                <DataGrid<PaperOwnerType>
                    loading={isLoading}
                    filterModel={filterModel}
                    filterMode="server"
                    filterDebounceMs={1000}
                    onFilterModelChange={setFilterModel}

                    initialState={{pagination: {paginationModel: {pageSize: PAGE_SIZES[0]}}}}
                    pageSizeOptions={PAGE_SIZES}
                    paginationMode="server"
                    onPaginationModelChange={setPaginationModel}
                    sortingMode="server"
                    onSortModelChange={setSortModel}

                    columns={columns}
                    rows={papers}
                    rowCount={paperCount}
                    rowHeight={32}

                    columnHeaderHeight={32}

                    checkboxSelection
                    disableRowSelectionOnClick
                    onRowSelectionModelChange={(newSelection) => setSelectedRows(newSelection)}

                    slots={{
                        pagination: CustomPagination
                    }}
                />

                {selectedRowId !== null && (
                    <ActionMenu
                        rowId={selectedRowId}
                        anchorEl={menuAnchor}
                        position={menuPosition}
                        onClose={handleMenuClose}
                    />
                )}
            </Box>
        </>
    );
}

export default UserDocumentList;
