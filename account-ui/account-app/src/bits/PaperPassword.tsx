import React, {useEffect, useState, useContext} from "react";
import {paths as adminApi} from "../types/admin-api";
import Typography from "@mui/material/Typography";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {fetchPlus} from "../fetchPlus.ts";

type PaperPwType = adminApi['/v1/paper-pw/{id}']['get']['responses']['200']['content']['application/json'];


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
                    const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/paper-pw/${documentId}`);
                    if (response.ok) {
                        const body: PaperPwType = await response.json();
                        setPwpassword(body);
                    }
                    else {
                        setPwpassword(null);
                    }
                }
                catch (error) {

                }
            }
        }

        fetchpwpassword();
    }, []);

    return (
        <Typography >
            {pwpassword?.password_enc}
        </Typography>
    );
};

export default PaperPassword;
