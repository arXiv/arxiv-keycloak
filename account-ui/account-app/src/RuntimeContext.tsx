import React, { createContext, useState, useEffect, } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import {Box} from '@mui/material';
import {paths} from "./types/aaa-api";
type User = paths["/account/info/id:str"]["get"]["responses"]["200"]["content"]["application/json"];

export interface RuntimeProps
{
    AAA_URL: string,
    UP_API_URL: string,
    ADMIN_API_BACKEND_URL: string,
    ADMIN_APP_ROOT: string,
    ARXIV_COOKIE_NAME: string,
    TAPIR_COOKIE_NAME: string,
    UNIVERSITY: string,
    HOME: string,
    currentUser: User | null,
}

const defaultRuntimeProps : RuntimeProps = {
    AAA_URL: 'http://localhost.arxiv.org:5000/aaa',
    UP_API_URL: 'http://localhost.arxiv.org:5000/up-api',
    ADMIN_API_BACKEND_URL: 'http://localhost.arxiv.org:5000/admin-api/v1',
    ADMIN_APP_ROOT: 'http://localhost.arxiv.org:5000/admin-console/',
    ARXIV_COOKIE_NAME: "arxiv_oidc_session",
    TAPIR_COOKIE_NAME: "tapir_session",
    UNIVERSITY: "https://cornell.edu",
    HOME: "https://cornell.edu",
    currentUser: null
};

export const RuntimeContext = createContext<RuntimeProps>(defaultRuntimeProps);

interface RuntimeContextProviderProps {
    children: React.ReactNode;
}


export const RuntimeContextProvider = ({ children } : RuntimeContextProviderProps) => {
    const [runtimeEnv, setRuntimeEnv] = useState<RuntimeProps>(defaultRuntimeProps);
    const [loading, setLoading] = useState<boolean>(true);

    function updateRuntimeEnv(props: Partial<RuntimeProps>) {
        const updated = Object.assign(runtimeEnv, props);
        setRuntimeEnv(updated);
    }

    useEffect(() => {
        const fetchRuntimeEnvironment = async () => {
            try {
                let baseUrl = window.location.protocol + "//" + window.location.hostname;
                if ((window.location.port !== "80") && (window.location.port !== "") && (window.location.port !== "443"))
                    baseUrl = baseUrl + ":" + window.location.port;
                baseUrl = baseUrl + "/";
                const runtime1: Partial<RuntimeProps> = {
                    AAA_URL: baseUrl + "aaa",
                    UP_API_URL: baseUrl + "admin-api/v1",
                    ADMIN_API_BACKEND_URL: baseUrl + "admin-api/v1",
                    ADMIN_APP_ROOT: baseUrl + "admin-console/",
                    ARXIV_COOKIE_NAME: defaultRuntimeProps.ARXIV_COOKIE_NAME,
                    TAPIR_COOKIE_NAME: defaultRuntimeProps.TAPIR_COOKIE_NAME,
                };
                console.log("runtime-1: " + JSON.stringify(runtime1));
                updateRuntimeEnv(runtime1);
                const cookie_name_response = await fetch(`${runtime1.AAA_URL}/token-names`);
                const cookie_names = await cookie_name_response.json();
                console.log("cookie_names: " + JSON.stringify(cookie_names));

                const runtime2: Partial<RuntimeProps> = {
                    AAA_URL: baseUrl + "aaa",
                    ADMIN_API_BACKEND_URL: baseUrl + "admin-api/v1",
                    ADMIN_APP_ROOT: baseUrl + "admin-console/",
                    ARXIV_COOKIE_NAME: cookie_names.session,
                    TAPIR_COOKIE_NAME: cookie_names.classic,
                };

                console.log("runtime-2: " + JSON.stringify(runtime2));
                updateRuntimeEnv(runtime2);

                try {
                    const reply = await fetch(runtime2.AAA_URL + "/account/info/current");
                    if (reply.status === 200) {
                        const data = await reply.json();
                        console.log({currentUser: data});
                        updateRuntimeEnv({currentUser: data});
                    }
                    else {
                        const data = await reply.json();
                        console.log("status=" + reply.status  + " data=" + JSON.stringify(data));
                        updateRuntimeEnv({currentUser: null});
                    }
                } catch (error) {
                    updateRuntimeEnv({currentUser: null});
                    console.error('Error fetching account urls:', error);
                }

            } catch (error) {
                console.error('Error fetching runtime urls:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchRuntimeEnvironment();
    }, []);

    if (loading) {
        return (<Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh"><CircularProgress /></Box>);
    }

    return (
        <RuntimeContext.Provider value={runtimeEnv}>
            {children}
        </RuntimeContext.Provider>
    );
};