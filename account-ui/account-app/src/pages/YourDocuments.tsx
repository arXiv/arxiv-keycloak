import React, {useCallback, useContext, useEffect, useState} from "react";
import {
    DataGrid,
    GridColDef,
    GridRowParams,
    GridFilterModel,
    GridPaginationModel,
    GridRenderCellParams,
    GridSortModel,
} from '@mui/x-data-grid';
import { GridFilterOperator } from "@mui/x-data-grid/models/gridFilterOperator";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {paths as adminApi} from "../types/admin-api";
import UnlockIcon from "@mui/icons-material/LockOpen";
// import UndoIcon from "@mui/icons-material/Undo";
// import Container from '@mui/material/Container'
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Paper from "@mui/material/Paper";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
import DocumentMetadata from "../bits/DocumentMetadata.tsx";
// import PaperPassword from "../bits/PaperPassword.tsx";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import MoreVertIcon from "@mui/icons-material/MoreVert";
// import TablePagination, { TablePaginationProps } from "@mui/material/TablePagination";
import DataGridDateRangeFilter from "../bits/DataGridDateRangeFilter.tsx";
import ArticleInfo from "../bits/ArticleInfo.tsx";
import {useNotification} from "../NotificationContext";

import ReplaceIcon from "../assets/images/replace.png";
import WithdrawIcon from "../assets/images/withdraw.png";
import CrossListIcon from "../assets/images/cross.png";
import JournalReferenceIcon from "../assets/images/journalref.png";
import LinkCodeDataIcon from "../assets/images/pwc_logo.png";
import DatagridPaginationMaker from "../bits/DataGridPagination.tsx";


type DocumentType = adminApi['/v1/documents/{id}']['get']['responses']['200']['content']['application/json'];
// type MetadataType = adminApi['/v1/metadatas/{id}']['get']['responses']['200']['content']['application/json'];

type DocumentsType = adminApi['/v1/documents/']['get']['responses']['200']['content']['application/json'];

// SubmissionsType = adminApi['/v1/submissions/']['get']['responses']['200']['content']['application/json'];

type DemographicType = adminApi['/v1/demographics/{id}']['get']['responses']['200']['content']['application/json'];


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
    { label: "Replace", icon: ImageIcon(ReplaceIcon) },
    { label: "Withdraw", icon: ImageIcon(WithdrawIcon) },
    { label: "Cross list", icon: ImageIcon(CrossListIcon) },
    { label: "Journal reference", icon: ImageIcon(JournalReferenceIcon) },
    { label: "Link code & data", icon: ImageIcon(LinkCodeDataIcon) },
    { label: "Paper Password", icon: <UnlockIcon />}
];

const ActionMenu: React.FC<{
    rowId: number;
    anchorEl: null | HTMLElement;
    position: { mouseX: number, mouseY: number } | null;
    onClose: (rowId: number, action: string) => void;
}> = ({ rowId, anchorEl, position, onClose }) => {
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
            anchorPosition={position ? { top: position.mouseY, left: position.mouseX } : undefined}
        >
            {menuActions.map((action) => (
                <MenuItem key={action.label} onClick={() => handleAction(action.label)}>
                    <ListItemIcon>
                        {action.icon}
                    </ListItemIcon>
                    <ListItemText primary={action.label} />
                </MenuItem>
            ))}
        </Menu>
    );
};

const dateFilterOperators: GridFilterOperator[] = [
    {
        label: "Between",
        value: "between",
        getApplyFilterFn: (filterItem) => {
            if (!filterItem.value || filterItem.value.length !== 2) return null;
            return ({ value }) => {
                if (!value) return false;
                const [startDate, endDate] = filterItem.value;
                const rowDate = new Date(value);
                return rowDate >= new Date(startDate) && rowDate <= new Date(endDate);
            };
        },
        InputComponent: DataGridDateRangeFilter, // Use the MUI Date Picker component
    },
];


