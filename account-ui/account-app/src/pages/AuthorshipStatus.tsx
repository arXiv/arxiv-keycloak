import React from "react";
import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import Paper from "@mui/material/Paper";

/*

This is a terrible page. This is mimicing the existing one but disfunctional and ugly.

 */
const AuthorshipStatus: React.FC = () => {
    return (
        <Box id="content" p={3}>
            <Typography variant="h4" gutterBottom>
                Change authorship information
            </Typography>

            <Typography paragraph>
                For each paper that you own in arXiv, you can be registered as an author
                or as a non-author. (At some institutes, for instance, submissions are made
                by administrative assistants who are non-authors.) In the process of
                upgrading our system, we tried to determine authors and non-authors by
                matching registered user names to the author names on papers. This process
                is more than 99% accurate, but because names have alternate spellings,
                we've made some mistakes.
            </Typography>

            <Typography paragraph>
                This form makes it simple for you to change the ownership status of your
                papers. If the checkbox next to a paper is checked, that means that arXiv
                believes you are the author of a paper. You can change this status by
                clicking on the checkbox and clicking on the "Save Changes" button.
            </Typography>

            <Typography paragraph>
                If, after careful inspection of the listing below, you are sure that you
                are an author or non-author of <b>ALL</b> the listed papers, you can click on
                the "I am an author of all of these papers" or "I am an author of none of these papers" buttons.
            </Typography>

            <form action="change-author-status" method="post">
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Author?</TableCell>
                                <TableCell>Paper id</TableCell>
                                <TableCell>Title</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {/* Dynamic rows go here */}
                        </TableBody>
                    </Table>
                </TableContainer>

                <Box mt={2} display="flex" flexDirection="row" gap={2}>
                    <Button type="submit" name="authored_all" variant="contained" color="primary">
                        I am an author of all of these papers
                    </Button>
                    <Button type="submit" name="authored_none" variant="contained" color="primary">
                        I am an author of none of these papers
                    </Button>
                    <Button type="submit" name="submit" variant="contained" color="success">
                        Save Changes
                    </Button>
                </Box>
            </form>

        </Box>
    );
};

export default AuthorshipStatus;
