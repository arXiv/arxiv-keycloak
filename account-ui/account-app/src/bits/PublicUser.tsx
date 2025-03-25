import React from "react";
import { paths as adminApi } from "../types/admin-api";
import {fetchPlus} from "../fetchPlus";
import {RuntimeProps} from "../RuntimeContext";
import Typography from "@mui/material/Typography";
import {printUserName} from "./printer.ts";
import {useQuery} from "@tanstack/react-query";


type PublicUserType = adminApi["/v1/public-users/{user_id}"]["get"]['responses']["200"]['content']['application/json'];

export const usePublicUser = (apiBaseUrl: string, user_id: number) => {
    return useQuery<PublicUserType>({
        queryKey: ["public-user", user_id],
        queryFn: async () => {
            const url = `${apiBaseUrl}/public-users/${user_id}`;
            const response = await fetchPlus(url);
            return response.json();
        },
        enabled: !!user_id // only fetch if user_id is truthy
    });
};

interface PublicUserPpops {
   runtimeProps: RuntimeProps;
   user_id: number;
}

const PublicUser: React.FC<PublicUserPpops> = ({runtimeProps, user_id}) => {
    const { data: user, isLoading, isError } = usePublicUser(runtimeProps.ADMIN_API_BACKEND_URL, user_id);

    if (isLoading) return <Typography>Loading user…</Typography>;
    if (isError) return <Typography>Error loading user</Typography>;

    return (
        <Typography component="span">
            {printUserName(user)}
        </Typography>
    );
}

export default PublicUser;
