import React, {useEffect, useState, useContext} from "react";
import {paths as adminApi} from "../types/admin-api";
import Typography from "@mui/material/Typography";
import {RuntimeContext} from "../RuntimeContext.tsx";
import { ADMIN_PAPER_PW_ID_URL } from "../types/admin-url.ts";

type PaperPwType = adminApi[typeof ADMIN_PAPER_PW_ID_URL]['get']['responses']['200']['content']['application/json'];


interface PaperPasswordProps  {
    documentId: string;
}

const PaperPassword: React.FC<PaperPasswordProps> = ({documentId}) => {
    const [pwpassword, setPwpassword] = useState<PaperPwType | null>(null);
    const runtimeProps = useContext(RuntimeContext);

    useEffect(() => {
        async function fetchpwpassword () {
            if (documentId) {
                try {
                    const getPaperPassword = runtimeProps.adminFetcher.path(ADMIN_PAPER_PW_ID_URL).method('get').create();
                    const response = await getPaperPassword({id: documentId});
                    if (response.ok) {
                        const body: PaperPwType = response.data;
                        setPwpassword(body);
                    }
                    else {
                        setPwpassword(null);
                    }
                }
                catch (error) {
                    console.error("Failed to fetch paper password", error);
                }
            }
        }

        fetchpwpassword();
    }, [documentId, runtimeProps.adminFetcher]);

    return (
        <Typography >
            {pwpassword?.password_enc}
        </Typography>
    );
};

export default PaperPassword;
