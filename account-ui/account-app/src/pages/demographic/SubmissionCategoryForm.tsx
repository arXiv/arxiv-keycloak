import React from "react";
import Box from "@mui/material/Box";
import {paths} from "../../types/aaa-api.ts";
import CategoryGroupSelection, {CategoryGroupType} from "../../bits/CategoryGroupSelection.tsx";
import CategoryChooser, {SelectedCategoryType} from "../../bits/CategoryChooser.tsx";
import {AccountFormError} from "./AccountFormError.ts";
import {ACCOUNT_PROFILE_URL, ACCOUNT_REGISTER_URL} from "../../types/aaa-url.ts";

type SubmitRequest = paths[typeof ACCOUNT_REGISTER_URL]['post']['requestBody']['content']['application/json'];

type UpdateProfileRequest = paths[typeof ACCOUNT_PROFILE_URL]['put']['requestBody']['content']['application/json'];

// Generic component that works with both form types
const SubmissionCategoryForm = <T extends SubmitRequest | UpdateProfileRequest>({
                                                                                    formData,
                                                                                    setFormData,
                                                                                    setErrors
                                                                                }: {
    formData: T;
    setFormData: React.Dispatch<React.SetStateAction<T>>;
    setErrors: React.Dispatch<React.SetStateAction<AccountFormError>>;
}) => {
    const setSelectedGroups = (groups: CategoryGroupType[]) => {
        setFormData(prev => ({...prev, groups: groups}));
        if (groups.length > 0) {
            setErrors(prev => ({...prev, groups: ""}));
        } else {
            setErrors(prev => ({...prev, groups: "Please select at least one group"}));
        }
    }

    const setDefaultCategory = (cat: SelectedCategoryType | null) => {
        if (cat) {
            setFormData(prev => ({
                ...prev,
                default_category: {archive: cat.archive, subject_class: cat.subject_class || ""}
            }));
            console.log(`default_category - ${JSON.stringify(formData.default_category)}`);
            setErrors((prev) => ({...prev, default_category: ""}));
        } else {
            setErrors((prev) => ({...prev, default_category: "The default category is required"}));
        }
    }

    return (
        <Box sx={{p: 1, m: 1}}>
            <CategoryGroupSelection
                selectedGroups={formData.groups as unknown as CategoryGroupType[]}
                setSelectedGroups={setSelectedGroups}
            />
            <Box sx={{pb: 1, mt: 2}}>
                <CategoryChooser
                    onSelect={setDefaultCategory}
                    selectedCategory={formData.default_category}
                />
            </Box>
        </Box>
    );
}

export default SubmissionCategoryForm;