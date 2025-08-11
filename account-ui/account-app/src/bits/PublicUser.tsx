import React, {useState, useEffect} from "react";
import { paths as adminApi } from "../types/admin-api";
import {RuntimeProps} from "../RuntimeContext";
import Typography from "@mui/material/Typography";
import {printUserName} from "./printer.ts";
import {ADMIN_PUBLIC_USER_URL} from "../types/admin-url.ts";

type PublicUserType = adminApi[typeof ADMIN_PUBLIC_USER_URL]["get"]['responses']["200"]['content']['application/json'];

interface PublicUserPpops {
   runtimeProps: RuntimeProps;
   user_id: number;
}

const PublicUser: React.FC<PublicUserPpops> = ({runtimeProps, user_id}) => {
    const [user, setUser] = useState<PublicUserType | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isError, setIsError] = useState(false);

    useEffect(() => {
        const fetchUser = async () => {
            if (!user_id) {
                setIsLoading(false);
                return;
            }

            try {
                setIsLoading(true);
                setIsError(false);
                const getPublicUser = runtimeProps.adminFetcher.path(ADMIN_PUBLIC_USER_URL).method('get').create();
                const response = await getPublicUser({user_id: user_id});
                setUser(response.data);
            } catch (error) {
                console.error("Error fetching public user:", error);
                setIsError(true);
            } finally {
                setIsLoading(false);
            }
        };

        fetchUser();
    }, [user_id, runtimeProps.adminFetcher]);

    if (isLoading) return <Typography>Loading user…</Typography>;
    if (isError) return <Typography>Error loading user</Typography>;

    return (
        <Typography component="span">
            {printUserName(user)}
        </Typography>
    );
}

export default PublicUser;
