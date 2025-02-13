import React, { useEffect, useState } from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Select,
    MenuItem,
    TextField,
    IconButton,
    Collapse,
    Box,
    SelectChangeEvent, TableFooter, TablePagination,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import {RuntimeProps} from "../RuntimeContext.tsx";
import {paths} from "../types/up-api.ts"
import SubmissionStatusName from "./SubmissionStatusName.tsx";
// import categoryChooser from "./CategoryChooser.tsx";

type SubmissionType = paths['/v1/submissions/{id}']['get']['responses']['200']['content']['application/json'];
type SubmissionsType = paths['/v1/submissions/']['get']['responses']['200']['content']['application/json'];

const PAGE_SIZES = [10, 25, 50];

type SubmissionStatus = "all" | "current" | "accepted" | "processing" | "invalid" | "expired" | "published";

const SubmissionsTable: React.FC<{runtimeProps: RuntimeProps}> = ({runtimeProps}) => {
    const [submissions, setSubmissions] = useState<SubmissionsType>([]);
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
    const [statusFilter, setStatusFilter] = useState<SubmissionStatus>("all");
    const [titleFilter, setTitleFilter] = useState<string>("");

    // Pagination state
    const [page, setPage] = useState<number>(0);
    const [pageSize, setPageSize] = useState<number>(10);
    const [totalCount, setTotalCount] = useState<number>(0);

    // Fetch submissions from API
    useEffect(() => {
        if (runtimeProps.currentUser) {
            fetchSubmissions();
        }
    }, [runtimeProps.currentUser, page, pageSize, statusFilter, titleFilter]);

    const fetchSubmissions = async () => {
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

            const response = await fetch(runtimeProps.UP_API_URL  + `/submissions/?${query.toString()}`);
            const data: SubmissionType[] = await response.json();
            const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);

            setSubmissions(
                data.map((submission) => ({
                    ...submission,
                    identifier: Number(submission.id),
                    expires: Number(submission.created),
                }))
            );
            setTotalCount(total);
        } catch (err) {
            console.error("Error fetching submissions:", err);
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
        setStatusFilter(event.target.value as unknown as SubmissionStatus);
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
                            <TableCell>Type</TableCell>
                            <TableCell>Title</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Expires</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {submissions.length > 0 ? (
                            submissions.map((submission) => (
                                <React.Fragment key={submission.id}>
                                    {/* Main Row */}
                                    <TableRow>
                                        <TableCell>
                                            <IconButton onClick={() => toggleRow(submission.id.toString())}>
                                                {expandedRows[submission.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                            </IconButton>
                                        </TableCell>
                                        <TableCell>{submission.id}</TableCell>
                                        <TableCell>{submission.type}</TableCell>
                                        <TableCell>{submission.title}</TableCell>
                                        <TableCell><SubmissionStatusName status={submission.status} /></TableCell>
                                        <TableCell>{submission.created}</TableCell>
                                    </TableRow>

                                    {/* Expanded Row */}
                                    <TableRow>
                                        <TableCell colSpan={6} sx={{ padding: 0 }}>
                                            <Collapse in={expandedRows[submission.id]} timeout="auto" unmountOnExit>
                                                <Box margin={2}>
                                                    <strong>Additional Details:</strong>
                                                    <pre>{JSON.stringify(submission.abstract, null, 2)}</pre>
                                                </Box>
                                            </Collapse>
                                        </TableCell>
                                    </TableRow>
                                </React.Fragment>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    No submissions found.
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

export default SubmissionsTable;
