import React, {useEffect, useState, useContext} from "react";
import {paths as adminApi} from "../types/admin-api";
import Typography from "@mui/material/Typography";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {fetchPlus} from "../fetchPlus.ts";

// type DocumentType = adminApi['/v1/documents/{id}']['get']['responses']['200']['content']['application/json'];
type MetadataType = adminApi['/v1/metadatas/{id}']['get']['responses']['200']['content']['application/json'];


interface DocumentMetadataProps  {
    arxivId: string;
}

const DocumentMetadata: React.FC<DocumentMetadataProps> = ({arxivId}) => {
    const [metadata, setMetadata] = useState<MetadataType | null>(null);
    const runtimeProps = useContext(RuntimeContext);

    useEffect(() => {
        async function fetchMetadata () {
            if (arxivId) {
                try {
                    const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/metadata/${arxivId}`);
                    if (response.ok) {
                        const body: MetadataType = await response.json();
                        setMetadata(body);
                    }
                    else {
                        setMetadata(null);
                    }
                }
                catch (error) {

                }
            }
        }

        fetchMetadata();
    }, []);

    return (
        <Typography >
            {metadata?.abstract}
        </Typography>
    );
};

export default DocumentMetadata;