const YourDocuments: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const {showMessageDialog, showNotification} = useNotification();
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [demographic, setDemographic] = useState<DemographicType | null>(null);
    const [documents, setDocuments] = useState<DocumentsType>([]);
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

    const [totalSubmissions, setTotalSubmissions] = useState<number>(0);
    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
    const [menuPosition, setMenuPosition] = useState<{ mouseX: number, mouseY: number } | null>(null);
    const [selectedRowId, setSelectedRowId] = useState<number | null>(null);

    useEffect(() => {
        async function fetchSubmissions() {
            if (!runtimeProps.currentUser)
                return;

            // const interestedIds = Object.values(submissinStatusList).filter(status => status.group === "current" || status.group === "processing");
            const start = 0;
            const end = 1;
            const query = new URLSearchParams();

            query.append("submitter_id", runtimeProps.currentUser.id);
            query.append("_start", start.toString());
            query.append("_end", end.toString());

            try {
                setIsLoading(true);
                const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/submissions/?${query.toString()}`);
                const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);
                setTotalSubmissions(total);
            } catch (err) {
                console.error("Error fetching documents:", err);
            } finally {
                setIsLoading(false);
            }
        }

        fetchSubmissions();
    }, [runtimeProps.currentUser]);


    useEffect(() => {
        async function fetchDemographic() {
            if (!runtimeProps.currentUser)
                return;

            try {
                setIsLoading(true);
                const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/demographics/${runtimeProps.currentUser.id}`);
                const demographic: DemographicType = await response.json();
                setDemographic(demographic);
            } catch (err) {
                setDemographic(null);
                console.error("Error fetching user:", err);

            } finally {
                setIsLoading(false);
            }
        }

        fetchDemographic();
    }, [runtimeProps.currentUser]);


    // Pagination state
    const [totalCount, setTotalCount] = useState<number>(0);


    const fetchDocuments = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        // const interestedIds = Object.values(submissinStatusList).filter(status => status.group === "current" || status.group === "processing");
        const start = paginationModel.page * paginationModel.pageSize;
        const end = start + paginationModel.pageSize;
        const query = new URLSearchParams();

        query.append("submitter_id", runtimeProps.currentUser.id);
        query.append("_start", start.toString());
        query.append("_end", end.toString());
        if (sortModel) {
            for (const criteria of sortModel) {
                query.append("_sort", criteria.field);
                if (criteria.sort)
                    query.append("_order", criteria.sort.toUpperCase());
            }
        }

        filterModel.items.forEach((filter) => {
            console.log("filter " + JSON.stringify(filter));
            if (filter.value) {
                query.append("filter", JSON.stringify(filter));
            }
        });

        try {
            setIsLoading(true);
            const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL  + `/documents/?${query.toString()}`);
            if (!response.ok) {
                if (response.status >= 500) {
                    showNotification("Data service is not operating");
                }
                return;
            }
            const data: DocumentType[] = await response.json();
            const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);
            setTotalCount(total);

            setDocuments(
                data.map((document) => ({
                    ...document,
                    identifier: Number(document.id),
                    expires: Number(document.created),
                }))
            );
        } catch (err) {
            console.error("Error fetching documents:", err);
        }
        finally {
            setIsLoading(false);
        }
    }, [paginationModel, filterModel, sortModel, runtimeProps.currentUser]);

    useEffect(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    useEffect(() => {
        console.log("n subs " + documents.length);
    }, [documents]);

    const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, rowId: number) => {
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

    const handleMenuClose = (_rowId: number, action: string) => {
        setMenuAnchor(null);
        setMenuPosition(null);

        if (action === "Paper Password") {
            showMessageDialog("FOO", "BAR");
        }
    };

    const columns: GridColDef<DocumentType>[] = [
        {
            field: 'paper_id',
            headerName: 'Identifier',
            width: 120,
            sortable: true,
            renderCell: (cell: GridRenderCellParams) => {
                return <Link href={`https://arxiv.org/abs/${cell.value}`}>{cell.value}</Link>;
            }
        },
        {
            field: 'abs_categories',
            headerName: 'Primary Category',
            width: 100,
            sortable: false,
            renderCell: (cell: GridRenderCellParams) => {
                return cell.row.abs_categories.split(' ')[0];
            }
        },
        {
            field: 'dated',
            headerName: 'Date',
            width: 76,
            sortable: true,
            filterOperators: dateFilterOperators,
            renderCell: (cell: GridRenderCellParams) => {
                return new Date(cell.row.dated).toLocaleDateString('en-CA');
            }
        },
        {
            field: 'title',
            headerName: 'Title',
            flex: 1,
            sortable: false,
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 60,
            sortable: false,
            renderCell:  (params) => (
                <IconButton onClick={(event) => handleMenuOpen(event, params.row.id)} size="small">
                    <MoreVertIcon />
                </IconButton>
            )
        },
    ];

    const CustomPagination = DatagridPaginationMaker(
        () => totalCount,
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


    return (<>
        <ArticleInfo key="article-info"
                     authorCount={totalSubmissions}
                     authorId={demographic?.author_id}
                     ownerCount={totalCount} submitCount={totalSubmissions} orcidId={demographic?.orcid} orcidAuth={true} />

        <Paper elevation={3} sx={{p: 3, mt: 4}}>
            <Box display="flex" gap={2} justifyContent="flex-start" mb={1}>
                <Typography variant="h5" gutterBottom>
                    Articles You Own
                </Typography>
                <Box flexGrow={1}/>
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
                    sortingMode="server"
                    onSortModelChange={setSortModel}

                    columns={columns}
                    rows={documents}
                    rowCount={totalCount}

                    getDetailPanelContent={({row}: GridRowParams<DocumentType>) => (
                        <Box sx={{p: 2, backgroundColor: "#f9f9f9", b: 2}}>
                            <Typography variant="subtitle1" fontWeight="bold">
                                Abstract:
                            </Typography>
                            <DocumentMetadata arxivId={row.paper_id} />
                        </Box>
                    )}

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
        </Paper>
        </>
    );
}

export default YourDocuments;
