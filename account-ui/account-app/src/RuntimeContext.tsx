import React, { createContext, useState, useEffect, } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import {Box} from '@mui/material';
import {paths} from "./types/aaa-api";
export type User = paths["/account/profile/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"];

export interface ArxivSiteURLs {
    arXiv: string,
    privacyPolicy: string;
    authorityRecord: string;
    submissionManagementURL: string;
    newSubmissionURL: string;
    authorIdentifier: string;
    whyTex: string;
    cleanUpload: string;
    commonMistakes: string;
    submissionChecklist: string;
    moreTips: string;
    webAccessibility: string;
    arxivStatus: string;
    arxivStatusEmail: string;
    arxivSlack: string;
    emailProtection: string;
    mathJaxHelp: string;
    needPaperPassword: string;
    requestOwnership: string;
    orcidOrg: string;
    ourMemberships: string;
    about: string;
    help: string;
    donate: string;
    contact: string;
    subscribe: string;
    license: string;

    // These are user actions. Not really belongs to the site URLs
    userChangeProfile: string;
    userPasswordRecovery: string;
    userChangePassword: string;
    userChangeEmail: string;
    userSendEmailVerification: string;
}

export interface RuntimeProps
{
    AAA_URL: string,
    UP_API_URL: string,
    ADMIN_API_BACKEND_URL: string,
    ADMIN_APP_ROOT: string,
    ARXIV_COOKIE_NAME: string,
    TAPIR_COOKIE_NAME: string,
    UNIVERSITY: string,
    POST_USER_REGISTRATION_URL: string,
    HOME: string,
    MATHJAX_COOKIE_NAME: string,
    URLS: ArxivSiteURLs,
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
    POST_USER_REGISTRATION_URL: "/",
    MATHJAX_COOKIE_NAME: "arxiv_mathjax",
    URLS: {
        arXiv: "/",
        privacyPolicy: "https://arxiv.org/help/policies/privacy_policy",
        authorityRecord: "https://info.arxiv.org/help/authority",
        submissionManagementURL: "https://arxiv.org/user/submissions",
        newSubmissionURL: "https://arxiv.org/user/submissions/new",
        authorIdentifier: "https://info.arxiv.org/help/author_identifiers",
        whyTex: "https://info.arxiv.org/help/faq/whytex.html",
        cleanUpload: "https://trevorcampbell.me/html/arxiv.html",
        commonMistakes: "https://info.arxiv.org/help/faq/mistakes.html",
        submissionChecklist: "https://www.ianhuston.net/2011/03/checklist-for-arxiv-submission/",
        moreTips: "https://www.ianhuston.net/2011/03/checklist-for-arxiv-submission/",
        webAccessibility: "/help/web_accessibility",
        arxivStatus: "https://status.arxiv.org",
        arxivStatusEmail: "https://subscribe.sorryapp.com/24846f03/email/new",
        arxivSlack: "https://subscribe.sorryapp.com/24846f03/slack/new",
        emailProtection: "https://info.arxiv.org/help/email-protection",
        mathJaxHelp: "https://info.arxiv.org/help/mathjax.html",
        needPaperPassword: "/auth/need-paper-password",
        requestOwnership: "/auth/request-ownership",
        orcidOrg: "http://orcid.org/",
        ourMemberships: "https://info.arxiv.org/about/ourmembers.html",
        about: "/about",
        help: "/help",
        donate: "https://info.arxiv.org/about/donate.html",
        contact: "/help/contact",
        subscribe: "help/subscribe",
        license: "/help/license",

        userChangeProfile: "/user-account/update-profile",
        userPasswordRecovery: "/password-recovery",
        userChangePassword: "/user-account/change-password",
        userChangeEmail: "/user-account/change-email",
        userSendEmailVerification: "/send-email-verification",
    },
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
                    const reply = await fetch(runtime2.AAA_URL + "/account/current");
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