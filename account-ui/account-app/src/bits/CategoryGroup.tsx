import React, {useContext, useState, useEffect} from "react";

import { RuntimeContext } from "../RuntimeContext.tsx";
import Typography, {TypographyProps} from "@mui/material/Typography";
import {ADMIN_TAXONOMY_GROUPS_URL} from "../types/admin-url.ts";


interface CategoryGroupProps extends TypographyProps {
    groupId: string;
}

const CategoryGroup: React.FC<CategoryGroupProps> = ({ groupId, ...props }) => {
    const runtimeProps = useContext(RuntimeContext);
    const [description, setDescription] = useState<string>("");

    useEffect(() => {
        const getTaxonomyGroups = runtimeProps.adminFetcher.path(ADMIN_TAXONOMY_GROUPS_URL).method('get').create();

        const fetchGroup = async () => {
            try {
                const response = await getTaxonomyGroups({
                    group_id: groupId,
                });
                setDescription(response.data.full_name);
            } catch (error) {
                console.error("Failed to fetch group info", error);
                setDescription("Failed to load group name");
            }
        };

        fetchGroup();
    }, [groupId, runtimeProps.adminFetcher]);

    return (<Typography {...props} >{description}</Typography>);
};

export default CategoryGroup;
