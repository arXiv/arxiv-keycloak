import {GridPaginationModel}from '@mui/x-data-grid';
import TablePagination, { TablePaginationProps } from "@mui/material/TablePagination";

function DatagridPaginationMaker(
    getTotalCount: () => number,
    getPaginationModel: () => GridPaginationModel,
    setPaginationModel: (_: GridPaginationModel) => void,
    getPageSizes: () => number[]
): (props: Partial<TablePaginationProps>) => JSX.Element {
    return (props: Partial<TablePaginationProps>) => {
        const totalCount = getTotalCount();
        const paginationModel = getPaginationModel();
        return (
            <TablePagination
                {...props}
                rowsPerPageOptions={getPageSizes()}
                component="div" // Required for DataGrid compatibility
                count={totalCount} // Ensure count is never undefined
                page={paginationModel.page ?? 0} // Ensure page is never undefined
                onPageChange={(_, newPage) => setPaginationModel({...paginationModel, page: newPage})}
                rowsPerPage={paginationModel.pageSize}
                onRowsPerPageChange={(event) => {
                    const newSize = parseInt(event.target.value, 10);
                    setPaginationModel({page: 0, pageSize: newSize});
                }}
                showFirstButton
                showLastButton
            />
        );
    }
}

export default DatagridPaginationMaker;
