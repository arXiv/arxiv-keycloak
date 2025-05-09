import React, {useContext, useState, useEffect} from "react";

import { RuntimeContext } from "../RuntimeContext.tsx";
import {paths as adminApi} from "../types/admin-api";
import Typography, {TypographyProps} from "@mui/material/Typography";

type GroupType = adminApi['/v1/taxonomy/groups/{group_id}']['get']['responses']['200']['content']['application/json'];

interface CategoryGroupProps extends TypographyProps {
    groupId: string;
}

const CategoryGroup: React.FC<CategoryGroupProps> = ({ groupId, ...props }) => {
    const runtimeProps = useContext(RuntimeContext);
    const [description, setDescription] = useState<string>("");

    useEffect(() => {
        const fetchGroup = async () => {
            try {
                const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/taxonomy/groups/${groupId}`);
                const result: GroupType = await response.json();
                setDescription(result.full_name);
            } catch (error) {
                console.error("Failed to fetch group info", error);
                setDescription("Failed to load group name");
            }
        };

        fetchGroup();
    }, [groupId, runtimeProps.ADMIN_API_BACKEND_URL]);

    return (<Typography {...props} >{description}</Typography>);
};

export default CategoryGroup;
