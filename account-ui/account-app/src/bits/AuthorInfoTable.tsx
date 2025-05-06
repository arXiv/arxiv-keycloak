import React from "react";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";

interface AuthorInfoTableProps {
    ownerCount: number;
    submitCount: number;
    authorCount: number;
}
const AuthorInfoTable: React.FC<AuthorInfoTableProps> = ({
                                                     ownerCount,
                                                     submitCount,
                                                     authorCount,
                                                 }) => {
    return (
                <Table size="small">
                    <TableBody>
                        <TableRow>
                            <TableCell>Owns</TableCell>
                            <TableCell>Submitted</TableCell>
                            <TableCell>Authored</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>{ownerCount}{ownerCount > 1 ? " articles" : " article"}</TableCell>
                            <TableCell>{submitCount}{submitCount > 1 ? " articles" : " article"}</TableCell>
                            <TableCell>{authorCount}{authorCount > 1 ? " articles" : " article"}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
    );
};

export default AuthorInfoTable;
