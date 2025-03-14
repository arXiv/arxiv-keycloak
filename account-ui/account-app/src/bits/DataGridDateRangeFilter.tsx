import React from "react";
import { Box } from "@mui/material";
import { GridFilterInputValueProps } from "@mui/x-data-grid";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs, { Dayjs } from "dayjs";

const DataGridDateRangeFilter: React.FC<GridFilterInputValueProps> = ({ item, applyValue }) => {
    const [startDate, setStartDate] = React.useState<Dayjs | null>(item?.value?.[0] ? dayjs(item.value[0]) : null);
    const [endDate, setEndDate] = React.useState<Dayjs | null>(item?.value?.[1] ? dayjs(item.value[1]) : null);

    const handleChange = (newStartDate: Dayjs | null, newEndDate: Dayjs | null) => {
        setStartDate(newStartDate);
        setEndDate(newEndDate);
        applyValue({
            ...item,
            value: [newStartDate?.toISOString() || "", newEndDate?.toISOString() || ""],
        });
    };

    return (
        <Box display="flex" gap={2}>
            <DatePicker
                label="Start Date"
                value={startDate}
                onChange={(date) => handleChange(date, endDate)}
                slotProps={{ textField: { variant: "standard", size: "small" } }}
            />
            <DatePicker
                label="End Date"
                value={endDate}
                onChange={(date) => handleChange(startDate, date)}
                slotProps={{ textField: { variant: "standard", size: "small" } }}
            />
        </Box>
    );
};

export default DataGridDateRangeFilter;
