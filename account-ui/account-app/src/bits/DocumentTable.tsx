import React, { useEffect, useState } from "react";
import Box from "@mui/material/Box";
// import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableFooter from "@mui/material/TableFooter";
import TableRow from "@mui/material/TableRow";
import TablePagination from "@mui/material/TablePagination";
import Paper from "@mui/material/Paper";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import IconButton from "@mui/material/IconButton";
import Collapse from "@mui/material/Collapse";

import {
    SelectChangeEvent,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import {RuntimeProps} from "../RuntimeContext.tsx";
import { paths as adminApi } from "../types/admin-api";
// import DocumentStatusName from "./DocumentStatusName.tsx";
// import categoryChooser from "./CategoryChooser.tsx";

type DocumentType = adminApi['/v1/documents/{id}']['get']['responses']['200']['content']['application/json'];
type DocumentsType = adminApi['/v1/documents/']['get']['responses']['200']['content']['application/json'];

const PAGE_SIZES = [10, 25, 50];

type DocumentStatus = "all" | "current" | "accepted" | "processing" | "invalid" | "expired" | "published";

const DocumentTable: React.FC<{runtimeProps: RuntimeProps}> = ({runtimeProps}) => {
    const [documents, setDocuments] = useState<DocumentsType>([]);
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
    const [statusFilter, setStatusFilter] = useState<DocumentStatus>("all");
    const [titleFilter, setTitleFilter] = useState<string>("");

    // Pagination state
    const [page, setPage] = useState<number>(0);
    const [pageSize, setPageSize] = useState<number>(10);
    const [totalCount, setTotalCount] = useState<number>(0);

    // Fetch documents from API
    useEffect(() => {
        if (runtimeProps.currentUser) {
            fetchDocuments();
        }
    }, [runtimeProps.currentUser, page, pageSize, statusFilter, titleFilter]);

    const fetchDocuments = async () => {
        if (!runtimeProps.currentUser)
            return;

        try {
            const start = page * pageSize;
            const end = start + pageSize;
            const query = new URLSearchParams();

            query.append("submitter_id", runtimeProps.currentUser.id);
            query.append("_start", start.toString());
            query.append("_end", end.toString());
            if (statusFilter) query.append("status", statusFilter);
            if (titleFilter) query.append("title_like", titleFilter);

            const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL  + `/documents/?${query.toString()}`);
            const data: DocumentType[] = await response.json();
            const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);

            setDocuments(
                data.map((document) => ({
                    ...document,
                    identifier: Number(document.id),
                    expires: Number(document.created),
                }))
            );
            setTotalCount(total);
        } catch (err) {
            console.error("Error fetching documents:", err);
        }
    };

    // Toggle row expansion
    const toggleRow = (id: string) => {
        setExpandedRows((prev) => ({
            ...prev,
            [id]: !prev[id],
        }));
    };

    // Handle filtering
    const handleStatusChange = (event: SelectChangeEvent<string>) => {
        setStatusFilter(event.target.value as unknown as DocumentStatus);
    };

    const handlePageSizeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setPageSize(parseInt(event.target.value, 10));
        setPage(0); // Reset to first page on size change
    };

    const handlePageChange = (_event: React.MouseEvent<HTMLButtonElement> | null, newPage: number) => {
        setPage(newPage);
    };

    return (
        <div>
            {/* Filters Section */}
            <Box display="flex" gap={2} mb={2}>
                <Select
                    value={statusFilter.toString()}
                    onChange={handleStatusChange}
                    displayEmpty
                    size="small"
                    variant={"standard"}>
                    <MenuItem value="all">All Statuses</MenuItem>
                    <MenuItem value="current">In progress</MenuItem>
                    <MenuItem value="processing">Pending</MenuItem>
                    <MenuItem value="accepted">Accepted</MenuItem>
                    <MenuItem value="published">Published</MenuItem>
                    <MenuItem value="invalid">Removed or Error</MenuItem>
                    <MenuItem value="expired">Expired (files removed)</MenuItem>
                </Select>

                <TextField
                    label="Search by Title"
                    variant="outlined"
                    size="small"
                    value={titleFilter}
                    onChange={(e) => setTitleFilter(e.target.value)}
                />
            </Box>

            {/* Table */}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell />
                            <TableCell>Identifier</TableCell>
                            <TableCell>Title</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Expires</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {documents.length > 0 ? (
                            documents.map((document) => (
                                <React.Fragment key={document.id}>
                                    {/* Main Row */}
                                    <TableRow>
                                        <TableCell>
                                            <IconButton onClick={() => toggleRow(document.id.toString())}>
                                                {expandedRows[document.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                            </IconButton>
                                        </TableCell>
                                        <TableCell>{document.paper_id}</TableCell>
                                        <TableCell>{document.title}</TableCell>
                                        <TableCell>{document.authors}</TableCell>
                                    </TableRow>

                                    {/* Expanded Row */}
                                    <TableRow>
                                        <TableCell colSpan={6} sx={{ padding: 0 }}>
                                            <Collapse in={expandedRows[document.id]} timeout="auto" unmountOnExit>
                                                <Box margin={2}>
                                                    <strong>Additional Details:</strong>
                                                    <pre>{JSON.stringify(document.paper_id,  null, 2)}</pre>
                                                </Box>
                                            </Collapse>
                                        </TableCell>
                                    </TableRow>
                                </React.Fragment>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    No documents found.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>

                    {/* Pagination Footer */}
                    <TableFooter>
                        <TableRow>
                            <TablePagination
                                rowsPerPageOptions={PAGE_SIZES}
                                count={totalCount}
                                rowsPerPage={pageSize}
                                page={page}
                                onPageChange={handlePageChange}
                                onRowsPerPageChange={handlePageSizeChange}
                                labelDisplayedRows={({ from, to, count }) =>
                                    `${from}-${to} of ${count !== -1 ? count : "more"}`
                                }
                            />
                        </TableRow>
                    </TableFooter>
                </Table>
            </TableContainer>

        </div>
    );
};

export default DocumentTable;
